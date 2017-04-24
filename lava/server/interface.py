import xmlrpclib

class LavaRPC(object):
  def __init__(self, config):
    user = config.get('lava.server', 'user')
    token = config.get('lava.server', 'token')
    server = config.get('lava.server', 'addr')
    self._url = "http://%s:%s@%s:2041/RPC2" % (user, token, server)

  def __enter__(self):
    return xmlrpclib.ServerProxy(self._url)

  def __exit__(self, exc_type, exc_value, traceback):
    pass
