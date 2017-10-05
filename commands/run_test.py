# -*- coding: utf-8 -*-
import os
import sys
import yaml

from lava.server import FTPStorage
from lava.jobs import Job, JobDefinition
from lava.tests import Test


class Command(object):
    """Run the specified lava tests"""

    def __init__(self, logger=None):
        super(Command, self).__init__()
        self._logger = logger or logging.getLogger(__name__)

    def add_arguments(self, subparsers):
        self.parser = subparsers.add_parser(
            'run-test', help='Run tests on an image')
        self.parser.add_argument(
            '--image', type=str, metavar='IMAGE NAME', help='image to test')
        self.parser.add_argument(
            'yaml_file', type=str, metavar='FILE', help='test description')
        self.parser.add_argument(
            '--no-wait', action='store_true', help='Don\'t wait for job result')
        self.parser.set_defaults(evaluate=self.evaluate)

    def load_remote_meta(self, image_name, config):
        with FTPStorage(config=config, logger=self._logger) as remote:
            meta = remote.get_metadata(image_name)
            self._logger.debug('Image metadata\n%s',
                               yaml.dump(meta, default_flow_style=False))
        return meta

    def check_meta(self, meta):
        REQUIRED = ['device', 'kernel', 'rootfs']
        missing = [p for p in REQUIRED if p not in meta]
        if len(missing) > 0:
            raise RuntimeError('Missing job configuration', missing)

        if meta['rootfs'].endswith('.gz'):
            meta['compressed'] = True

        return meta

    def evaluate(self, args, config):
        """Evaluate if the necessary arguments are present"""

        # Check the file exists
        if not os.path.exists(args.yaml_file):
            raise RuntimeError('File does not exist', args.yaml_file)

        with open(args.yaml_file) as testfile:
            test = yaml.load(testfile.read())

        self._logger.debug("test file content:\n%s",
                           yaml.dump(test, default_flow_style=False))

        if args.image:
            meta = self.check_meta(args.image)

        # is a reference to an image in the FTP server
        elif 'image' in test:
            if isinstance(test['image'], basestring):
                meta = self.load_remote_meta(test['image'], config)
            else:
                meta = self.check_meta(test['image'])

        else:
            meta = self.check_meta(config.get('default_image'))

        job = Job(config=meta, logger=self._logger)

        if 'tests' in test and len(test['tests']) > 0:
            for conf in test['tests']:
                job.add_test(Test(config=conf, logger=self._logger))

        jobdef = JobDefinition(job=job, config=config, logger=self._logger)

        success = jobdef.submit(wait=not args.no_wait)

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
