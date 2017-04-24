#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

from ConfigParser import ConfigParser
from pkg_resources import resource_filename
from lava.Job import Job
from config.default import DefaultConfig

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

  parser.add_argument('--kernel', metavar='FILE', type=path_exists, help='kernel file.')
  parser.add_argument('--rootfs', metavar='FILE', type=path_exists, help='rootfs file.')

  parser.add_argument('--show-config', action='store_true', help='Print configuration')
  parser.add_argument('-c', '--config', metavar='FILE', type=path_exists, help='Config file')
  parser.add_argument('-v', '--verbose', action='store_true', help='Show debug info')

  args = parser.parse_args()

  # Init logging
  logging.basicConfig()
  logger = logging.getLogger('lava')
  if args.verbose:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)

  # Init configuration
  if args.config:
    config = ConfigParser()
    config.read(args.config)
  else:
    config = DefaultConfig()

  if args.kernel or args.rootfs:
    if args.kernel and args.rootfs and args.kernel != args.rootfs:
      config.add_section('lava.files')
      config.set('lava.files', 'kernel', args.kernel)
      config.set('lava.files', 'filesystem', args.rootfs)
    else:
      logger.error("--kernel and --rootfs must be specified together")
      exit(1)

  if args.show_config:
    config.write(sys.stdout)

  job = Job(config, logger=logger)
  job.submit()
  job.poll()
