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

def integer_convertible(field, value, error):
    try:
        int(value)
    except ValueError:
        error(field, "Value must be integer convertible")

LAVACTL_SCHEMA = {
    'default_image': {
        'type': 'dict',
        'schema': {
            'compressed': {'type': 'boolean'},
            'device': {'type': 'string'},
            'kernel': {'type': 'string'},
            'rootfs': {'type': 'string'},
            'image': {'type': 'string', 'nullable': True},
            'patch': {'type': 'string', 'nullable': True},
        }
    },
    'lava': {
        'type': 'dict',
        'schema': {
            'server': {
                'type': 'dict',
                'schema': {
                    'host': {'type': 'string'},
                    'port': {'validator': integer_convertible},
                    'user': {'type': 'string'},
                    'token': {'type': 'string'},
                    'jobs': {
                        'type': 'dict',
                        'schema': {
                            'timeout': {'type': 'number'},
                        },
                    },
                }
            },
            'publisher': {
                'type': 'dict',
                'schema': {
                    'port': {'validator': integer_convertible},
                }
            }
        }
    },
}
