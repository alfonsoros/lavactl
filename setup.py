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
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as version_file:
    version = version_file.read().strip()

setup(
    name='lava-ctl',
    version=version,
    url='https://code.siemens.com/iot/DOPS/lava-ctl',
    author='Alfonso Ros',
    author_email='alfonso.ros-dos-santos@evosoft.com',
    description='LAVA CI setup tool',

    packages=find_packages(),
    include_package_data=True,
    package_data={'': 'lava_ctl/resources/*'},

    data_files=[('', ['VERSION'])],

    install_requires=[
        "zmq",
        "GitPython",
        "Jinja2",
        "paramiko",
        "progress",
        "PyYAML",
    ],

    scripts=['bin/lava-ctl'],
    zip_safe=False
)
