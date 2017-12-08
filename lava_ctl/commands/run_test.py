# -*- coding: utf-8 -*-
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

import os
import sys
import yaml
import shutil

from lava_ctl.lava.server import FTPStorage
from lava_ctl.lava.jobs import Job, JobDefinition
from lava_ctl.lava.tests import Test


class Command(object):
    """Run the specified lava tests"""

    def __init__(self, logger=None):
        super(Command, self).__init__()
        self._logger = logger or logging.getLogger(__name__)

    def add_arguments(self, subparsers):
        """Define the arguments of the command"""        
        self.parser = subparsers.add_parser(
            'run-test', help='Run tests on an image')
        self.parser.add_argument(
            '--image', type=str, metavar='IMAGE NAME', help='image to test')
        self.parser.add_argument(
            '--repo', type=str, metavar='GIT URL', help='git repo URL')
        self.parser.add_argument(
            '--rev', type=str, metavar='REV HASH', help='commit\'s hash')
        self.parser.add_argument(
            '--branch', type=str, metavar='BRANCH', help='git branch')
        self.parser.add_argument(
            'yaml_file', type=str, metavar='FILE', help='test description')
        self.parser.add_argument(
            '--no-wait', action='store_true', help='Don\'t wait for job result')
        self.parser.set_defaults(evaluate=self.evaluate)

    def load_remote_meta(self, image_name, config):
        """Read meta-information of the image"""    
        with FTPStorage(config=config, logger=self._logger) as remote:
            meta = remote.get_metadata(image_name)
            self._logger.debug('Image metadata\n%s',
                               yaml.dump(meta, default_flow_style=False))
        return meta

    def check_meta(self, meta):
        """Validate image metadata"""
        if 'device' not in meta:
            raise RuntimeError('Missing job configuration', ['device'])

        REQUIRED = ['image', 'patch'] if meta['device']=='iot2000' else ['kernel', 'rootfs']
        missing = [p for p in REQUIRED if p not in meta]
        if len(missing) > 0:
            raise RuntimeError('Missing job configuration', missing)

        if 'rootfs' in meta and meta['rootfs'].endswith('.gz'):
            meta['compressed'] = True

        if meta['device']=='iot2000':
            meta['kernel'] = None
            meta['rootfs'] = None
        else:
            meta['image'] = None
            meta['patch'] = None

        return meta

    def evaluate(self, args, config):
        """Evaluate if the necessary arguments are present"""

        if args.repo:
            repopath = os.path.join(os.curdir, 'test_repo')
            branch = 'master' if not args.branch else args.branch

            import git
            repo = git.Repo.clone_from(args.repo, repopath, branch=branch)

            if args.rev:
                gitcmd = repo.git
                gitcmd.checkout(args.rev)

            args.yaml_file = os.path.join(repopath, args.yaml_file)

        # Check if the file exists
        if not os.path.exists(args.yaml_file):
            raise RuntimeError('File does not exist', args.yaml_file)

        with open(args.yaml_file) as testfile:
            test = yaml.load(testfile.read())

        if args.repo:
            shutil.rmtree(repopath)


        self._logger.debug("test file content:\n%s",
                           yaml.dump(test, default_flow_style=False))

        if args.image:
            meta = self.load_remote_meta(args.image, config)

        #'image' is a reference to an image in the FTP server
        elif 'image' in test:
            if isinstance(test['image'], basestring):
                meta = self.load_remote_meta(test['image'], config)
            else:
                meta = self.check_meta(test['image'])

        else:
            meta = self.check_meta(config.get('default_image'))

        #Create the minimal configuration to run the LAVA job
        job = Job(config=meta, logger=self._logger)

        #Add the test information to the job
        if 'tests' in test and len(test['tests']) > 0:
            for conf in test['tests']:
                job.add_test(Test(config=conf, logger=self._logger))

        #Create a LAVA job definition from the available configuration
        jobdef = JobDefinition(job=job, config=config, logger=self._logger)

        #Submit the job to the LAVA server
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
