# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Siemens AG
# Author: Alfonso Ros Dos Santos
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os
import sys
import yaml
import shutil

from collections import defaultdict

from lava_ctl.lava.jobs import Job, JobDefinition
from lava_ctl.lava.test import Test, TestSetsRepo
from lava_ctl.config.schemas import TEST_SCHEMA
from lava_ctl.config import Config


class Command(object):
    """Run the specified lava tests"""

    def __init__(self, logger=None):
        super(Command, self).__init__()
        self._logger = logger or logging.getLogger(__name__)

    def add_arguments(self, subparsers):
        """Define the arguments of the command"""
        self.parser = subparsers.add_parser(
            'run', help='Run a LAVA test')
        self.parser.add_argument(
            '-p', '--param', type=str, action='append', metavar='KEY=VALUE', help='modify test parameter')
        self.parser.add_argument(
            'yaml_file', type=str, metavar='FILE', help='test description')
        self.parser.add_argument(
            '--no-wait', action='store_true', help='Don\'t wait for the job\'s result')
        self.parser.set_defaults(evaluate=self.evaluate)

    def evaluate(self, args, config):
        """Evaluate if the necessary arguments are present"""
        test_config = Config(schema=TEST_SCHEMA, filename=args.yaml_file,
                             logger=self._logger)

        # Overwride/add config parameters from command line
        self._logger.debug('overriding paramerters: %s', args.param)
        if args.param:
            for param in args.param:
                key, value = param.split('=')
                test_config.set(key, value)

        test_config.validate()
        self._logger.debug('test order configuration: %s', test_config)

        test_results = []

        for repo_ref in test_config.get('test_repos'):
            with TestSetsRepo(repo_ref) as test_sets:
                for test_set in test_sets:

                    # TODO refactor job class
                    conf = defaultdict(lambda: None)
                    conf['device'] = test_config.get('device')
                    conf.update(test_config.get('image'))

                    job = Job(config=conf, logger=self._logger)
                    for test in test_set:
                        job.add_test(test)

                    jobdef = JobDefinition(
                        job=job, config=config, logger=self._logger)

                    # Submit the job to the LAVA server
                    success = jobdef.submit(wait=not args.no_wait)

                    if success:
                        self._logger.debug("Job finished successfully")
                    else:
                        self._logger.error("Job finished with errors")

                    test_results.append(success)

        # finish
        sys.exit(0) if all(test_results) else sys.exit(1)

    def __repr__(self):
        return 'Command(run)'

    def __str__(self):
        return 'Command(run)'

    def __unicode__(self):
        return u'Command(run)'
