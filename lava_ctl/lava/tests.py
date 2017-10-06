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
        inline = ['name', 'steps']
        remote = ['repository', 'name', 'revision']
        is_inline = all([p in config for p in inline])
        is_remote = all([p in config for p in remote])
        if not is_inline and not is_remote:
            raise RuntimeError('Error test configuration', config)
        self._inline = is_inline

    def __init__(self, config=None, logger=None):
        if not config:
            raise RuntimeError('Missing test configuration')
        self.check_configuration(config)

        if not self._inline:
            self._repo = config['repository']
            self._name = config['name']
            self._revision = config['revision']
        else:
            self._name = config['name']
            self._steps = config['steps']

        if 'params' in config:
            self._params = config['params']
        else:
            self._params = {}

        if 'role' in config:
            self._roles = config['role']
        else:
            self._roles = []

    @property
    def inline(self):
        return self._inline

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

    @property
    def roles(self):
        return self._roles

    @property
    def steps(self):
        return self._steps
