#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lava.Job import Job

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('kernel', help='Filepath to the Kernel.')
  parser.add_argument('filesystem', help='Filepath to the File System.')

  args = parser.parse_args()

  config = {}
  config['kernel'] = args.kernel
  config['filesystem'] = args.filesystem

  job = Job(config)
  job.submit()
  job.poll()
