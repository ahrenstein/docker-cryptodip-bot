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


import json
import boto3


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
