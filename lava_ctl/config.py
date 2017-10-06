import yaml
import logging
import collections
from pkg_resources import resource_filename


class ConfigManager(object):
    """Handle the App's configuration values"""

    def load_file(self, filename):
        # Load default configuration
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
        access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
        return reduce(access, key.split('.'), self._config)

    def set(self, key, value):
        keys = key.split('.')
        access = lambda c, k: c[int(k)] if isinstance(c, list) else c[k]
        cont = reduce(access, keys[:-1], self._config)
        cont[keys[-1]] = value

    def has_option(self, key):
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

        if filename:
            user_config = self.load_file(filename)
            self.deep_update(user_config)

    def __repr__(self):
        return yaml.dump(self._config)
