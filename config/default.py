import os
import logging

from ConfigParser import ConfigParser
from pkg_resources import resource_filename

class DefaultConfig(ConfigParser):
  """Default configuration for the lava-ctl

  This class looks for the following environment variables

  - ATF_USER
  - ATF_PASS

  """
  def required_environment(self):
    required = [
      'ATF_USER',
      'ATF_PASS',
    ]

    env_dict = {}
    for var in required:
      if var in os.environ:
        env_dict[var] = os.environ[var]
      else:
        self.logger.warning("missing %s environment variable", var)
    return env_dict

  def __init__(self, logger=None):
    self.logger = logger or logging.getLogger(__name__ + '.DefaultConfig')
    ConfigParser.__init__(self, self.required_environment())
    self.read(resource_filename('config', 'default.cfg'))
