#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

from pkg_resources import resource_filename

from config import ConfigManager
from lava.jobs import Job, JobDefinition
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
                        type=path_exists, help='LAVA Job YAML definition')


    parser.add_argument('--test-repo', dest='test_repos', metavar='URL', action='append',
                        help='git url for test repository')

    parser.add_argument('--test-param', dest='test_params', metavar='KEY=VALUE',
                        action='append', help='parameter to make available to the tests')

    # provide a custom configuration file
    parser.add_argument('-c', '--config', metavar='FILE',
                        type=path_exists, help='config file')

    # Set log level to DEBUG
    parser.add_argument('-d', '--debug', action='store_true', help='show debug info')

    # Print the version to the stdout
    parser.add_argument('-v', '--version', action='store_true', help='print version')

    parser.add_argument('--no-progress-bars',
                        action='store_true', help='skip progress bars.')

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

    # TODO: configure the logging as well
    # config.add_section('logging')
    # config.set('logging', 'progress-bars', str(not args.no_progress_bars))

    # Test provided image
    if args.kernel or args.rootfs:
        if args.kernel and args.rootfs and args.kernel != args.rootfs:
            config.add_section('lava.files')
            config.set('lava.files', 'kernel', args.kernel)
            config.set('lava.files', 'rootfs', args.rootfs)
        else:
            logger.error('--kernel and --rootfs must be specified together')
            exit(1)

    # Lava tests
    if args.test_repos:
        config.add_section('lava.test')

        if args.test_params:
            config.set('lava.test', 'repos', [
                       Test(repo, args.test_params) for repo in args.test_repos])
        else:
            config.set('lava.test', 'repos', [
                       Test(repo) for repo in args.test_repos])

    # Print configuration when debugging
    logger.debug('LAVA-CTL Configuration:\n=== BEGIN CONFIGURATION ===\n%s\n'
                 '=== END CONFIGURATION ===', str(config))

    # Execute job
    if args.from_yaml:
        logger.debug("Reading YAML job definition")
        JobDefinition(filename=args.from_yaml)
        sys.exit(0)

    sys.exit(0)

    job = Job(config)
    if job.valid():
        job.submit()
        job.poll()
    else:
        logger.error("Can't create a LAVA job from the input")
