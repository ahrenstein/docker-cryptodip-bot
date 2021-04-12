#!/usr/bin/env python3
"""Simple math functions"""
#
# Python Script:: bot_math.py
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


def get_average(list_of_numbers: list) -> float:
    """Read all current price records in the database

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
