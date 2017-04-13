# -*- coding: utf-8 -*-

import os
import xmlrpclib

from jinja2 import Environment, PackageLoader
from lava.config import default
from lava.server.Storage import Storage
from lava.server.interface import LavaRPC

class Job(object):
  def __init__(self, config):
    self._conf = config
    self._env = Environment(loader=PackageLoader('lava.devices', 'templates'))

    # Upload the files
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
      server.scheduler.submit_job(self._job_definition)
