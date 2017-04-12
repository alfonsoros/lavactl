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

class Storage:
  def __init__(self):
    try:
      addr = os.environ['LAVA_STORAGE_FTP_ADDR']
      usr =  os.environ['LAVA_STORAGE_FTP_USER']
      pwd =  os.environ['LAVA_STORAGE_FTP_PASS']
    except KeyError:
      raise ImportError("lava.Storage", "Set LAVA_STORAGE_* env variables")

    self._transport = paramiko.Transport((addr, 2040))
    self._transport.connect(username=usr, password=pwd)

    self._sftp = paramiko.SFTPClient.from_transport(self._transport)

  def __str__(self):
    return u'Lava master storage'

  def __del__(self):
    self._sftp.close()
    self._transport.close()

  def upload(self, localpath):
    self._sftp.put(localpath, os.path.basename(localpath))
