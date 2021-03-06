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

import yaml


class Command(object):
    """ Manage the lavactl configuration """

    def __init__(self, logger=None):
        super(Command, self).__init__()
        self._logger = logger or logging.getLogger(__name__)

    def add_arguments(self, subparsers):
        """Define the arguments of the command"""
        self.parser = subparsers.add_parser(
            'config', help='Manages the lavactl configuration')
        self.parser.add_argument(
            '--set', type=str, metavar="PARAM=VALUE", help='Set a configuration paramerter')
        self.parser.add_argument(
            '--get', type=str, metavar="PARAM", help='Get the value of the parameter')
        self.parser.set_defaults(evaluate=self.evaluate)

    def evaluate(self, args, config):
        """Evaluate if the necessary arguments are present"""

        if args.set:
            config.set(*(args.set.split('=')))
            config.write()
        elif args.get:
            print "%s=%s" % (args.get, config.get(args.get))
        else:
            print config

    def __repr__(self):
        return 'Command(submit-job)'

    def __str__(self):
        return 'Command(submit-job)'

    def __unicode__(self):
        return u'Command(submit-job)'
