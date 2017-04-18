import os

from ConfigParser import ConfigParser
from pkg_resources import resource_filename

SLEEP = 5
WAITING_TIMEOUT = 600
RUNNING_TIMEOUT = 120

lava_server = os.environ['LAVA_SERVER_ADDR']
lava_port = 2041

lava_user = os.environ['LAVA_USER']
lava_token = os.environ['LAVA_TOKEN']

lava_rpc_url = "http://%s:%s@%s/RPC2" % (lava_user, lava_token, lava_server)

class DefaultConfig(ConfigParser):
  def __init__(self):
    ConfigParser.__init__(self, os.environ)
    self.read(resource_filename('lava.config', 'default.cfg'))

# print config.get('lava.server', 'addr')
# print config.options('lava.server')
# print dict(config.items('lava.server')).get('addr')
