# -*- coding: utf-8 -*-
import os
import paramiko
import gzip
import shutil
import logging

from progress.bar import Bar
from lava.config.default import DefaultConfig

class Storage(object):
  def __init__(self, config=None, logger=None):
    if not config:
      config = DefaultConfig()

    self._log = logger.getChild('sftp') if logger else logging.getLogger('sftp')

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
      self._log.info('Gzip the filesystem before uploading')
      with open(path, 'rb') as f_in, gzip.open(path + '.gz', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
      path = path + '.gz'

    # Some fancy progress bar
    bar = Bar('Uploading %s' % os.path.basename(path))

    def update_progress(current, total):
      bar.index = current
      bar.max = total
      bar.update()

    name = os.path.basename(path)
    self._sftp.put(path, name, callback=update_progress)
    bar.finish()
    return u'%s/%s' % (self._download_url, name)
