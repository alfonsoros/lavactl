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
import time

from datetime import datetime
from lava_ctl.lava.server import FTPStorage

class Command(object):
    """Uploads an image to the master FTP server"""

    def __init__(self, logger=None):
        super(Command, self).__init__()
        self._logger = logger or logging.getLogger(__name__)

    def add_arguments(self, subparsers):
        """Define the arguments of the command"""
        self.parser = subparsers.add_parser(
            'upload-image', help='uploads an image to the LAVA FTP server')
        self.parser.add_argument(
            '--device', type=str, default='qemux86', help='device type')
        self.parser.add_argument(
            '--kernel', type=str, help='kernel file')
        self.parser.add_argument(
            '--rootfs', type=str, help='rootfs file')
        self.parser.add_argument(
            '--image', type=str, help='image file') 
        self.parser.add_argument(
            '--patch', type=str, help='patch file') 
        self.parser.add_argument(
            '--prefix', type=str, help='identifier for the image')
        self.parser.set_defaults(evaluate=self.evaluate)

    def evaluate(self, args, config):
        # Special behavior for IoT2000 devices
        iot_device = (args.device == 'iot2000')

        # Check if the required arguments are provided
        REQUIRED = ['image', 'patch'] if iot_device else ['kernel', 'rootfs']
        for param in REQUIRED:
            if getattr(args, param) is None:
                self.parser.error('Argument %s is required!'%(param))

        # Check if the required files exist
        for param in REQUIRED:
            path = getattr(args, param)
            if not os.path.exists(path):
                raise RuntimeError('File does not exist', path)

        #Add a default prefix if not specified by the user
        if not args.prefix:
            args.prefix = args.device + datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')

        # Upload the files
        with FTPStorage(config=config, logger=self._logger) as remote:
            if iot_device: 
                remote.upload_image_iot(args.prefix, args.image, args.patch, device=args.device) 
            else:
                remote.upload_image(args.prefix, args.kernel, args.rootfs, device=args.device)

    def __repr__(self):
        return 'Command(upload-image)'

    def __str__(self):
        return 'Command(upload-image)'

    def __unicode__(self):
        return u'Command(upload-image)'
