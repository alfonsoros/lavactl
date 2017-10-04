# -*- coding: utf-8 -*-

import sys
import os
import xmlrpclib
import time
import urllib2
import logging
import tempfile
import yaml

from progress.bar import Bar
from jinja2 import Environment, PackageLoader, TemplateNotFound
from lava.server import LavaServer, FTPStorage
from config import ConfigManager

class Job(object):
    """Minimal configuration to run a LAVA job

    lava-ctl tries to help the user by defaulting the LAVA configuration as
    much as possible. However, the minimum configuration required for running a
    LAVA job is:

    - kernel URL: from where to download the kernel file
    - rootfs URL: from where to download the root file system
    - device: device type where to run the job

    """
    def __init__(self, config=None, logger=None):
        super(Job, self).__init__()
        self._logger = logger or logging.getLogger(__name__)
        self._tests = []
        if not config:
            raise RuntimeError('Missing configuration for instantiating job')
        self._kernel = config['kernel']
        self._rootfs = config['rootfs']
        self._device = config['device']

        if 'compressed' in config:
            self._compressed = config['compressed']
        else:
            self._compressed = self.rootfs.endswith('.gz')

    @property
    def kernel(self):
        return self._kernel

    @property
    def rootfs(self):
        return self._rootfs

    @property
    def device(self):
        return self._device

    @property
    def compressed(self):
        return self._compressed

    @property
    def tests(self):
        return self._tests

    def add_test(self, test):
        self._tests.append(test)

    def has_tests(self):
        return len(self.tests) > 0


class JobDefinition(object):
    """LAVA Job Definition

    This class can contain the complete definition of a LAVA job. This
    information is stored in a structure that is serializable in YAML format
    which can later be sen t to the LAVA server.

    Currently this class can be only initialized from a YAML file. Use the
    'filename' argument in the construction of the class.

    """

    def __init__(self, job=None, filename=None, config=None, logger=None):
        """Parse and store the LAVA job definition.

        Args:
            filename (str): Path to the input file

        """
        self._logger = logger or logging.getLogger(__name__ + '.JobDefinition')
        self._conf = config or ConfigManager()

        if filename:
            try:
                with open(filename, 'rt') as f:
                    content = f.read()
                    self._yaml = yaml.load(content)
            except IOError, e:
                self._logger.error("Couldn't read the file %s", filename)
                raise e

            except yaml.YAMLError, e:
                self._logger.error("Invalid YAML in file %s", filename)
                raise e

        # Try to instantiate a LAVA definition using the configuration
        # parameters
        elif job:
            env = Environment(loader=PackageLoader('lava.devices'))

            try:
                device = env.get_template(job.device + '.yaml')
            except TemplateNotFound:
                self._logger.error('Device %s not supported', job.device)
                raise RuntimeError('Device not supported', job.device)

            self._logger.debug('Found template job for device %s', job.device)

            # Template context
            context = {}
            context['kernel_url'] = job.kernel
            context['rootfs_url'] = job.rootfs
            context['compression'] = job.compressed

            # Add the specified tests if any
            if job.has_tests():
                context['test'] = True
                context['test_repos'] = []

                for test in job.tests:
                    context['test_repos'].append(test)

            self._yaml = yaml.load(device.render(context))

        self._logger.debug("Job Definition:\n=== BEGIN JOB DEFINITION ===\n%r\n"
                           "=== END JOB DEFINITION ===", self)

    def get(self, key):
        """Get te value associated to the input key in the job configuration"""
        try:
            # solve keys encoded using 'dot' notation
            access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
            return reduce(access, key.split('.'), self._yaml)
        except KeyError:
            self._logger.error("Missing key %s in LAVA job description", key)
        except:
            self._logger.error("Incorrect LAVA Job definition")
        return None

    def set(self, key, value):
        keys = key.split('.')
        access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
        cont = reduce(access, keys[:-1], self._yaml)
        cont[keys[-1]] = value

    @property
    def lava_server(self):
        return self._lava_server

    @lava_server.getter
    def lava_server(self):
        if getattr(self, '_lava_server', None) is None:
            self._lava_server = LavaServer(
                config=self._conf, logger=self._logger)
        return self._lava_server

    def valid(self):
        if getattr(self, '_valid', None) is None:
            self._valid = self.lava_server.validate(self.__str__())
        return self._valid

    def submit(self, wait=True):
        if self.valid():
            result = self.lava_server.submit(self.__str__(), wait)
        else:
            self._logger.error("Trying to submit invalid job")
            raise RuntimeError("Trying to submit invalid job")

        return result if result else False

    def __str__(self):
        return yaml.dump(self._yaml)

    def __repr__(self):
        return yaml.dump(self._yaml)
