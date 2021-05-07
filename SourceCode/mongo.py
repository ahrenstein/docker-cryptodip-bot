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


def add_price(bot_name: str, db_server: str, current_price: float):
    """Add a current price record to the database

    Args:
    bot_name: The name of the bot
    db_server: The MongoDB server to connect to
    current_price: The current price of the currency
    """
    timestamp = datetime.datetime.utcnow()
    try:
        # Create a Mongo client to connect to
        mongo_client = pymongo.MongoClient(db_server)
        bot_db = mongo_client[bot_name]
        prices_collection = bot_db["prices"]
        record = {"time": timestamp, "price": current_price}
        prices_collection.insert_one(record)
    except Exception as err:
        print("Error creating price record: %s" % err)


def read_all_prices(bot_name: str, db_server: str):
    """Read all current price records in the database

    Args:
    bot_name: The name of the bot
    db_server: The MongoDB server to connect to
    """
    try:
        # Create a Mongo client to connect to
        mongo_client = pymongo.MongoClient(db_server)
        bot_db = mongo_client[bot_name]
        prices_collection = bot_db["prices"]
        records = prices_collection.find()
    except Exception as err:
        print("Error reading price records: %s" % err)
    for record in records:
        print(record)


def average_pricing(bot_name: str, db_server: str, average_period: int) -> float:
    """Check the last week of prices and return the average

        Args:
        bot_name: The name of the bot
        db_server: The MongoDB server to connect to
        average_period: The time period in days to average across

        Returns:
        average_price: The average price of the last week
        """
    price_history = []
    try:
        # Create a Mongo client to connect to
        mongo_client = pymongo.MongoClient(db_server)
        bot_db = mongo_client[bot_name]
        prices_collection = bot_db["prices"]
        records = prices_collection.find({})
    except Exception as err:
        print("Error reading price records for averaging: %s" % err)
    for record in records:
        record_age = datetime.datetime.utcnow() - record['time']
        if record_age.days <= average_period:
            price_history.append(record['price'])
    average_price = bot_internals.get_average(price_history)
    return average_price


def cleanup_old_records(bot_name: str, db_server: str):
    """Remove all price history older than X days

    Args:
    bot_name: The name of the bot
    db_server: The MongoDB server to connect to
    """
    try:
        # Create a Mongo client to connect to
        mongo_client = pymongo.MongoClient(db_server)
        bot_db = mongo_client[bot_name]
        prices_collection = bot_db["prices"]
        records = prices_collection.find()
    except Exception as err:
        print("Error cleaning up old price records: %s" % err)
    for record in records:
        record_age = datetime.datetime.utcnow() - record['time']
        if record_age.days >= PURGE_OLDER_THAN_DAYS:
            prices_collection.delete_one({"_id": record['_id']})


def set_last_buy_date(bot_name: str, db_server: str):
    """Sets the date the last time the currency was bought

    Args:
    bot_name: The name of the bot
    db_server: The MongoDB server to connect to
    """
    timestamp = datetime.datetime.utcnow()
    try:
        # Create a Mongo client to connect to
        mongo_client = pymongo.MongoClient(db_server)
        bot_db = mongo_client[bot_name]
        buy_date = bot_db["buy-date"]
    except Exception as err:
        print("Error connecting to buy-date collection: %s" % err)
    try:
        buy_date.find_one_and_update({"_id": 1},
                                     {"$set": {"time": timestamp}}, upsert=True)
    except Exception as err:
        print("Error updating buy date record: %s" % err)


def check_last_buy_date(bot_name: str, db_server: str,
                        cool_down_period: int) -> bool:
    """Get the date of the last time the currency was bought
    and returns true if it >= cool down period

    Args:
    bot_name: The name of the bot
    db_server: The MongoDB server to connect to
    cool_down_period: The time period in days that you will wait before transacting

    Returns:
    clear_to_buy: A bool that is true if we are clear to buy
    """
    try:
        # Create a Mongo client to connect to
        mongo_client = pymongo.MongoClient(db_server)
        bot_db = mongo_client[bot_name]
        buy_date = bot_db["buy-date"]
    except Exception as err:
        print("Error connecting to buy-date collection: %s" % err)
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
