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
from artifactory import ArtifactoryPath
from lava.server import LavaServer, FTPStorage
from lava.atf import AtfImage
from config import ConfigManager


class JobDefinition(object):
    """LAVA Job Definition

    This class can contain the complete definition of a LAVA job. This
    information is stored in a structure that is serializable in YAML format
    which can later be sen t to the LAVA server.

    Currently this class can be only initialized from a YAML file. Use the
    'filename' argument in the construction of the class.

    """

    def __init__(self, filename=None, config=None, logger=None):
        """Parse and store the LAVA job definition.

        Args:
            filename (str): Path to the input file

        """
        self._logger = logger or logging.getLogger(__name__ + '.JobDefinition')
        self._conf = config or ConfigManager()

        if filename:
            with open(filename, 'rt') as f:
                content = f.read()
                try:
                    self._yaml = yaml.load(content)
                except yaml.YAMLError:
                    self._logger.error(
                        "Incorrect YAML format in file name %s", filename)
                    raise RuntimeError("Invalid YAML file format", filename)

        # Try to instantiate a LAVA definition using the configuration
        # parameters
        else:

            self._logger.debug('Generating job description from arguments')
            env = Environment(loader=PackageLoader('lava.devices'))

            # These are the minimum required parameters to instantiate a job
            REQUIRED_ARGUMENTS = [
                'lava.job.device',
                'lava.job.kernel',
                'lava.job.rootfs',
            ]


            if not all([self._conf.has_option(o) for o in REQUIRED_ARGUMENTS]):
                self._logger.error("Missing arguments to instantiate LAVA job")
                raise RuntimeError("Missing arguments to instantiate LAVA job")

            device = self._conf.get('lava.job.device')

            try:
                qemu = env.get_template(device + '.yaml')
            except TemplateNotFound:
                self._logger.error('Device %s not supported', device)
                raise RuntimeError('Device not supported', device)

            # Template context
            context = {}
            context['kernel_url'] = self._conf.get('lava.job.kernel')
            context['rootfs_url'] = self._conf.get('lava.job.rootfs')
            context['compression'] = True and self._conf.get('lava.job.compressed')

            self._yaml = yaml.load(qemu.render(context))

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
            self._lava_server = LavaServer(config=self._conf, logger=self._logger)
        return self._lava_server

    def valid(self):
        if getattr(self, '_valid', None) is None:
            self._valid = self.lava_server.validate(self.__str__())
        return self._valid

    def submit(self):
        if self.valid():
            self._jobid = self.lava_server.submit(self.__str__())
        else:
            self._logger.error("Trying to submit invalid job")
            raise RuntimeError("Trying to submit invalid job")

        if self._jobid:
            self._logger.debug("Job Submitted successfully -- ID: %s", self._jobid)
        else:
            self._logger.error("Couldn't submit LAVA job")
            raise RuntimeError("Couldn't submit LAVA job")

    def submit_and_wait(self):
        return self.lava_server.submit_and_wait(self.__str__())

    def __str__(self):
        return yaml.dump(self._yaml)

    def __repr__(self):
        return yaml.dump(self._yaml)
