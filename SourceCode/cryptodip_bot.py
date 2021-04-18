#!/usr/bin/env python3
"""A bot that attempts to buy cryptocurrency on the dip."""
#
# Python Script:: cryptodip_bot.py
#
# Linter:: pylint
#
# Copyright 2021, Matthew Ahrenstein, All Rights Reserved.
#
# Maintainers:
# - Matthew Ahrenstein: matt@ahrenstein.com
#
# See LICENSE
#

import argparse
import bot_internals


def main(config_file: str, debug_mode: bool):
    """
    The main function that triggers and runs the bot functions

    Args:
    config_file: Path to the JSON file containing credentials and config options
    debug_mode: Use Sandbox APIs instead of production
    """
    # Load the configuration file
    config_params = bot_internals.read_bot_config(config_file)
    if config_params[5]:
        aws_config = bot_internals.get_aws_creds_from_file(config_file)
        message = "%s-Bot has been started" % config_params[0]
        bot_internals.post_to_sns(aws_config[0], aws_config[1], aws_config[2], message, message)
    # Start the correct cycle
    if config_params[6]:
        print("Gemini support coming")
    else:
        bot_internals.coinbase_pro_cycle(config_params, debug_mode)


if __name__ == '__main__':
    # This function parses and return arguments passed in
    # Assign description to the help doc
    PARSER = argparse.ArgumentParser(
        description='A bot that attempts to buy'
                    ' cryptocurrency on the dip.')
    # Add arguments
    PARSER.add_argument(
        '-c', '--configFile', type=str, help="Path to config.json file", required=True
    )
    PARSER.add_argument(
        '-d', '--debug', help="Use sandbox APIs", required=False, action='store_true'
    )
    # Array for all arguments passed to script
    ARGS = PARSER.parse_args()
    ARG_CONFIG = ARGS.configFile
    ARG_DEBUG = ARGS.debug
    main(ARG_CONFIG, ARG_DEBUG)
