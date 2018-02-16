# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Siemens AG
# Author: Alfonso Ros Dos Santos
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import copy
import yaml
import logging
from collections import defaultdict

from cerberus import Validator
from pkg_resources import resource_filename

from lava_ctl.config.schemas import LAVACTL_SCHEMA


yaml.add_representer(defaultdict, yaml.representer.Representer.represent_dict)


class Config(object):
    """Base class for a Configuration dictionary

    Every configuration structure is basically a dictionary of key-value pairs
    that has a shape defined in a associated schema.

    The dot-notation is used to access the recursive configuration
    estructure. For example, if the configuration is:

    { 'a': { 'b': { 'c': 42 } }

    you can access the value of 'c' by using the key 'a.b.c'
    """

    def __init__(self, config={}, schema={}, filename=None, logger=None):
        """Config class initializer

        keyword arguments:
        config -- the dictionary with the key-value pairs (default {})
        schema -- a dictionary with the Cerberus schema definition (default {})
        logger -- the logger class (default None)
        """
        super(Config, self).__init__()
        self._logger = logger or logging.getLogger(__name__)
        self._log_extra = {'config': config, 'schema': schema}
        self._logger.debug(
            'config %(config)s with %(schema)s', extra=self._log_extra)
        self._config = defaultdict(lambda: {})
        self._config.update(config)
        self._schema = schema
        self._validator = Validator(self._schema)
        self._config_file = filename

        if self._config_file:
            self.load()

    def get(self, key):
        """Return the value associated to the key
        arguments:
        key -- key string in dot-notation
        """
        try:
            access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
            return reduce(access, key.split('.'), self._config)
        except (IndexError, KeyError):
            self._logger.error('wrong config key %s', key)
            raise KeyError('wrong config key', key)

    def has(self, key):
        """Return True if the key is present in the configuration
        arguments:
        key -- key string in dot-notation
        """
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def set(self, key, value):
        """Set the value for a key in the configuration
        arguments:
        key -- key string in dot-notation
        value -- the value associated to the key
        """
        try:
            access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
            keys = key.split('.')
            parents, key = keys[:-1], keys[-1]
            conf = reduce(access, parents, self._config)
            self._logger.debug("setting %s to %s", key, value)
            conf[key] = value
            self._logger.debug("validating config", extra=self._log_extra)
        except (IndexError, KeyError):
            self._logger.error('wrong config key %s', key)
            raise KeyError('wrong config key', key)

    def load(self, filename=None):
        """Loads the configuration from the input file
        keyword arguments:
        filename -- a path to a YAML file with configuration information
        """
        path = self._config_file or filename
        self._logger.debug("loading config from file: %s", path)
        try:
            with open(path, 'r') as src:
                self._config.clear()
                self._config.update(yaml.load(src))
        except IOError, exc:
            self._logger.error('Could not read from file %s', path)
            raise exc

        except yaml.YAMLError, exc:
            self._logger.error("YAML Error with file: %s", path)
            raise exc

    def write(self, filename=None):
        """Write this configuration to a file
        keyword arguments:
        filename -- a path to a YAML file with configuration information
        """
        path = self._config_file or filename
        self._logger.debug("writing config to file: %s", path)
        self.validate()
        try:
            with open(path, 'w') as cf:
                cf.write(yaml.dump(self._config))
        except IOError, exc:
            self._logger.error('Could not write to file %s', self._filename)
            raise exc

    def validate(self):
        if not self._validator.validate(self._config):
            self._logger.error('configuration error %s',
                               self._validator.errors)
            raise RuntimeError('wrong configuration', self._validator.errors)

    def __repr__(self):
        return yaml.dump(self._config)


class ConfigManager(Config):
    """Handle the App's configuration values"""

    def __init__(self, filename=None, logger=None):
        config_file = filename or resource_filename(
            'lava_ctl', 'resources/lavactl_conf.yaml')

        super(ConfigManager, self).__init__(
            schema=LAVACTL_SCHEMA, filename=config_file, logger=logger)
