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
