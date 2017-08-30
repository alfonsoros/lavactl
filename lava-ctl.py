#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

from ConfigParser import ConfigParser
from lava.jobs import Job
from lava.tests import Test
from config.default import DefaultConfig


def setup_logging(name, debug):
  logging.basicConfig()
  logger = logging.getLogger('lava-ctl')
  logger.setLevel(logging.DEBUG) if debug else logger.setLevel(logging.INFO)
  return logger

def load_config(conf_file=None):
  if conf_file:
    config = ConfigParser()
    config.read(conf_file)
  else:
    config = DefaultConfig()
  return config


if __name__ == '__main__':

  if len(sys.argv) == 2 and sys.argv[1] == 'bash':
    with open('bash/lava-ctl', 'r') as f:
      sys.stdout.write(f.read())
      exit(0)

  import argparse
  parser = argparse.ArgumentParser()

  def path_exists(filepath):
    return filepath if os.path.exists(filepath) else parser.error("%s does not exists" % filepath)


  parser.add_argument('--kernel', metavar='FILE', type=path_exists, help='kernel file.')
  parser.add_argument('--rootfs', metavar='FILE', type=path_exists, help='rootfs file.')

  parser.add_argument('--test-repo', dest='test_repos', metavar='URL', action='append',
                      help='git url for test repository')

  parser.add_argument('--test-param', dest='test_params', metavar='KEY=VALUE',
                      action='append', help='parameter to make available to the tests')

  parser.add_argument('-c', '--config', metavar='FILE', type=path_exists, help='config file')

  parser.add_argument('--debug', action='store_true', help='show debug info')
  parser.add_argument('--version', action='store_true', help='print version')
  parser.add_argument('--no-progress-bars', action='store_true', help='skip progress bars.')

  args = parser.parse_args()

  # Print version and exit
  if args.version:
    version_file = fn = os.path.join(os.path.dirname(__file__), 'VERSION')
    with open(version_file, 'r') as f:
      sys.stdout.write(f.read())

  # Setup the logger
  logger = setup_logging('lava-ctl', args.debug)

  # Init configuration
  config = load_config(args.config)

  config.add_section('logging')
  config.set('logging', 'progress-bars', str(not args.no_progress_bars))

  # Test provided image
  if args.kernel or args.rootfs:
    if args.kernel and args.rootfs and args.kernel != args.rootfs:
      config.add_section('lava.files')
      config.set('lava.files', 'kernel', args.kernel)
      config.set('lava.files', 'rootfs', args.rootfs)
    else:
      logger.error('--kernel and --rootfs must be specified together')
      exit(1)

  # Lava tests
  if args.test_repos:
    config.add_section('lava.test')

    if args.test_params:
      config.set('lava.test', 'repos', [Test(repo, args.test_params) for repo in args.test_repos])
    else:
      config.set('lava.test', 'repos', [Test(repo) for repo in args.test_repos])

  if args.debug:
    logger.debug('lava-ctl configuration')
    config.write(sys.stdout)

  job = Job(config, logger=logger)
  job.submit()
  job.poll()
