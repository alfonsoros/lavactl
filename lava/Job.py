# -*- coding: utf-8 -*-

import os
import csv
import xmlrpclib
import time
import urllib2

from progress.bar import Bar
from jinja2 import Environment, PackageLoader
from lava.server.Storage import Storage
from lava.server.interface import LavaRPC

class Job(object):
  def __init__(self, config):
    self._lava_url = config.get('lava.server', 'url')
    self._sleep = config.getint('lava.jobs', 'sleep')
    self._running_timeout = config.getint('lava.jobs', 'running_timeout')
    self._waiting_timeout = config.getint('lava.jobs', 'waiting_timeout')
    self._env = Environment(loader=PackageLoader('lava.devices', 'templates'))

    with Storage(config) as ftp:
      self._kernel_url = ftp.upload(config.get('lava.files', 'kernel'))
      self._filesystem_url = ftp.upload(config.get('lava.files', 'filesystem'))

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

  def poll(self):
    with LavaRPC() as server:

      wcount = 0 # number of loops while the job is running
      count = 0  # number of loops waiting for the job to start

      bar = Bar('Polling job %d' % self._jobid, max=self._running_timeout)

      while wcount < self._waiting_timeout and count < self._running_timeout:
        status = server.scheduler.job_status(self._jobid)

        bar.index = count
        bar.update()

        if status['job_status'] == 'Complete':
          bar.finish()

          # Check the tests passed
          response = urllib2.urlopen("%s/results/%d/csv" %
              (self._lava_url, self._jobid))
          tests = csv.DictReader(response.read().split('\r\n'))

          if all([test["result"] == "pass" for test in tests]):
            exit(0)
          else:
            exit(1)

        elif status['job_status'] == 'Canceled' or status['job_status'] == 'Cancelling':
            exit(1)
        elif status['job_status'] == 'Submitted':
            wcount += self._sleep
        elif status['job_status'] == 'Running':
            count += self._sleep
        elif status['job_status'] == 'Incomplete':
            exit(1)

        # Wait _sleep seconds
        time.sleep(self._sleep)

      if wcount >= self._waiting_timeout:
        log.error("Queued timeout")
      else:
        log.error("Running timeout")
      exit(1)
