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

import yaml
import logging
import collections
from pkg_resources import resource_filename


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
        cont[keys[-1]] = value

    def has_option(self, key):
	"""Check if a key is available in the configuration"""
        try:
            self.get(key)
            return True
        except KeyError:
            return False


    def __init__(self, filename=None, logger=None):
        super(ConfigManager, self).__init__()
        self.logger = logger or logging.getLogger(__name__ + '.ConfigManager')

        # Load default configuration
        self._config = self.load_file(
            resource_filename('lava_ctl', 'resources/default_conf.yaml'))

		# Override default configuration with the user defined configuration file
        if filename:
            user_config = self.load_file(filename)
            self.deep_update(user_config)

    def __repr__(self):
        return yaml.dump(self._config)
