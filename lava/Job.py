# -*- coding: utf-8 -*-

import os
import csv
import xmlrpclib
import time
import urllib2
import logging

from progress.bar import Bar
from jinja2 import Environment, PackageLoader
from lava.server.Storage import Storage
from lava.server.interface import LavaRPC

class Job(object):
  def __init__(self, config, logger=None):
    self._log = logger.getChild('job') if logger else logging.getLogger('lava.job')

    self._lava_url = config.get('lava.server', 'url')
    self._sleep = config.getint('lava.jobs', 'sleep')
    self._running_timeout = config.getint('lava.jobs', 'running_timeout')
    self._waiting_timeout = config.getint('lava.jobs', 'waiting_timeout')
    self._env = Environment(loader=PackageLoader('lava.devices', 'templates'))

    self._log.debug('Lava URL:          %s', self._lava_url)
    self._log.debug('Waiting-loop time: %ds', self._sleep)
    self._log.debug('Running timemout:  %ds', self._running_timeout)
    self._log.debug('Queued timeout:    %ds', self._waiting_timeout)

    self._log.info('Uploading files to FTP server')
    with Storage(config) as ftp:
      self._kernel_url = ftp.upload(config.get('lava.files', 'kernel'))
      self._filesystem_url = ftp.upload(config.get('lava.files', 'filesystem'))

    self._log.info('Generating job description')
    qemu = self._env.get_template('qemux86.yaml')
    self._job_definition = qemu.render({
      'kernel_url' : self._kernel_url,
      'file_system_url' : self._filesystem_url,
    })


  def definition(self):
    return self._job_definition

  def submit(self):
    with LavaRPC() as server:
      self._jobid = server.scheduler.submit_job(self._job_definition)
      self._log.info('Submitted Job ID: %d', self._jobid)
      self._log.info('job url:\n\n%s/%s/%d\n', self._lava_url, 'scheduler/job', self._jobid)

  def poll(self):
    with LavaRPC() as server:

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

          if all([test["result"] == "pass" for test in tests]):
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

      if count >= self._waiting_timeout:
        self._log.error("Running timeout")
        exit(1)
