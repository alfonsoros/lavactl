#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

from ConfigParser import ConfigParser
from pkg_resources import resource_filename
from lava.Job import Job
from lava.config.default import DefaultConfig

if __name__ == '__main__':

  if len(sys.argv) == 2 and sys.argv[1] == 'bash':
    with open('bash/lava-ctl', 'r') as f:
      sys.stdout.write(f.read())
      exit(0)
  elif len(sys.argv) == 2 and sys.argv[1] == '--version':
    with open('VERSION', 'r') as f:
      sys.stdout.write(f.read())
      exit(0)

  import argparse
  parser = argparse.ArgumentParser()

  def path_exists(filepath):
    return filepath if os.path.exists(filepath) else parser.error("%s does not exists" % filepath)

  parser.add_argument('kernel', help='Filepath to the Kernel.')
  parser.add_argument('filesystem', help='Filepath to the File System.')
  parser.add_argument('--show-config', action='store_true', help='Print configuration')
  parser.add_argument('-c', '--config', dest='config', metavar='FILE', type=path_exists, help='Config file')
  parser.add_argument('-v', '--verbose', action='store_true', help='Show debug info')

  args = parser.parse_args()


  if args.config:
    config = ConfigParser()
    config.read(args.config)
  else:
    config = DefaultConfig()

  config.add_section('lava.files')
  config.set('lava.files', 'kernel', args.kernel)
  config.set('lava.files', 'filesystem', args.filesystem)

  if args.show_config:
    config.write(sys.stdout)

  logging.basicConfig()
  logger = logging.getLogger('lava')

  if args.verbose:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)

  job = Job(config, logger=logger)
  job.submit()
  job.poll()
