# -*- coding: utf-8 -*-
import os
import paramiko

from exceptions import ImportError
from lava.config.default import DefaultConfig

class Storage(object):
  def __init__(self, config=None):
    if not config:
      config = DefaultConfig()

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

  def upload(self, localpath):
    name = os.path.basename(localpath)
    self._sftp.put(localpath, name)
    return u'%s/%s' % (self._download_url, name)
