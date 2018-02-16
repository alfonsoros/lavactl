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
import git
import yaml
import shutil
import logging

from lava_ctl.lava.test import Test


class TestSetsRepo(object):
    """Git Repository containing different tests"""

    DIRECTORY = os.path.join(os.curdir, 'test_repo')

    def __init__(self, config, logger=None):
        super(TestSetsRepo, self).__init__()
        self._logger = logger or logging.getLogger(__name__)
        self._config = config.copy()

    def __enter__(self):
        self._logger.debug('cloning %s to %s', self._config['url'], self.DIRECTORY)
        if 'branch' in self._config:
            self._repo = git.Repo.clone_from(
                self._config['url'], self.DIRECTORY, branch=self._config['branch'])
        else:
            self._repo = git.Repo.clone_from(self._config['url'], self.DIRECTORY)

        if 'revision' in self._config:
            self._repo.head.reset(commit=self._config['revision'])

        test_sets = []
        for filename in self._config['tests']:
            filename = os.path.join(self.DIRECTORY, filename)
            with open(filename, 'r') as testfile:
                test = yaml.load(testfile.read())
                test_sets.append([Test(config=conf, logger=self._logger) for conf in test['tests']])
        return test_sets

    def __exit__(self, type, value, traceback):
        self._logger.debug('removing %s', self._config['url'], self.DIRECTORY)
        shutil.rmtree(self.DIRECTORY)
