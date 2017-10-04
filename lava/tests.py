class Test(object):
    """

    A LAVA test requires 2 arguments, the first is the git URL where the test
    definitions are and the second is the name of the file with the test to
    evaluate. An optional third argumen is the revision for the git repository.

    In order to have an 'easy' way to specify these 3 things as a command line
    argument, we have decided to concatenate these 3 in a string joined by '#'
    characters in the following order:

    git@repository/url.git#test_name.yaml#revision

    where the revision is optional.

    """

    def check_configuration(self, config):
        REQUIRED = ['repository', 'name', 'revision']
        missing = [p for p in REQUIRED if p not in config]
        if len(missing) > 0:
            raise RuntimeError('missing keys in test conf', missing)

    def __init__(self, config=None, logger=None):
        if not config:
            raise RuntimeError('Missing test configuration')
        self.check_configuration(config)
        self._repo = config['repository']
        self._name = config['name']
        self._revision = config['revision']

        if 'params' in config:
            self._params = config['params']
        else:
            self._params = {}

    @property
    def repo(self):
        return self._repo

    @property
    def name(self):
        return self._name

    @property
    def revision(self):
        return self._revision

    @property
    def params(self):
        return self._params
