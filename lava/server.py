# -*- coding: utf-8 -*-
import os
import paramiko
import gzip
import shutil
import logging
import xmlrpclib
import logging

from progress.bar import Bar
from config.default import DefaultConfig


class LavaServer(object):
  """Handle the communication with the LAVA Master server

  This class requires the user to define the following configuration
  parameters:

    [lava.server]
    addr = 139.25.40.26
    port = 2041
    files_prefix = lava-files
    files = %(url)s/%(files_prefix)s
    user = %(LAVA_USER)s
    token = %(LAVA_TOKEN)s


  """

  def read_config(self, config):
    CONFIG_SECTION = 'lava.server'
    if not config.has_section(CONFIG_SECTION):
        self.logger.error('Missing %s configuration section', CONFIG_SECTION)
        raise RuntimeError('Missing Configuration Section: ', CONFIG_SECTION)

    config_params = ['addr', 'port', 'files_prefix', 'user', 'token']

    # Check all the parameters are set
    missing = [p for p in config_params if not config.has_option(CONFIG_SECTION, p)]

  def __init__(self, config=None, logger=None):
    super(LavaServer, self).__init__()
    self.logger = logger or logging.getLogger(__name__ + '.LavaServer')

    if not config:
      self.logger.debug("Using Default Configuration for LAVA Master")
      self.read_config(DefaultConfig())
    else:
      self.read_config(config)


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

class Storage(object):

    def __init__(self, config=None):
        if not config:
            config = DefaultConfig()

        self._logger = logging.getLogger(__name__)
        self._logger.progress_bar = config.getboolean(
            'logging', 'progress-bars')

        server = config.get('lava.server', 'addr')
        port = config.getint('lava.sftp', 'port')
        usr = config.get('lava.sftp', 'user')
        pwd = config.get('lava.sftp', 'pass')

        self._transport = paramiko.Transport((server, port))
        self._transport.connect(username=usr, password=pwd)
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)
        self._download_url = config.get('lava.server', 'files')

    def __str__(self):
        return u'Lava master ftp storage'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._sftp.close()
        self._transport.close()

    def upload(self, path, compressed=False):
        # Try to compress the file before uploading
        if compressed and not path.endswith('.gz'):
            self._logger.info('Gzip the filesystem before uploading')
            with open(path, 'rb') as f_in, gzip.open(path + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            path = path + '.gz'

        # Some fancy progress bar
        bar = Bar('Uploading %s' % os.path.basename(path))

        def update_progress(current, total):
            bar.index = current
            bar.max = total
            bar.update()

        if not self._logger.progress_bar:
            update_progress = None

        name = os.path.basename(path)
        self._sftp.put(path, name, callback=update_progress)
        bar.finish()
        return u'%s/%s' % (self._download_url, name)
