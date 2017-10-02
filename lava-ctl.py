#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

from pkg_resources import resource_filename

from config import ConfigManager
from commands import submit_job, upload_image, list_images, run_test

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
    if args.conf_params:
        for k, v in [p.split('=') for p in args.conf_params]:
            config.set(k, v)

    return config


if __name__ == '__main__':
    # Print out a bash script to call the docker image for lava-ctl
    if len(sys.argv) == 2 and sys.argv[1] == 'bash':
        with open('bash/lava-ctl', 'r') as f:
            sys.stdout.write(f.read())
            exit(0)

    if len(sys.argv) == 2 and sys.argv[1] == '--version':
        sys.stdout.write(get_version_desc())

    import argparse
    parser = argparse.ArgumentParser()
    sub_cmds = parser.add_subparsers(help='Command Help')

    # Sub-Commands
    commands = [ cmd.Command(logger=logger) for cmd in [submit_job,
        upload_image, list_images, run_test] ]

    for cmd in commands:
        cmd.add_arguments(sub_cmds)

    path_exists = lambda f: f if os.path.exists(f) else parser.error("%s not found" % f)

    # Overwrite configuration parameters
    parser.add_argument('-p', '--param', dest='conf_params', metavar='KEY=VALUE',
                        type=str, action='append', help='set configuration parameter')

    # provide a custom configuration file
    parser.add_argument('-c', '--config', metavar='FILE',
                        type=path_exists, help='specify a custom configuration file')

    # Set log level to DEBUG
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Show debug info')

    # Print the version to the stdout
    parser.add_argument('--version', action='store_true', help='print the lava-ctl version')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Print version and exit
    logger.debug("lava-ctl VERSION %s", get_version_desc())

    # Init configuration
    config = ConfigManager(filename=args.config, logger=logger)

    # Override the configuration with the command-line arguments
    overwrite_configuration_arguments(config, args)

    # Print configuration when debugging
    logger.debug('LAVA-CTL Configuration:\n=== BEGIN CONFIGURATION ===\n%s\n'
                 '=== END CONFIGURATION ===', str(config))

    # Execute the specified command
    args.evaluate(args, config)
