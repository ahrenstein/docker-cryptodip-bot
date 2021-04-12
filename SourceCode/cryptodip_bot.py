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

from itertools import count
import argparse
import datetime
import json
import time
import bot_alerts
import bot_math
import coinbase_pro
import mongo

# Constants that might be useful to adjust for debugging purposes
CYCLE_INTERVAL_MINUTES = 60


def read_bot_config(config_file: str) -> [str, float, int, bool]:
    """Open a JSON file and get the bot configuration
    Args:
        config_file: Path to the JSON file containing credentials and config options

    Returns:
        crypto_currency: The cryptocurrency that will be monitored
        buy_amount: The price in $USD that will be purchased when a dip is detected
        dip_percentage: The percentage of the average price drop that means a dip occurred
        aws_loaded: A bool to determine if AWS configuration options exist
    """
    with open(config_file) as creds_file:
        data = json.load(creds_file)
    crypto_currency = data['bot']['currency']
    buy_amount = data['bot']['buy_amount']
    dip_percentage = data['bot']['dip_percentage']
    aws_loaded = bool('aws' in data)
    return crypto_currency, buy_amount, dip_percentage, aws_loaded


def main(config_file: str, debug_mode: bool):
    """
    The main function that triggers and runs the bot functions

    Args:
    config_file: Path to the JSON file containing credentials and config options
    debug_mode: Use Sandbox APIs instead of production
    """
    # Load the configuration file
    config_params = read_bot_config(config_file)
    if config_params[3]:
        aws_config = bot_alerts.get_aws_creds_from_file(config_file)
        message = "%s-Bot has been started" % config_params[0]
        bot_alerts.post_to_sns(aws_config[0], aws_config[1], aws_config[2], message, message)
    # Set API URLs
    coinbase_pro_api_url = ""
    mongo_db_connection = ""
    if debug_mode:
        coinbase_pro_api_url = "https://api-public.sandbox.pro.coinbase.com/"
        mongo_db_connection = "mongodb://bots:buythedip@bots-db:27017/"
    else:
        coinbase_pro_api_url = "https://api.pro.coinbase.com/"
        mongo_db_connection = "mongodb://bots:buythedip@bots-db:27017/"
    print("LOG: Starting bot...")
    print("LOG: Monitoring %s to buy $%s worth when a %s%% dip occurs."
          % (config_params[0], config_params[1], config_params[2]))
    # Execute the bot every 10 seconds
    for cycle in count():
        now = datetime.datetime.now().strftime("%m/%d/%Y-%H:%M:%S")
        print("LOG: Cycle %s: %s" % (cycle, now))
        # Verify that there is enough money to transact, otherwise don't bother
        if not coinbase_pro.verify_balance(coinbase_pro_api_url, config_file, config_params[1]):
            message = "LOG: Not enough account balance" \
                      " to buy $%s worth of %s" % (config_params[1], config_params[0])
            subject = "%s-Bot Funding Issue" % config_params[0]
            if config_params[3]:
                bot_alerts.post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                                       subject, message)
            print("LOG: %s" % message)
            # Sleep for the specified cycle interval then end the cycle
            time.sleep(CYCLE_INTERVAL_MINUTES * 60)
            continue
        coin_current_price = coinbase_pro.get_coin_price\
            (coinbase_pro_api_url, config_file, config_params[0])
        # Add the current price to the price database
        mongo.add_price(mongo_db_connection, config_params[0], coin_current_price)
        # Check if the a week has passed since the last dip buy
        clear_to_proceed = mongo.check_last_buy_date(mongo_db_connection, config_params[0])
        if clear_to_proceed is True:
            print("LOG: Last buy date over a week ago. Checking if a dip is occurring.")
            average_price = mongo.average_pricing(mongo_db_connection, config_params[0])
            dip_price = bot_math.dip_percent_value(average_price, config_params[2])
            print("LOG: A %s%% dip at the average price of %s would be %s"
                  %(config_params[2], average_price, dip_price))
            if coin_current_price <= dip_price:
                print("LOG: The current price of %s is <= %s. We are in a dip!"
                      % (coin_current_price, dip_price))
                did_buy = coinbase_pro.buy_currency(coinbase_pro_api_url,
                                                    config_file, config_params[0], config_params[1])
                message = "Buy success status is %s for %s worth of %s"\
                          % (did_buy, config_params[1], config_params[0])
                subject = "%s-Bot Buy Status Alert" % config_params[0]
                print("LOG: %s" % message)
                if config_params[3]:
                    bot_alerts.post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                                           subject, message)
            else:
                print("LOG: The current price of %s  is > %s. We are not in a dip!"
                      % (coin_current_price, dip_price))
        else:
            print("LOG: Last buy date under a week ago. No buys will be attempted.")

        # Run a price history cleanup daily otherwise sleep the interval
        if (cycle * CYCLE_INTERVAL_MINUTES) % 1440 == 0:
            print("LOG: Cleaning up price history older than 30 days.")
            mongo.cleanup_old_records(mongo_db_connection, config_params[0])
        else:
            # Sleep for the specified cycle interval
            time.sleep(CYCLE_INTERVAL_MINUTES * 60)


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
