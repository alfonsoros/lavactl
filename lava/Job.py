# -*- coding: utf-8 -*-

import os
import csv
import xmlrpclib
import time
import urllib2

from jinja2 import Environment, PackageLoader
from lava.config import default
from lava.server.Storage import Storage
from lava.server.interface import LavaRPC

class Job(object):
  def __init__(self, config):
    self._conf = config
    self._env = Environment(loader=PackageLoader('lava.devices', 'templates'))

    with Storage(default.lava_server, default.lava_ftp_usr, default.lava_ftp_pwd) as ftp:
      self._kernel_url = ftp.upload(self._conf['kernel'])
      self._filesystem_url = ftp.upload(self._conf['filesystem'])

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

      # wcount = number of times we loop while the job is running
      wcount = 0

      # count = number of times we loop waiting for the job to start
      count = 0

      while wcount < default.WAITING_TIMEOUT and count < default.RUNNING_TIMEOUT:
        status = server.scheduler.job_status(self._jobid)

        if status['job_status'] == 'Complete':
            # Check the tests passed
            response = urllib2.urlopen("http://%s:2041/results/%d/csv" %
                (default.lava_server, self._jobid))
            tests = csv.DictReader(response.read().split('\r\n'))

            if all([test["result"] == "pass" for test in tests]):
              exit(0)
            else:
              exit(1)

        elif status['job_status'] == 'Canceled' or status['job_status'] == 'Cancelling':
            exit(1)
        elif status['job_status'] == 'Submitted':
            wcount += default.SLEEP
        elif status['job_status'] == 'Running':
            count += default.SLEEP
        elif status['job_status'] == 'Incomplete':
            exit(1)
        time.sleep(default.SLEEP)

      if wcount >= default.WAITING_TIMEOUT:
        log.error("Queued timeout")
      else:
        log.error("Running timeout")
      exit(1)
