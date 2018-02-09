"""
Copyright (c) 2017 Siemens AG
Author: Alfonso Ros Dos Santos

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import copy
import yaml
import logging
import collections

from cerberus import Validator
from pkg_resources import resource_filename


CONFIG_SCHEMA = {
    'default_image': {
        'type': 'dict',
                'schema': {
                    'compressed': {'type': 'boolean'},
                    'device': {'type': 'string'},
                    'kernel': {'type': 'string'},
                    'rootfs': {'type': 'string'},
                }
    },
    'lava': {
        'type': 'dict',
                'schema': {
                    'server': {
                        'type': 'dict',
                        'schema': {
                            'host': {'type': 'string'},
                            'port': {'type': 'number'},
                            'user': {'type': 'string'},
                            'token': {'type': 'string'},
                            'jobs': {
                                'type': 'dict',
                                'schema': {
                                    'timeout': {'type': 'number'},
                                },
                            },
                        }
                    },
                    'publisher': {
                        'type': 'dict',
                        'schema': {
                            'port': {'type': 'number'}
                        }
                    }
                }
    },
}


class ConfigValidator(Validator):
    """lavactl Configuration Validator"""
    def __init__(self, *args, **kwargs):
        super(ConfigValidator, self).__init__(*args, **kwargs)


class ConfigManager(object):
    """Handle the App's configuration values"""

    def load_file(self, filename):
        """Load configuration from a file"""
        with open(filename, 'r') as src:
            try:
                return yaml.load(src)
            except yaml.YAMLError, exc:
                self.logger.error("YAML Error with file: %s", filename)
                raise exc

    def deep_update(self, config):
        """Overrides current configuration with the values of the input one"""
        def update(d, u):
            for k, v in u.iteritems():
                if isinstance(v, collections.Mapping):
                    r = update(d.get(k, {}), v)
                    d[k] = r
                else:
                    d[k] = u[k]
            return d
        update(self._config, config)

    def get(self, key):
        """Get the value for a key from the configuration"""
        access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
        return reduce(access, key.split('.'), self._config)

    def set(self, key, value):
        """Set the value for a key in the configuration"""
        keys = key.split('.')
        access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]

        cont = reduce(access, keys[:-1], self._config)

        self.logger.debug("setting key: %s, to value: %s" % (key, value))
        cont[keys[-1]] = value

        self.validate()

    def validate(self):
        if not self._validator.validate(self._config, CONFIG_SCHEMA):
            raise RuntimeError('Invalid config parameters: %s' %
                               self._validator.errors)

    def has_option(self, key):
        """Check if a key is available in the configuration"""
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def write(self):
        with open(self._config_file, 'w') as cf:
            cf.write(yaml.dump(self._config))

    def __init__(self, filename=None, logger=None):
        super(ConfigManager, self).__init__()
        self.logger = logger or logging.getLogger(__name__ + '.ConfigManager')

        self._config_file = resource_filename(
            'lava_ctl', 'resources/lavactl_conf.yaml')

        # Load static configuration
        self._config = self.load_file(self._config_file)

        # Schema validator
        self._validator = ConfigValidator()

        # Override default configuration with the user defined configuration
        # file
        if filename:
            user_config = self.load_file(filename)
            self.deep_update(user_config)

        self.validate()

    def __repr__(self):
        return yaml.dump(self._config)
