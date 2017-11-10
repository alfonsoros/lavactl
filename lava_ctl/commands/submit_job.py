# -*- coding: utf-8 -*-
"""
Copyright (c) 2017 Evosoft GmbH

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

import sys
import os
import logging

from lava_ctl.lava.jobs import JobDefinition


class Command(object):
    """Submit LAVA job definition command"""

    def __init__(self, logger=None):
        super(Command, self).__init__()
        self._logger = logger or logging.getLogger(__name__)

    def add_arguments(self, subparsers):
		"""Define the arguments of the command"""
        self.parser = subparsers.add_parser(
            'submit-job', help='submit lava job definition')
        self.parser.add_argument(
            'yaml_file', type=str, metavar='FILE', help='LAVA job definition')
        self.parser.add_argument(
            '--no-wait', action='store_true', help='Don\'t wait for job result')
        self.parser.set_defaults(evaluate=self.evaluate)

    def evaluate(self, args, config):
        """Evaluate if the necessary arguments are present"""
        filename = args.yaml_file

        # Check the file exists
        if not os.path.exists(filename):
            raise RuntimeError('File does not exist', filename)

        try:
			#Create a LAVA job definition
            job = JobDefinition(filename=filename,
                                config=config, logger=self._logger)
        except Exception, e:
            self._logger.error(e)
            sys.exit(1)

        if not job:
            self._logger.error("Could not instantiate a LAVA Job definition")
            sys.exit(1)

		#Submit the job to the LAVA server
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
