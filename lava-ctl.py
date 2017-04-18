#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from lava.Job import Job
from lava.config.default import DefaultConfig

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('kernel', help='Filepath to the Kernel.')
  parser.add_argument('filesystem', help='Filepath to the File System.')
  parser.add_argument('--show-config', action='store_true', help='Print configuration')

  args = parser.parse_args()

  config = DefaultConfig()
  config.add_section('lava.files')
  config.set('lava.files', 'kernel', args.kernel)
  config.set('lava.files', 'filesystem', args.filesystem)

  if args.show_config:
    config.write(sys.stdout)

  job = Job(config)
  job.submit()
  job.poll()
