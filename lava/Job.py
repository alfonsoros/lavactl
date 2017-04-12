# -*- coding: utf-8 -*-

import os

from lava.server.Storage import Storage
from jinja2 import Environment, PackageLoader

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class Job(object):
  def __init__(self, config):
    self._conf = config
    self._env = Environment(loader=PackageLoader('lava.devices', 'templates'))

    # Upload the files
    with Storage() as lava_ftp:
      self._kernel_url = lava_ftp.upload(self._conf['kernel'])
      self._filesystem_url = lava_ftp.upload(self._conf['filesystem'])

    qemu = self._env.get_template('qemux86.yaml')

    self._job_definition = qemu.render({
      'kernel_url' : self._kernel_url,
      'file_system_url' : self._filesystem_url,
    })

  def definition(self):
    return self._job_definition
