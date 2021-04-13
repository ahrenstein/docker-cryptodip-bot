#!/usr/bin/env python3
"""Functions to use with MongoDB"""
#
# Python Script:: mongo.py
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

import datetime
import pymongo
import bot_internals

# Constants that might be useful to adjust for debugging purposes
PURGE_OLDER_THAN_DAYS = 30


def add_price(db_server: str, currency: str, current_price: float):
    """Add a current price record to the database

    Args:
    db_server: The MongoDB server to connect to
    currency: The cryptocurrency the bot is monitoring
    current_price: The current price of the currency
    """
    timestamp = datetime.datetime.utcnow()
    # Create a Mongo client to connect to
    mongo_client = pymongo.MongoClient(db_server)
    bot_db = mongo_client["%s-bot" % currency]
    prices_collection = bot_db["prices"]
    record = {"time": timestamp, "price": current_price}
    try:
        prices_collection.insert_one(record)
    except Exception as err:
        print("Error creating price record: %s" % err)


def read_all_prices(db_server: str, currency: str):
    """Read all current price records in the database

    Args:
    db_server: The MongoDB server to connect to
    currency: The cryptocurrency the bot is monitoring
    """
    # Create a Mongo client to connect to
    mongo_client = pymongo.MongoClient(db_server)
    bot_db = mongo_client["%s-bot" % currency]
    prices_collection = bot_db["prices"]
    records = prices_collection.find()
    for record in records:
        print(record)


def average_pricing(db_server: str, currency: str, average_period: int) -> float:
    """Check the last week of prices and return the average

        Args:
        db_server: The MongoDB server to connect to
        currency: The cryptocurrency the bot is monitoring
        average_period: The time period in days to average across

        Returns:
        average_price: The average price of the last week
        """
    price_history = []
    # Create a Mongo client to connect to
    mongo_client = pymongo.MongoClient(db_server)
    bot_db = mongo_client["%s-bot" % currency]
    prices_collection = bot_db["prices"]
    records = prices_collection.find({})
    for record in records:
        record_age = datetime.datetime.utcnow() - record['time']
        if record_age.days <= average_period:
            price_history.append(record['price'])
    average_price = bot_internals.get_average(price_history)
    return average_price


def cleanup_old_records(db_server: str, currency: str):
    """Remove all price history older than X days

    Args:
    db_server: The MongoDB server to connect to
    currency: The cryptocurrency the bot is monitoring
    """
    # Create a Mongo client to connect to
    mongo_client = pymongo.MongoClient(db_server)
    bot_db = mongo_client["%s-bot" % currency]
    prices_collection = bot_db["prices"]
    records = prices_collection.find()
    for record in records:
        record_age = datetime.datetime.utcnow() - record['time']
        if record_age.days >= PURGE_OLDER_THAN_DAYS:
            prices_collection.delete_one({"_id": record['_id']})


def set_last_buy_date(db_server: str, currency: str):
    """Sets the date the last time the currency was bought

    Args:
    db_server: The MongoDB server to connect to
    currency: The cryptocurrency the bot is monitoring
    """
    timestamp = datetime.datetime.utcnow()
    # Create a Mongo client to connect to
    mongo_client = pymongo.MongoClient(db_server)
    bot_db = mongo_client["%s-bot" % currency]
    buy_date = bot_db["buy-date"]
    try:
        buy_date.find_one_and_update({"_id": 1},
                                     {"$set": {"time": timestamp}}, upsert=True)
    except Exception as err:
        print("Error updating buy date record: %s" % err)


def check_last_buy_date(db_server: str, currency: str, cool_down_period: int) -> bool:
    """Get the date of the last time the currency was bought
    and returns true if it >= cool down period

    Args:
    db_server: The MongoDB server to connect to
    currency: The cryptocurrency the bot is monitoring
    cool_down_period: The time period in days that you will wait before transacting

    Returns:
    clear_to_buy: A bool that is true if we are clear to buy
    """
    # Create a Mongo client to connect to
    mongo_client = pymongo.MongoClient(db_server)
    bot_db = mongo_client["%s-bot" % currency]
    buy_date = bot_db["buy-date"]
    # Create an initial record if the record doesn't exist yet
    if buy_date.find({'_id': 1}).count() == 0:
        print("Initializing new last buy date")
        timestamp = datetime.datetime.utcnow()
        buy_date.find_one_and_update({"_id": 1},
                                     {"$set": {"time": timestamp}}, upsert=True)
        return False
    try:
        last_buy_date = buy_date.find_one({"_id": 1})['time']
    except Exception as err:
        print("Error getting buy date record: %s" % err)
        return False
    time_difference = datetime.datetime.utcnow() - last_buy_date
    return time_difference.days >= cool_down_period
