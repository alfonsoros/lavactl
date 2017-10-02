# -*- coding: utf-8 -*-

from lava.server import FTPStorage

class Command(object):
    """Submit LAVA job definition command"""

    def __init__(self, logger=None):
        super(Command, self).__init__()
        self._logger = logger or logging.getLogger(__name__)

    def add_arguments(self, subparsers):
        self.parser = subparsers.add_parser(
            'list-images', help='list the images in the ftp server')
        self.parser.set_defaults(evaluate=self.evaluate)

    def evaluate(self, args, config):
        # Upload the files
        with FTPStorage(config=config, logger=self._logger) as remote:
            remote.list_images()

    def __repr__(self):
        return 'Command(list-images)'

    def __str__(self):
        return 'Command(list-images)'

    def __unicode__(self):
        return u'Command(list-images)'
