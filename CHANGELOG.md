Crypto Dip Buying Bot: Changelog
================================
A list of all the changes made to this repo, and the bot it contains

Version 0.3.0
-------------

1. Shifted TODO versions around to reflect new goals
2. **BREAKING CHANGE** Added Gemini Support
    1. The database name the bot uses is now exchange-currency-"bot", so a new DB will be created when
    using the new version of the bot
3. Fixed a bug where price data would not continue gathering if the bot was not funded
4. Super basic exception catching around DB functions
5. `test-compose.yml` for local debugging/testing is now separate from the production example `docker-compose-yml`

Version 0.2.0
-------------

1. **Fixed a critical issue where the last buy date is not updated when buys are made!**
2. Bot functions condensed in to 1 file
3. Averaging time period and purchase cool down period are now both config variables
4. Fixed some incorrect function descriptions

Version 0.1.0
-------------

1. Initial Pre-release of repository

Return to [README](README.md)
