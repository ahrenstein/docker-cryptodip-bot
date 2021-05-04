#!/usr/bin/env python3
"""Functions to use with the Gemini Exchange"""
#
# Python Script:: gemini_exchange.py
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

import base64
import datetime
import json
import time
import hmac
import hashlib
import requests


# Create custom api call for Gemini
# as per https://docs.gemini.com/rest-api/#private-api-invocation
def gemini_api_call(api_url: str, gemini_api_key: str,
                    gemini_api_secret: str, api_query: str) -> dict:
    """Make a post to the Gemini Exchange API
    Args:
    api_url: The API URL for the Gemini Exchange
    gemini_api_key: An API key for Gemini Exhcange
    gemini_api_secret: An API secret for Gemini Exhcange
    api_query: The query to be posted to the API

    Returns:
    api_response: The API response
    """
    full_query_url = api_url + api_query

    # Using POSIX timestamps in UTC tp avoid repeating nonce issues.
    # This avoids the bad design of the API reference sample code
    current_time = datetime.datetime.now(datetime.timezone.utc)
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)  # use POSIX epoch
    posix_timestamp_micros = (current_time - epoch) // datetime.timedelta(microseconds=1)
    payload_nonce = str(posix_timestamp_micros)

    payload = {"request": api_query, "nonce": payload_nonce}
    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(gemini_api_secret.encode(), b64, hashlib.sha384).hexdigest()

    request_headers = {
        'Content-Type': "text/plain",
        'Content-Length': "0",
        'X-GEMINI-APIKEY': gemini_api_key,
        'X-GEMINI-PAYLOAD': b64,
        'X-GEMINI-SIGNATURE': signature,
        'Cache-Control': "no-cache"
    }

    response = requests.post(full_query_url, headers=request_headers)
    return response.json()


def get_gemini_creds_from_file(config_file: str) -> [str, str]:
    """Open a JSON file and get Gemini credentials out of it
    Args:
    config_file: Path to the JSON file containing credentials and config options

    Returns:
    gemini_api_key: An API key for Gemini Exhcange
    gemini_api_secret: An API secret for Gemini Exhcange
    """
    with open(config_file) as creds_file:
        data = json.load(creds_file)
    gemini_api_key = data['gemini']['api_key']
    gemini_api_secret = data['gemini']['api_secret']
    return gemini_api_key, gemini_api_secret


def get_coin_price(api_url: str, currency: str) -> float:
    """
    Get the USD price of a coin from Gemini

    Args:
    api_url: The API URL for Gemini
    currency: The cryptocurrency the bot is monitoring

    Returns:
    coin_price: The price the coin currently holds in USD
    """
    # Instantiate Gemini and query the price
    coin_price = -1
    api_query = "/v1/pricefeed"
    price_feeds = requests.get(api_url + api_query).json()
    try:
        for feed in price_feeds:
            if feed.get('pair') == currency + "USD":
                coin_price = float(feed.get('price'))
    except Exception as err:
        print("ERROR: Unable to get price due to %s" % err)
        print("Price feed: %s" % price_feeds)
    return coin_price


def verify_balance(api_url: str, config_file: str, buy_amount: float) -> bool:
    """Check if enough money exists in the account
    Args:
    api_url: The API URL for Gemini
    config_file: Path to the JSON file containing credentials and config options
    buy_amount: The amount of $USD the bot plans to spend

    Returns:
    all_clear: A bool that returns true if there is enough money to transact
    """
    # Instantiate Gemini and query the price
    gemini_creds = get_gemini_creds_from_file(config_file)
    api_query = "/v1/balances"
    result = gemini_api_call(api_url, gemini_creds[0], gemini_creds[1], api_query)
    try:
        for account in result:
            if account.get('currency') == "USD":
                balance = float(account.get('amount'))
                if balance >= buy_amount:
                    return True
    except Exception as err:
        print("ERROR: Unable to get current balance!")
        print(err)
        return False
    # Return false by default
    return False


def get_decimal_max(api_url: str, currency: str) -> int:
    """Get the maximum amount of decimals permitted for a currency

    Args:
    api_url: The API URL for the Gemini Exchange
    currency: The cryptocurrency the bot is monitoring

    Returns:
    tick_size: An integer of decimal places permitted
    """
    # Instantiate Gemini and query the price
    api_query = "/v1/symbols/details/%s" % (currency + "usd").lower()
    symbol_details = requests.get(api_url + api_query).json()
    tick_size = str(symbol_details.get('tick_size'))[3:]
    return int(tick_size)


def buy_currency(api_url: str, config_file: str,
                 currency: str, buy_amount: float) -> bool:
    """Conduct a trade on Gemini to trade a currency with USD
    Args:
    api_url: The API URL for the Gemini Exchange
    config_file: Path to the JSON file containing credentials and config options
    currency: The cryptocurrency the bot is monitoring
    buy_amount: The amount of $USD the bot plans to spend

    Returns:
    api_response: The API response
    """
    # Gemini's API doesn't support market orders in an effort to protect you from yourself
    # So we just do a limit order at the current price multipled by 1.2
    coin_current_price = get_coin_price(api_url, currency)
    # Gemini also denominates purchases in the coin amount not USD so we have to do math
    tick_size = get_decimal_max(api_url, currency)
    coin_amount = round(buy_amount / coin_current_price, tick_size)
    market_price_fix = round(coin_current_price * 1.2, 2)

    # Instantiate Gemini and query the price
    gemini_creds = get_gemini_creds_from_file(config_file)
    full_query_url = api_url + "/v1/order/new"

    # Using POSIX timestamps in UTC tp avoid repeating nonce issues.
    # This avoids the bad design of the API reference sample code
    current_time = datetime.datetime.now(datetime.timezone.utc)
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)  # use POSIX epoch
    posix_timestamp_micros = (current_time - epoch) // datetime.timedelta(microseconds=1)
    payload_nonce = str(posix_timestamp_micros)
    payload = {
        "request": "/v1/order/new",
        "nonce": payload_nonce,
        "symbol": currency + "usd",
        "amount": str(coin_amount),
        "price": str(market_price_fix),
        "side": "buy",
        "type": "exchange limit",
        "options": ["immediate-or-cancel"]

    }

    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(gemini_creds[1].encode(), b64, hashlib.sha384).hexdigest()

    request_headers = {
        'Content-Type': "text/plain",
        'Content-Length': "0",
        'X-GEMINI-APIKEY': gemini_creds[0],
        'X-GEMINI-PAYLOAD': b64,
        'X-GEMINI-SIGNATURE': signature,
        'Cache-Control': "no-cache"
    }

    response = requests.post(full_query_url, data=None, headers=request_headers)
    order_result = response.json()
    if 'executed_amount' in order_result.keys():
        print("LOG: Buy order succeeded.")
        print("LOG: Buy Results: %s" % json.dumps(order_result, indent=2))
        return True
    else:
        print("LOG: Buy order failed.")
        print("LOG: Reason: %s" % json.dumps(order_result, indent=2))
        return False
