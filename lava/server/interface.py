import xmlrpclib
import lava.config.default as conf

class LavaRPC(object):
  def __enter__(self):
    url = "http://%s:%s@%s:2041/RPC2" % (conf.lava_user, conf.lava_token, conf.lava_server)
    return xmlrpclib.ServerProxy(url)

  def __exit__(self, exc_type, exc_value, traceback):
    pass
