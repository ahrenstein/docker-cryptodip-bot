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
import json
import time
import hmac
import hashlib
import requests
from requests.auth import AuthBase


# Create custom authentication for CoinbasePro
# as per https://docs.pro.coinbase.com/?python#creating-a-request
class CoinbaseProAuth(AuthBase):
    """
        Coinbase Pro provided authentication method with minor fixes
        """
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        try:
            message = timestamp + request.method + request.path_url + (request.body or b'').decode()
        except:
            message = timestamp + request.method + request.path_url + (request.body or b'')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest()).decode()

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request


def get_cbpro_creds_from_file(config_file: str) -> [str, str, str]:
    """Open a JSON file and get Coinbase Pro credentials out of it
    Args:
        config_file: Path to the JSON file containing credentials and config options

    Returns:
        cbpro_api_key: An API key for Coinbase Pro
        cbpro_api_secret: An API secret for Coinbase Pro
        cbpro_api_passphrase: An API passphrase for Coinbase Pro
    """
    with open(config_file) as creds_file:
        data = json.load(creds_file)
    cbpro_api_key = data['coinbase']['api_key']
    cbpro_api_secret = data['coinbase']['api_secret']
    cbpro_api_passphrase = data['coinbase']['passphrase']
    return cbpro_api_key, cbpro_api_secret, cbpro_api_passphrase


def get_coin_price(api_url: str, config_file: str, currency: str) -> float:
    """
    Get the USD price of a coin from Coinbase Pro

    Args:
        api_url: The API URL for Coinbase Pro
        config_file: Path to the JSON file containing credentials and config options
        currency: The cryptocurrency the bot is monitoring

    Returns:
        coin_price: The price the coin currently holds in USD
    """
    # Instantiate Coinbase API and query the price
    coinbase_creds = get_cbpro_creds_from_file(config_file)
    coinbase_auth = CoinbaseProAuth(coinbase_creds[0], coinbase_creds[1], coinbase_creds[2])
    api_query = "products/%s-USD/ticker" % currency
    result = requests.get(api_url + api_query, auth=coinbase_auth)
    coin_price = float(result.json()['price'])
    return coin_price


def verify_balance(api_url: str, config_file: str, buy_amount: float) -> bool:
    """Check if enough money exists in the account
    Args:
        api_url: The API URL for Coinbase Pro
        config_file: Path to the JSON file containing credentials and config options
        buy_amount: The amount of $USD the bot plans to spend

    Returns:
        all_clear: A bool that returns true if there is enough money to transact
    """
    # Instantiate Coinbase API and query the price
    coinbase_creds = get_cbpro_creds_from_file(config_file)
    coinbase_auth = CoinbaseProAuth(coinbase_creds[0], coinbase_creds[1], coinbase_creds[2])
    api_query = "accounts"
    result = requests.get(api_url + api_query, auth=coinbase_auth).json()
    try:
        for account in result:
            if account['currency'] == "USD":
                if float(account['balance']) >= buy_amount:
                    return True
    except Exception as err:
        print("ERROR: Unable to current balance!")
        print(err)
        return False
    # Return false by default
    return False


def buy_currency(api_url: str, config_file: str, currency: str, buy_amount: float) -> bool:
    """
    Conduct a trade on Coinbase Pro to trade a currency with USD

    Args:
        api_url: The API URL for Coinbase Pro
        config_file: Path to the JSON file containing credentials and config options
        currency: The cryptocurrency the bot is monitoring
        buy_amount: The amount of $USD the bot plans to spend

    Returns:
        trade_success: A bool that is true if the trade succeeded
    """
    coinbase_creds = get_cbpro_creds_from_file(config_file)
    # Instantiate Coinbase API and query the price
    coinbase_auth = CoinbaseProAuth(coinbase_creds[0], coinbase_creds[1], coinbase_creds[2])
    buy_query = 'orders'
    order_config = json.dumps({'type': 'market', 'funds': buy_amount,
                               'side': 'buy', 'product_id': '%s-USD' % currency})
    buy_result = requests.post(api_url + buy_query, data=order_config, auth=coinbase_auth).json()
    if 'message' in buy_result:
        print("LOG: Buy order failed.")
        print("LOG: Reason: %s" % buy_result['message'])
        return False
    else:
        print("LOG: Buy order succeeded.")
        print("LOG: Buy Results: %s" % json.dumps(buy_result, indent=2))
        return True
