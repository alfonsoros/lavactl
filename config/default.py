import os

from ConfigParser import ConfigParser
from pkg_resources import resource_filename

class DefaultConfig(ConfigParser):
  def __init__(self):
    ConfigParser.__init__(self, os.environ)
    self.read(resource_filename('config', 'default.cfg'))
