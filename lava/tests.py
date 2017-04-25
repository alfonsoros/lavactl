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
  def __init__(self, uri):
    parts = uri.split('#')
    if len(parts) == 3:
      self._uri, self._name, self._rev = parts
    elif len(parts) == 2:
      self._uri, self._name = parts
      self._rev = None
    else:
      raise AttributeError('Missing parameters in LAVA test %s', uri)

    if self._name.endswith('.yaml'):
      self._name = self._name.replace('.yaml', '')

  @property
  def repo(self):
    return self._uri

  @property
  def name(self):
    return self._name

  @property
  def revision(self):
    return self._rev
