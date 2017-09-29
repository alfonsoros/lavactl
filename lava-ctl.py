#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

from pkg_resources import resource_filename

from config import ConfigManager
from lava.server import LavaServer, FTPStorage
from lava.jobs import JobDefinition
from lava.tests import Test

# Settup basic logging
# TODO: Make lava-ctl to load the logging configuration from the conf file
logging.basicConfig()
logger = logging.getLogger(__name__)


def get_version_desc():
    # Print version and exit
    with open(resource_filename(__name__, 'VERSION'), 'r') as f:
        return f.read()


def overwrite_configuration_arguments(config, args):
    """Gathers all the configuration in a final conf instance.

    The configuration parameters can be overwritten if the proper environment
    variables are found. However, the parameters specified by the command-line
    take precedence over the environment variables and default configuration.

    configuration precedence (highest to lowest):

    1.- command-line arguments
    2.- environment variables
    3.- values in conf/default.yaml

    """

    # Override the command-line parameters
    for k, v in [p.split('=') for p in args.conf_params]:
        config.set(k, v)

    return config

def test_local_image(arguments):
    """Check if a local image is present in the arguments

    :arguments: The command line arguments
    :returns: TODO

    """

    parameters = [
      'kernel',
      'rootfs',
      'device',
    ]

    present = [getattr(arguments, param) is not None for param in parameters]

    if all(present):
        return True
    elif any(present) and not all(present):
        logger.warning("Missing parameters for testing the local image.")
        for (arg, isPresent) in zip(parameters, present):
            if isPresent:
                logger.warning(arg + ": ok")
            else:
                logger.warning(arg + ": missing")
        raise RuntimeError("Some parameters to test a local image are set.")

    return False


if __name__ == '__main__':
    # Print out a bash script to call the docker image for lava-ctl
    if len(sys.argv) == 2 and sys.argv[1] == 'bash':
        with open('bash/lava-ctl', 'r') as f:
            sys.stdout.write(f.read())
            exit(0)

    import argparse
    parser = argparse.ArgumentParser()

    def path_exists(filepath):
        return filepath if os.path.exists(filepath) else parser.error("%s does not exists" % filepath)

    # Overwrite configuration parameters
    parser.add_argument('-p', '--param', dest='conf_params', metavar='KEY=VALUE',
                        type=str, action='append', help='Set configuration parameter')

    # Send LAVA Job description
    parser.add_argument('--from-yaml', metavar='FILE',
                        type=path_exists, help='Submit LAVA Job definition from a file')




    # Submit local files
    parser.add_argument('--device', metavar='DEVICE',
                        type=str, help='Device type (e.g. qemux86)')
    parser.add_argument('--kernel', metavar='FILE',
                        type=path_exists, help='Kernel to be tested')
    parser.add_argument('--rootfs', metavar='FILE',
                        type=path_exists, help='filesystem to be tested')




    # parser.add_argument('--test-repo', dest='test_repos', metavar='URL', action='append',
    # help='git url for test repository')

    parser.add_argument('--test-param', dest='test_params', metavar='KEY=VALUE',
                        action='append', help='Parameter to make available to the tests')

    # provide a custom configuration file
    parser.add_argument('-c', '--config', metavar='FILE',
                        type=path_exists, help='Specify a custom configuration file')

    # Do not wait of the job to finish or timeout
    parser.add_argument('-q', '--dont-wait', action='store_true',
                        help='Exit after job submission')

    # Set log level to DEBUG
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Show debug info')

    # Print the version to the stdout
    parser.add_argument('-v', '--version',
                        action='store_true', help='print version')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Print version and exit
    logger.debug("lava-ctl VERSION %s", get_version_desc())
    if args.version:
        sys.stdout.write(get_version_desc())

    # Init configuration
    config = ConfigManager(filename=args.config, logger=logger)

    # Override the configuration with the command-line arguments
    overwrite_configuration_arguments(config, args)

    # Print configuration when debugging
    logger.debug('LAVA-CTL Configuration:\n=== BEGIN CONFIGURATION ===\n%s\n'
                 '=== END CONFIGURATION ===', str(config))

    job_definition = None

    if test_local_image(args):

        # Upload the files
        with FTPStorage(config=config, logger=logger) as remote:
            url = remote.upload(args.kernel)
            config.set('lava.job.kernel', url)

            url = remote.upload(args.rootfs, compressed=True)
            config.set('lava.job.rootfs', url)
            config.set('lava.job.compressed', True)

            config.set('lava.job.device', args.device)

    # Execute job
    if args.from_yaml:
        try:
            job_definition = JobDefinition(
                filename=args.from_yaml, config=config, logger=logger)
        except Exception, e:
            logger.error(e)
            sys.exit(1)

    # Try to instantiate a LAVA job from the arguments
    else:
        job_definition = JobDefinition(config=config, logger=logger)

    if not job_definition:
        logger.error("Could not instantiate a LAVA Job definition")
        sys.exit(1)

    if args.dont_wait:
        success = job_definition.submit()
    else:
        success = job_definition.submit_and_wait()

    if success:
        logger.debug("Job finished successfully")
        sys.exit(0)
    else:
        logger.error("Job finished with errors")
        sys.exit(1)

    # job = Job(config)
    # if job.valid():
    # job.submit()
    # job.poll()
    # else:
    # logger.error("Can't create a LAVA job from the input")
