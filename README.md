Crypto Dip Buying Bot
=====================
This bot is designed to buy cryptocurrency on Coinbase Pro using a USD prefunded portfolio whenever it detects a significant dip in price.

PRE-RELEASE WARNING
-------------------
I tested this code in a sandbox for a few days, before releasing it. I am running this bot against my live Coinbase Pro account as well.
This is still a very new bot with limited testing so **USE THIS BOT AT YOUR OWN RISK!**

Dip Detection
-------------
The bot runs in hourly cycles. Each cycle the bot will check the price of the specified cryptocurrency.
It will then compare the average price of the previous 7 days worth of price history to the configured dip percentage.
If the current price is the configured percentage lower than the price average it will buy the cryptocurrency in the
specified amount of USD.

Running The Bot
---------------
To run the bot you will need Docker and docker-compose installed on your computer.  

    docker-compose up -d

Config File
-----------
You will need the following:

1. Coinbase Pro credentials tied to the portfolio you want to run the bot against
2. Dip logic parameters:
    1. The cryptocurrency you want to transact in. (It must support being paired against USD in Coinbase Pro)
    2. The buy amount you want in $USD.
    3. The average percentage drop from the previous week's worth of intervals you want to consider a buy worthy dip.

The following sections are optional.

1. Time variables in the bot config
   1. Period of days to average (Default: 7)
   2. Cool down period before buying again (Default: 7)
2. AWS credentials:
   1. AWS API keys
   2. SNS topic ARN (us-east-1 only for now)

These settings should be in a configuration file named `config.json` and placed in `./config`.
Additionally, you can override the volume mount to a new path if you prefer.
The file should look like this:

```json
{
  "bot": {
    "currency": "ETH",
    "buy_amount": 75.00,
    "dip_percentage": 10,
     "average_period_days": 3,
     "cool_down_period_days": 5
  },
  "coinbase": {
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "passphrase": "YOUR_API_PASSPHRASE"
  },
   "aws": {
    "access_key": "YOUR_API_KEY",
    "secret_access_key": "YOUR_API_SECRET",
    "sns_arn": "arn:aws:sns:us-east-1:012345678901:dip_alerts"
  }
}
```

Running outside of Docker
-------------------------
You can run the bot outside of Docker pretty easily.

```bash
python SourceCode/cryptodip-bot.py -c /path/to/config.json
```

Logs
----
The bot will log activity to stdout, so you can review it with `docker logs`

Donations
---------
Any and all donations are greatly appreciated.  
I have GitHub Sponsors configured however I happily prefer cryptocurrency:

ETH/ERC20s: ahrenstein.eth (0x288f3d3df1c719176f0f6e5549c2a3928d27d1c1)  
BTC: 3HrVPPwTmPG8LKBt84jbQrVjeqDbM1KyEb
