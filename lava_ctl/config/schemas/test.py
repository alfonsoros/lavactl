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

FILE_URL_REGEX = '^https:\/\/[\w\-\.]+(:[0-9]+)?(\/[\w\-\.\/\+]*)?$'
GIT_URL_REGEX = '^(https:\/\/|git:\/\/)?[@\w\-\.]+:?([0-9]+)?([\w\-\.\/\+]*)?$'

from lava_ctl.lava.devices import SUPPORTED_DEVICES

def supported_device(field, value, error):
    if not value in SUPPORTED_DEVICES:
        error(field, "Device %s not supported" % value)

boot_from_kernel_and_rootfs = {
    'kernel': {
        'required': True,
        'type': 'string',
        'regex': FILE_URL_REGEX,
    },
    'rootfs': {
        'required': True,
        'type': 'string',
        'regex': FILE_URL_REGEX,
    },
    'rootfs_compressed': {
        'required': False,
        'type': 'boolean'
    },
}

boot_from_wic_image = {
    'url': {
        'required': True,
        'excludes': 'kernel',
        'type': 'string',
        'regex': FILE_URL_REGEX,
    },
    'patch': {
        'ltype': 'dict',
        'schema': {
            'url': {
                'required': True,
                'type': 'string',
                'regex': FILE_URL_REGEX,
            },
            'target': {
                'required': True,
                'type': 'string',
            },
            'partition': {
                'required': True,
                'type': 'integer',
            },
        }
    },
}

TEST_SCHEMA = {
    'device': {
        'required': True,
        'type': 'string',
        'validator': supported_device,
    },
    'image': {
        'type': 'dict',
        'oneof_schema': [
            boot_from_kernel_and_rootfs,
            # boot_from_wic_image,
        ],
    },
    'test_repos': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'url': {
                    'required': True,
                    'type': 'string',
                    'regex': GIT_URL_REGEX,
                },
                'branch': {'type': 'string'},
                'revision': {'type': 'string'},
                'tests': {
                    'required': True,
                    'type': 'list',
                    'schema': {
                      'type': 'string'
                    },
                },
            }
        }
    },
}
