#!/usr/bin/env python3
"""Internal functions the bot uses"""
#
# Python Script:: bot_internals.py
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
import json
import datetime
import time
import boto3
import coinbase_pro
import gemini_exchange
import mongo


def read_bot_config(config_file: str) -> [str, float, int, int, int, bool, bool, int, str]:
    """Open a JSON file and get the bot configuration
    Args:
        config_file: Path to the JSON file containing credentials and config options

    Returns:
        crypto_currency: The cryptocurrency that will be monitored
        buy_amount: The price in $USD that will be purchased when a dip is detected
        dip_percentage: The percentage of the average price drop that means a dip occurred
        average_period_days: The time period in days to average across
        cool_down_period_days: The time period in days that you will wait before transacting
        aws_loaded: A bool to determine if AWS configuration options exist
        using_gemini: A bool to determine if the bot should use Gemini
        cycle_time_minutes: The cycle interval in minutes
        bot-name: The name of the bot
    """
    with open(config_file) as creds_file:
        data = json.load(creds_file)
    crypto_currency = data['bot']['currency']
    buy_amount = data['bot']['buy_amount']
    dip_percentage = data['bot']['dip_percentage']
    aws_loaded = bool('aws' in data)
    using_gemini = bool('gemini' in data)
    if 'average_period_days' in data['bot']:
        average_period_days = data['bot']['average_period_days']
    else:
        average_period_days = 7
    if 'cool_down_period_days' in data['bot']:
        cool_down_period_days = data['bot']['cool_down_period_days']
    else:
        cool_down_period_days = 7
    if 'cycle_time_minutes' in data['bot']:
        cycle_time_minutes = data['bot']['cycle_time_minutes']
    else:
        cycle_time_minutes = 60
    if 'name' in data['bot']:
        bot_name = data['bot']['name']
    else:
        if gemini_exchange:
            bot_name = "Gemini-" + crypto_currency + "-bot"
        else:
            bot_name = "CoinbasePro-" + crypto_currency + "-bot"
    return crypto_currency, buy_amount, dip_percentage,\
        average_period_days, cool_down_period_days,\
        aws_loaded, using_gemini, cycle_time_minutes, bot_name


def get_aws_creds_from_file(config_file: str) -> [str, str, str]:
    """Open a JSON file and get AWS credentials out of it
    Args:
        config_file: Path to the JSON file containing credentials

    Returns:
        aws_access_key: The AWS access key your bot will use
        aws_secret_key: The AWS secret access key
        sns_topic_arn: The SNS topic ARN to publish to
    """
    with open(config_file) as creds_file:
        data = json.load(creds_file)
    aws_access_key = data['aws']['access_key']
    aws_secret_key = data['aws']['secret_access_key']
    sns_topic_arn = data['aws']['sns_arn']
    return aws_access_key, aws_secret_key, sns_topic_arn


def post_to_sns(aws_access_key: str, aws_secret_key: str, sns_topic_arn: str,
                message_subject: str, message_body: str):
    """Post a message and subject to AWS SNS

    Args:
    aws_access_key: The AWS access key your bot will use
    aws_secret_key: The AWS secret access key
    sns_topic_arn: The SNS topic ARN to publish to
    message_subject: A message subject to post to SNS
    message_body: A message body to post to SNS
    """
    sns = boto3.client('sns', region_name="us-east-1",
                       aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    sns.publish(TopicArn=sns_topic_arn, Subject=message_subject, Message=message_body)


def get_average(list_of_numbers: list) -> float:
    """Get an average of the numbers in a list

    Args:
    list_of_numbers: A list of floats

    Returns:
    list_average: A float containing the list average
    """
    sum_of_numbers = 0
    for number in list_of_numbers:
        sum_of_numbers = sum_of_numbers + number
    list_average = sum_of_numbers / len(list_of_numbers)
    return round(list_average, 2)


def dip_percent_value(price: float, percent: float) -> float:
    """Return the value of the current price if it dips a certain percent

    Args:
    price: The price to check a dip percentage against
    percent: the dip percentage we care about

    Returns:
    dip_price: A float containing the price if we hit our dip target
    """
    dip_price = price * (1 - percent / 100)
    return round(dip_price, 2)


def gemini_exchange_cycle(config_file: str, debug_mode: bool) -> None:
    """Perform bot cycles using Gemini as the exchange

        Args:
        config_file: Path to the JSON file containing credentials
        debug_mode: Are we running in debugging mode?
        """
    # Load the configuration file
    config_params = read_bot_config(config_file)
    if config_params[5]:
        aws_config = get_aws_creds_from_file(config_file)
        message = "%s has been started" % config_params[8]
        post_to_sns(aws_config[0], aws_config[1], aws_config[2], message, message)
    # Set API URLs
    if debug_mode:
        gemini_exchange_api_url = "https://api.sandbox.gemini.com"
        mongo_db_connection = "mongodb://bots:buythedip@bots-db:27017/"
    else:
        gemini_exchange_api_url = "https://api.gemini.com"
        mongo_db_connection = "mongodb://bots:buythedip@bots-db:27017/"
    print("LOG: Starting bot...\nLOG: Monitoring %s on Gemini to buy $%s worth"
          " when a %s%% dip occurs." % (config_params[0], config_params[1], config_params[2]))
    print("LOG: Dips are checked against a %s day price"
          " average with a %s day cool down period" % (config_params[3], config_params[4]))
    for cycle in count():
        now = datetime.datetime.now().strftime("%m/%d/%Y-%H:%M:%S")
        print("LOG: Cycle %s: %s" % (cycle, now))
        coin_current_price = gemini_exchange.get_coin_price(
            gemini_exchange_api_url, config_params[0])
        if coin_current_price == -1:
            message = "ERROR: Coin price invalid. This could be an API issue. Ending cycle"
            print(message)
            subject = "Gemini-%s-Coin price invalid" % config_params[0]
            if config_params[5]:
                post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                            subject, message)
            time.sleep(config_params[7] * 60)
            continue
        # Add the current price to the price database
        mongo.add_price(config_params[8], mongo_db_connection, coin_current_price)
        # Verify that there is enough money to transact, otherwise don't bother
        if not gemini_exchange.verify_balance(gemini_exchange_api_url,
                                              config_file, config_params[1]):
            message = "LOG: Not enough account balance" \
                      " to buy $%s worth of %s" % (config_params[1], config_params[0])
            subject = "%s Funding Issue" % config_params[8]
            if config_params[5]:
                post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                            subject, message)
            print("LOG: %s" % message)
            # Sleep for the specified cycle interval then end the cycle
            time.sleep(config_params[7] * 60)
            continue
        # Check if the a week has passed since the last dip buy
        clear_to_proceed = mongo.check_last_buy_date(config_params[8], mongo_db_connection,
                                                     config_params[4])
        if clear_to_proceed is True:
            print("LOG: Last buy date outside cool down period. Checking if a dip is occurring.")
            average_price = mongo.average_pricing(config_params[8], mongo_db_connection,
                                                  config_params[3])
            dip_price = dip_percent_value(average_price, config_params[2])
            print("LOG: A %s%% dip at the average price of %s would be %s"
                  % (config_params[2], average_price, dip_price))
            if coin_current_price <= dip_price:
                print("LOG: The current price of %s is <= %s. We are in a dip!"
                      % (coin_current_price, dip_price))
                did_buy = gemini_exchange.buy_currency(gemini_exchange_api_url,
                                                       config_file,
                                                       config_params[0], config_params[1])
                message = "Buy success status is %s for %s worth of %s" \
                          % (did_buy, config_params[1], config_params[0])
                subject = "%s Buy Status Alert" % config_params[8]
                mongo.set_last_buy_date(config_params[8], mongo_db_connection)
                print("LOG: %s" % message)
                if config_params[5]:
                    post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                                subject, message)
            else:
                print("LOG: The current price of %s is > %s. We are not in a dip!"
                      % (coin_current_price, dip_price))
        else:
            print("LOG: Last buy date inside cool down period. No buys will be attempted.")

        # Run a price history cleanup daily otherwise sleep the interval
        if (cycle * config_params[7]) % 1440 == 0:
            print("LOG: Cleaning up price history older than 30 days.")
            mongo.cleanup_old_records(config_params[8], mongo_db_connection)
        else:
            # Sleep for the specified cycle interval
            time.sleep(config_params[7] * 60)


def coinbase_pro_cycle(config_file: str, debug_mode: bool) -> None:
    """Perform bot cycles using Coinbase Pro as the exchange

        Args:
        config_file: Path to the JSON file containing credentials
        debug_mode: Are we running in debugging mode?
        """
    # Load the configuration file
    config_params = read_bot_config(config_file)
    if config_params[5]:
        aws_config = get_aws_creds_from_file(config_file)
        message = "%s has been started" % config_params[8]
        post_to_sns(aws_config[0], aws_config[1], aws_config[2], message, message)
    # Set API URLs
    if debug_mode:
        coinbase_pro_api_url = "https://api-public.sandbox.pro.coinbase.com/"
        mongo_db_connection = "mongodb://bots:buythedip@bots-db:27017/"
    else:
        coinbase_pro_api_url = "https://api.pro.coinbase.com/"
        mongo_db_connection = "mongodb://bots:buythedip@bots-db:27017/"
    print("LOG: Starting bot...\nLOG: Monitoring %s on Coinbase Pro to buy $%s worth"
          " when a %s%% dip occurs." % (config_params[0], config_params[1], config_params[2]))
    print("LOG: Dips are checked against a %s day price"
          " average with a %s day cool down period" % (config_params[3], config_params[4]))
    for cycle in count():
        now = datetime.datetime.now().strftime("%m/%d/%Y-%H:%M:%S")
        print("LOG: Cycle %s: %s" % (cycle, now))
        coin_current_price = coinbase_pro.get_coin_price\
            (coinbase_pro_api_url, config_file, config_params[0])
        # Add the current price to the price database
        mongo.add_price(config_params[8], mongo_db_connection, coin_current_price)
        # Verify that there is enough money to transact, otherwise don't bother
        if not coinbase_pro.verify_balance(coinbase_pro_api_url, config_file, config_params[1]):
            message = "LOG: Not enough account balance" \
                      " to buy $%s worth of %s" % (config_params[1], config_params[0])
            subject = "%s Funding Issue" % config_params[8]
            if config_params[5]:
                post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                            subject, message)
            print("LOG: %s" % message)
            # Sleep for the specified cycle interval then end the cycle
            time.sleep(config_params[7] * 60)
            continue
        # Check if the a week has passed since the last dip buy
        clear_to_proceed = mongo.check_last_buy_date(config_params[8], mongo_db_connection,
                                                     config_params[4])
        if clear_to_proceed is True:
            print("LOG: Last buy date outside cool down period. Checking if a dip is occurring.")
            average_price = mongo.average_pricing(config_params[8], mongo_db_connection,
                                                  config_params[3])
            dip_price = dip_percent_value(average_price, config_params[2])
            print("LOG: A %s%% dip at the average price of %s would be %s"
                  %(config_params[2], average_price, dip_price))
            if coin_current_price <= dip_price:
                print("LOG: The current price of %s is <= %s. We are in a dip!"
                      % (coin_current_price, dip_price))
                did_buy = coinbase_pro.buy_currency(coinbase_pro_api_url,
                                                    config_file, config_params[0], config_params[1])
                message = "Buy success status is %s for %s worth of %s"\
                          % (did_buy, config_params[1], config_params[0])
                subject = "%s Buy Status Alert" % config_params[8]
                mongo.set_last_buy_date(config_params[8], mongo_db_connection)
                print("LOG: %s" % message)
                if config_params[5]:
                    post_to_sns(aws_config[0], aws_config[1], aws_config[2],
                                subject, message)
            else:
                print("LOG: The current price of %s is > %s. We are not in a dip!"
                      % (coin_current_price, dip_price))
        else:
            print("LOG: Last buy date inside cool down period. No buys will be attempted.")

        # Run a price history cleanup daily otherwise sleep the interval
        if (cycle * config_params[7]) % 1440 == 0:
            print("LOG: Cleaning up price history older than 30 days.")
            mongo.cleanup_old_records(config_params[8], mongo_db_connection)
        else:
            # Sleep for the specified cycle interval
            time.sleep(config_params[7] * 60)
