#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jinja2 import Environment, PackageLoader

def qemu_job(kernel_url, fs_url):
  env = Environment(loader=PackageLoader('lava', 'templates'))
  qemu = env.get_template('qemux86.yaml')
  context = {}
  context['kernel_url'] = kernel_url
  context['file_system_url'] = fs_url
  print qemu.render(context)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('kernel_url', help='URL to the Kernel')
  parser.add_argument('filesystem_url', help='URL to the file system.')

  args = parser.parse_args()

  print qemu_job(args.kernel_url, args.filesystem_url)
