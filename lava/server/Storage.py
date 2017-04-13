# -*- coding: utf-8 -*-
import os
import paramiko

from exceptions import ImportError

"""
  The following environment variables are required:

  LAVA_STORAGE_FTP_ADDR
  LAVA_STORAGE_FTP_USER
  LAVA_STORAGE_FTP_PASS
"""

class Storage(object):
  def __init__(self, addr, usr, pwd):
    self._server = addr
    self._transport = paramiko.Transport((addr, 2040))
    self._transport.connect(username=usr, password=pwd)

    self._sftp = paramiko.SFTPClient.from_transport(self._transport)

  def __str__(self):
    return u'Lava master storage'

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self._sftp.close()
    self._transport.close()

  def upload(self, localpath):
    name = os.path.basename(localpath)
    self._sftp.put(localpath, name)
    return u'http://%s:2041/lava-files/%s' % (self._server, name)
