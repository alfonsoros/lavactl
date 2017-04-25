# -*- coding: utf-8 -*-

import os
import csv
import xmlrpclib
import time
import urllib2
import logging
import tempfile

from progress.bar import Bar
from jinja2 import Environment, PackageLoader
from artifactory import ArtifactoryPath
from lava.server.Storage import Storage
from lava.server.interface import LavaRPC

class Job(object):
  def __init__(self, config, logger=None):
    self._log = logger.getChild('job') if logger else logging.getLogger('lava.job')

    self._conf = config
    self._lava_url = config.get('lava.server', 'url')
    self._sleep = config.getint('lava.jobs', 'sleep')
    self._running_timeout = config.getint('lava.jobs', 'running_timeout')
    self._waiting_timeout = config.getint('lava.jobs', 'waiting_timeout')
    self._env = Environment(loader=PackageLoader('lava.devices', 'templates'))

    self._log.debug('Lava URL:          %s', self._lava_url)
    self._log.debug('Waiting-loop time: %ds', self._sleep)
    self._log.debug('Running timemout:  %ds', self._running_timeout)
    self._log.debug('Queued timeout:    %ds', self._waiting_timeout)

    if config.has_section('lava.files'):
      self._log.info('Uploading files to FTP server')
      with Storage(config, self._log) as ftp:
        self._kernel_url = ftp.upload(config.get('lava.files', 'kernel'))
        self._rootfs_url = ftp.upload(config.get('lava.files', 'rootfs'),
            compressed=True)
        self._log.debug('Kernel URL:        %ds', self._kernel_url)
        self._log.debug('Rootfs URL:        %ds', self._rootfs_url)

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

      with Storage(config, self._log) as ftp:

        self._log.info('Downloading latest image from artifactory')

        file = ArtifactoryPath(atf_kernel, auth=atfauth, verify=False)
        with file.open() as k:
          local_kernel.write(k.read())

        file = ArtifactoryPath(atf_rootfs, auth=atfauth, verify=False)
        with file.open() as r:
          local_rootfs.write(r.read())

        local_kernel.seek(0)
        local_rootfs.seek(0)

        self._kernel_url = ftp.upload(local_kernel.name)
        self._rootfs_url = ftp.upload(local_rootfs.name, compressed=True)
        if not self._rootfs_url.endswith('.gz'):
          self._rootfs_url = self._rootfs_url + '.gz'

        self._log.debug('Kernel URL:        %s', self._kernel_url)
        self._log.debug('Rootfs URL:        %s', self._rootfs_url)

      local_kernel.close()
      local_rootfs.close()

      os.remove(local_kernel.name)
      os.remove(local_rootfs.name)

    self._log.info('Generating job description')
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
      self._log.info('Submitted Job ID: %d', self._jobid)
      self._log.info('job url:\n\n%s/%s/%d\n', self._lava_url, 'scheduler/job', self._jobid)

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
        status = server.scheduler.job_status(self._jobid).get('job_status')

      # Job didn't start
      if count >= self._waiting_timeout:
        self._log.error('Waiting timeout for queued Job-ID %d', self._jobid)
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

          self._log.info("Test PASSED %d", results.count('pass'))
          self._log.info("Test FAILED %d", results.count('fail'))

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
        status = server.scheduler.job_status(self._jobid).get('job_status')

      bar.finish()

      if count >= self._running_timeout:
        self._log.error("Running timeout")
        exit(1)
