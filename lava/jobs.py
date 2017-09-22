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
from lava.server import LavaServer, Storage
from lava.atf import AtfImage
from config import ConfigManager


class JobDefinition(object):
    """LAVA Job Definition

    This class can contain the complete definition of a LAVA job. This
    information is stored in a structure that is serializable in YAML format
    which can later be sen t to the LAVA server.

    Currently this class can be only initialized from a YAML file. Use the
    'filename' argument in the construction of the class.

    """

    def __init__(self, filename=None, config=None, logger=None):
        """Parse and store the LAVA job definition.

        Args:
            filename (str): Path to the input file

        """
        self._logger = logger or logging.getLogger(__name__ + '.JobDefinition')
        self._conf = config or ConfigManager()

        if not filename:
            self._logger.error("Wrong JobDefinition Initialization")
            raise NotImplemented("Only Initialization from file implemented")

        with open(filename, 'rt') as f:
            content = f.read()
            try:
                self._yaml = yaml.load(content)
                self._logger.debug("Job Definition:\n=== BEGIN JOB DEFINITION ===\n%s\n"
                                   "=== END JOB DEFINITION ===", yaml.dump(self._yaml))
            except yaml.YAMLError:
                self._logger.error(
                    "Incorrect YAML format in file name %s", filename)
                raise RuntimeError("Invalid YAML file format", filename)

    def get(self, key):
        """Get te value associated to the input key in the job configuration"""
        try:
            # solve keys encoded using 'dot' notation
            access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
            return reduce(access, key.split('.'), self._yaml)
        except KeyError:
            self._logger.error("Missing key %s in LAVA job description", key)
        except:
            self._logger.error("Incorrect LAVA Job definition")
        return None

    def set(self, key, value):
        keys = key.split('.')
        access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
        cont = reduce(access, keys[:-1], self._yaml)
        cont[keys[-1]] = value

    @property
    def lava_server(self):
        return self._lava_server

    @lava_server.getter
    def lava_server(self):
        if getattr(self, '_lava_server', None) is None:
            self._lava_server = LavaServer(config=self._conf, logger=self._logger)
        return self._lava_server

    def valid(self):
        if getattr(self, '_valid', None) is None:
            self._valid = self.lava_server.validate(self.__str__())
        return self._valid

    def submit(self):
        if self.valid():
            self._jobid = self.lava_server.submit(self.__str__())
        else:
            self._logger.error("Trying to submit invalid job")
            raise RuntimeError("Trying to submit invalid job")

        if self._jobid:
            self._logger.debug("Job Submitted successfully -- ID: %s", self._jobid)
        else:
            self._logger.error("Couldn't submit LAVA job")
            raise RuntimeError("Couldn't submit LAVA job")

    def submit_and_wait(self):
        return self.lava_server.submit_and_wait(self.__str__())

    def __str__(self):
        return yaml.dump(self._yaml)

    def __repr__(self):
        return yaml.dump(self._yaml)


# class Job(object):
    # """Lava Job

    # This class is the interface with a LAVA job that can be modified, validated
    # and submitted to the a LAVA testing framework.


    # """

    # def __init__(self, config=None, filename=None):
        # """Init the Job from the configuration"""

        # self._logger = logging.getLogger(__name__ + ".Job")

        # if not config:
            # self._logger.error("Creating a job with empty configuration")
            # self._is_valid = False

        # self._logger.progress_bar = config.getboolean(
            # 'logging', 'progress-bars')

        # self._conf = config
        # self._lava_url = config.get('lava.server', 'url')
        # self._sleep = config.getint('lava.jobs', 'sleep')
        # self._running_timeout = config.getint('lava.jobs', 'running_timeout')
        # self._waiting_timeout = config.getint('lava.jobs', 'waiting_timeout')
        # self._env = Environment(
            # loader=PackageLoader('lava.devices', 'templates'))

        # self._logger.debug('Lava URL:          %s', self._lava_url)
        # self._logger.debug('Waiting-loop time: %ds', self._sleep)
        # self._logger.debug('Running timemout:  %ds', self._running_timeout)
        # self._logger.debug('Queued timeout:    %ds', self._waiting_timeout)

        # if config.has_section('lava.files'):
            # self._logger.info('Uploading files to FTP server')
            # with Storage(config) as ftp:
                # self._kernel_url = ftp.upload(
                    # config.get('lava.files', 'kernel'))
                # self._rootfs_url = ftp.upload(config.get('lava.files', 'rootfs'),
                                              # compressed=True)
                # self._logger.debug('Kernel URL:        %ds', self._kernel_url)
                # self._logger.debug('Rootfs URL:        %ds', self._rootfs_url)

        # # Test latest artifactory image
        # else:
            # atf = AtfImage(self._conf)

            # atf = config.get('artifactory', 'server')
            # latest = config.get('artifactory', 'latest')
            # kernel = config.get('artifactory', 'kernel')
            # rootfs = config.get('artifactory', 'rootfs')

            # atfuser = config.get('artifactory', 'user')
            # atfpass = config.get('artifactory', 'pass')
            # atfauth = (atfuser, atfpass)

            # atf_kernel = "%s/%s/%s" % (atf, latest, kernel)
            # atf_rootfs = "%s/%s/%s" % (atf, latest, rootfs)

            # local_kernel = open(kernel, 'wb')
            # local_rootfs = open(rootfs, 'wb')

            # with Storage(config) as ftp:

                # self._logger.info('Downloading latest image from artifactory')

                # file = ArtifactoryPath(atf_kernel, auth=atfauth, verify=False)
                # with file.open() as k:
                    # local_kernel.write(k.read())

                # file = ArtifactoryPath(atf_rootfs, auth=atfauth, verify=False)
                # with file.open() as r:
                    # local_rootfs.write(r.read())

                # local_kernel.seek(0)
                # local_rootfs.seek(0)

                # self._kernel_url = ftp.upload(local_kernel.name)
                # self._rootfs_url = ftp.upload(
                    # local_rootfs.name, compressed=True)
                # if not self._rootfs_url.endswith('.gz'):
                    # self._rootfs_url = self._rootfs_url + '.gz'

                # self._logger.debug('Kernel URL:        %s', self._kernel_url)
                # self._logger.debug('Rootfs URL:        %s', self._rootfs_url)

            # local_kernel.close()
            # local_rootfs.close()

            # os.remove(local_kernel.name)
            # os.remove(local_rootfs.name)

        # self._logger.info('Generating job description')
        # qemu = self._env.get_template('qemux86.yaml')

        # # Template context
        # context = {}
        # context['kernel_url'] = self._kernel_url
        # context['rootfs_url'] = self._rootfs_url

        # # Add inline test
        # if config.has_section('lava.test'):
            # context['test'] = True
            # context['test_repos'] = config.get('lava.test', 'repos')

        # self._job_definition = qemu.render(context)

    # @property
    # def definition(self):
        # return self._job_definition

    # def submit(self):
        # with LavaRPC(self._conf) as server:
            # self._jobid = server.scheduler.submit_job(self._job_definition)
            # self._logger.info('Submitted Job ID: %d', self._jobid)
            # self._logger.info('job url:\n\n%s/%s/%d\n',
                              # self._lava_url, 'scheduler/job', self._jobid)

    # def poll(self):
        # with LavaRPC(self._conf) as server:

            # count = 0
            # status = server.scheduler.job_status(self._jobid).get('job_status')

            # # Wait while the job is Queued
            # bar = Bar('Job %d: waiting in queue ' % self._jobid,
                      # max=self._waiting_timeout, suffix='%(index)d / %(max)d seconds')
            # while status == 'Submitted' and count < self._waiting_timeout:
                # bar.index = count
                # bar.update()

                # count += self._sleep
                # time.sleep(self._sleep)
                # status = server.scheduler.job_status(
                    # self._jobid).get('job_status')

            # # Job didn't start
            # if count >= self._waiting_timeout:
                # self._logger.error(
                    # 'Waiting timeout for queued Job-ID %d', self._jobid)
                # exit(1)

            # count = 0
            # while count < self._running_timeout:
                # bar.message = 'Job %d: %s' % (self._jobid, status)
                # bar.index = count
                # bar.max = self._running_timeout
                # bar.update()

                # if status == 'Complete':
                    # bar.finish()

                    # # Check the tests passed
                    # response = urllib2.urlopen("%s/results/%d/csv" %
                                               # (self._lava_url, self._jobid))
                    # tests = csv.DictReader(response.read().split('\r\n'))

                    # results = [test.get('result') for test in tests]

                    # self._logger.info("Test PASSED %d", results.count('pass'))
                    # self._logger.info("Test FAILED %d", results.count('fail'))

                    # if all(result == "pass" for result in results):
                        # exit(0)
                    # else:
                        # exit(1)

                # elif status == 'Canceled' or status == 'Cancelling':
                    # bar.finish()
                    # exit(1)

                # elif status == 'Running':
                    # count += self._sleep

                # elif status == 'Incomplete':
                    # bar.finish()
                    # exit(1)

                # # Wait _sleep seconds
                # time.sleep(self._sleep)
                # status = server.scheduler.job_status(
                    # self._jobid).get('job_status')

            # bar.finish()

            # if count >= self._running_timeout:
                # self._logger.error("Running timeout")
                # exit(1)
