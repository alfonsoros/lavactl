# -*- coding: utf-8 -*-

import sys
import os
import csv
import xmlrpclib
import time
import urllib2
import logging
import tempfile
import yaml

from progress.bar import Bar
from jinja2 import Environment, PackageLoader
from artifactory import ArtifactoryPath
from lava.server.Storage import Storage
from lava.server.interface import LavaRPC


class JobDefinition(object):
    """LAVA Job Definition

    This class can contain the complete definition of a LAVA job. This
    information is stored in a structure that is serializable in YAML format
    which can later be sent to the LAVA server.

    Currently this class can be initialized from a YAML file.

    """

    def __init__(self, filename=None, *args, **kwargs):
        """Parse and store the LAVA job definition.

        Args:
            filename (str): Path to the input file

        """
        self._logger = logging.getLogger(__name__)

        # Construct from a file path
        if filename:
            with open(filename, 'rt') as f:
                content = f.read()

                # YAML format
                try:
                    self._yaml = yaml.load(content)
                    self._logger.info("LAVA Job definition loaded")
                except yaml.YAMLError:
                    self._logger.error(
                        "Incorrect YAML format in file name %s", filename)
                    self._yaml = yaml.load("")
        else:
            self._logger.error("Couldn't load LAVA job definition")
            self._yaml = yaml.load("")

    def get(self, key):
        """Get te value associated to the input key in the job configuration"""
        try:
            access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
            # solve keys encoded using 'dot' notation
            return reduce(access, key.split('.'), self._yaml)
        except KeyError:
            self._logger.error("Missing key %s in LAVA job description", key)
        except:
            self._logger.error("Incorrect LAVA Job definition")
        return None

    def __repr__(self):
        return yaml.dump(self._yaml)


class Job(object):
    """Lava Job"""

    def __init__(self, config):

        self._logger = logging.getLogger(__name__ + ".Job")
        self._logger.progress_bar = config.getboolean(
            'logging', 'progress-bars')

        self._conf = config
        self._lava_url = config.get('lava.server', 'url')
        self._sleep = config.getint('lava.jobs', 'sleep')
        self._running_timeout = config.getint('lava.jobs', 'running_timeout')
        self._waiting_timeout = config.getint('lava.jobs', 'waiting_timeout')
        self._env = Environment(
            loader=PackageLoader('lava.devices', 'templates'))

        self._logger.debug('Lava URL:          %s', self._lava_url)
        self._logger.debug('Waiting-loop time: %ds', self._sleep)
        self._logger.debug('Running timemout:  %ds', self._running_timeout)
        self._logger.debug('Queued timeout:    %ds', self._waiting_timeout)

        if config.has_section('lava.files'):
            self._logger.info('Uploading files to FTP server')
            with Storage(config) as ftp:
                self._kernel_url = ftp.upload(
                    config.get('lava.files', 'kernel'))
                self._rootfs_url = ftp.upload(config.get('lava.files', 'rootfs'),
                                              compressed=True)
                self._logger.debug('Kernel URL:        %ds', self._kernel_url)
                self._logger.debug('Rootfs URL:        %ds', self._rootfs_url)

        # Test latest artifactory image
        else:
            atf = config.get('artifactory', 'server')
            latest = config.get('artifactory', 'latest')
            kernel = config.get('artifactory', 'kernel')
            rootfs = config.get('artifactory', 'rootfs')

            atfuser = config.get('artifactory', 'user')
            atfpass = config.get('artifactory', 'pass')
            atfauth = (atfuser, atfpass)

            atf_kernel = "%s/%s/%s" % (atf, latest, kernel)
            atf_rootfs = "%s/%s/%s" % (atf, latest, rootfs)

            local_kernel = open(kernel, 'wb')
            local_rootfs = open(rootfs, 'wb')

            with Storage(config) as ftp:

                self._logger.info('Downloading latest image from artifactory')

                file = ArtifactoryPath(atf_kernel, auth=atfauth, verify=False)
                with file.open() as k:
                    local_kernel.write(k.read())

                file = ArtifactoryPath(atf_rootfs, auth=atfauth, verify=False)
                with file.open() as r:
                    local_rootfs.write(r.read())

                local_kernel.seek(0)
                local_rootfs.seek(0)

                self._kernel_url = ftp.upload(local_kernel.name)
                self._rootfs_url = ftp.upload(
                    local_rootfs.name, compressed=True)
                if not self._rootfs_url.endswith('.gz'):
                    self._rootfs_url = self._rootfs_url + '.gz'

                self._logger.debug('Kernel URL:        %s', self._kernel_url)
                self._logger.debug('Rootfs URL:        %s', self._rootfs_url)

            local_kernel.close()
            local_rootfs.close()

            os.remove(local_kernel.name)
            os.remove(local_rootfs.name)

        self._logger.info('Generating job description')
        qemu = self._env.get_template('qemux86.yaml')

        # Template context
        context = {}
        context['kernel_url'] = self._kernel_url
        context['rootfs_url'] = self._rootfs_url

        # Add inline test
        if config.has_section('lava.test'):
            context['test'] = True
            context['test_repos'] = config.get('lava.test', 'repos')

        self._job_definition = qemu.render(context)

    @property
    def definition(self):
        return self._job_definition

    def submit(self):
        with LavaRPC(self._conf) as server:
            self._jobid = server.scheduler.submit_job(self._job_definition)
            self._logger.info('Submitted Job ID: %d', self._jobid)
            self._logger.info('job url:\n\n%s/%s/%d\n',
                              self._lava_url, 'scheduler/job', self._jobid)

    def poll(self):
        with LavaRPC(self._conf) as server:

            count = 0
            status = server.scheduler.job_status(self._jobid).get('job_status')

            # Wait while the job is Queued
            bar = Bar('Job %d: waiting in queue ' % self._jobid,
                      max=self._waiting_timeout, suffix='%(index)d / %(max)d seconds')
            while status == 'Submitted' and count < self._waiting_timeout:
                bar.index = count
                bar.update()

                count += self._sleep
                time.sleep(self._sleep)
                status = server.scheduler.job_status(
                    self._jobid).get('job_status')

            # Job didn't start
            if count >= self._waiting_timeout:
                self._logger.error(
                    'Waiting timeout for queued Job-ID %d', self._jobid)
                exit(1)

            count = 0
            while count < self._running_timeout:
                bar.message = 'Job %d: %s' % (self._jobid, status)
                bar.index = count
                bar.max = self._running_timeout
                bar.update()

                if status == 'Complete':
                    bar.finish()

                    # Check the tests passed
                    response = urllib2.urlopen("%s/results/%d/csv" %
                                               (self._lava_url, self._jobid))
                    tests = csv.DictReader(response.read().split('\r\n'))

                    results = [test.get('result') for test in tests]

                    self._logger.info("Test PASSED %d", results.count('pass'))
                    self._logger.info("Test FAILED %d", results.count('fail'))

                    if all(result == "pass" for result in results):
                        exit(0)
                    else:
                        exit(1)

                elif status == 'Canceled' or status == 'Cancelling':
                    bar.finish()
                    exit(1)

                elif status == 'Running':
                    count += self._sleep

                elif status == 'Incomplete':
                    bar.finish()
                    exit(1)

                # Wait _sleep seconds
                time.sleep(self._sleep)
                status = server.scheduler.job_status(
                    self._jobid).get('job_status')

            bar.finish()

            if count >= self._running_timeout:
                self._logger.error("Running timeout")
                exit(1)
