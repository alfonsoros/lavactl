from pkg_resources import resource_filename

def read_version():
    with open(resource_filename('lava_ctl', 'VERSION')) as version:
        return version.read().strip()

__version__ = read_version()
