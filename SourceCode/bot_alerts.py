#!/usr/bin/env python3
"""Alerting Functions"""
#
# Python Script:: bot_alerts.py
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
    """Read all current price records in the database

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
