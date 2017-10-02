# -*- coding: utf-8 -*-
import os
import time

from datetime import datetime
from lava.server import FTPStorage

class Command(object):
    """Uploads an image to the master FTP server"""

    def __init__(self, logger=None):
        super(Command, self).__init__()
        self._logger = logger or logging.getLogger(__name__)

    def add_arguments(self, subparsers):
        self.parser = subparsers.add_parser(
            'upload-image', help='uploads an image to the LAVA FTP server')
        self.parser.add_argument(
            'kernel', type=str, metavar='KERNEL', help='kernel file')
        self.parser.add_argument(
            'rootfs', type=str, metavar='ROOTFS', help='rootfs file')
        self.parser.add_argument(
            '--device', type=str, default='qemux86', help='device type')
        self.parser.add_argument(
            '--prefix', type=str, help='identifier for the image')
        self.parser.set_defaults(evaluate=self.evaluate)

    def evaluate(self, args, config):
        # Check that all the files exist

        # Check the file exists
        for path in [args.kernel, args.rootfs]:
            if not os.path.exists(path):
                raise RuntimeError('File does not exist', path)

        if not args.prefix:
            args.prefix = args.device + datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')

        # Upload the files
        with FTPStorage(config=config, logger=self._logger) as remote:
            remote.upload_image(args.prefix, args.kernel, args.rootfs, device=args.device)

    def __repr__(self):
        return 'Command(upload-image)'

    def __str__(self):
        return 'Command(upload-image)'

    def __unicode__(self):
        return u'Command(upload-image)'
