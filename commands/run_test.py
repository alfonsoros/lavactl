# -*- coding: utf-8 -*-
import os
import sys
import yaml

from lava.server import FTPStorage
from lava.jobs import JobDefinition


class Command(object):
    """Run the specified lava tests"""

    def __init__(self, logger=None):
        super(Command, self).__init__()
        self._logger = logger or logging.getLogger(__name__)

    def add_arguments(self, subparsers):
        self.parser = subparsers.add_parser(
            'run-test', help='Run tests on an image')
        self.parser.add_argument(
            'yaml_file', type=str, metavar='FILE', help='test description')
        self.parser.add_argument(
            '--no-wait', action='store_true', help='Don\'t wait for job result')
        self.parser.set_defaults(evaluate=self.evaluate)

    def evaluate(self, args, config):
        """Evaluate if the necessary arguments are present"""

        # Check the file exists
        if not os.path.exists(args.yaml_file):
            raise RuntimeError('File does not exist', args.yaml_file)

        with open(args.yaml_file) as testfile:
            test = yaml.load(testfile.read())

        self._logger.debug("test file content:\n%s",
                           yaml.dump(test, default_flow_style=False))

        with FTPStorage(config=config, logger=self._logger) as remote:
            meta = remote.get_metadata(test['image'])
            self._logger.debug('Image metadata\n%s',
                           yaml.dump(meta, default_flow_style=False))

        config.set('lava.job.kernel', meta['kernel'])
        config.set('lava.job.rootfs', meta['rootfs'])
        config.set('lava.job.device', meta['device'])
        config.set('lava.job.compressed', meta['compressed'])

        if len(test['tests']) > 0:
            config.set('lava.job.tests', [])
            for t in test['tests']:
                new = {}
                new['repo'] = t['repository']
                new['name'] = t['name']
                new['revision'] = t['revision']
                new['params'] = t['params']
                config.get('lava.job.tests').append(new)

        job = JobDefinition(config=config, logger=self._logger)

        success = job.submit(wait=not args.no_wait)

        if success:
            self._logger.debug("Job finished successfully")
            sys.exit(0)
        else:
            self._logger.error("Job finished with errors")
            sys.exit(1)

    def __repr__(self):
        return 'Command(submit-job)'

    def __str__(self):
        return 'Command(submit-job)'

    def __unicode__(self):
        return u'Command(submit-job)'
