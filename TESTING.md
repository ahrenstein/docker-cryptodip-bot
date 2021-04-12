Crypto Dip Buying Bot: Testing
==============================
I test this bot against Coinbase Pro sandbox first then against my live Coinbase Pro account.

Testing Requirements
--------------------
All modules tested must follow these testing rules:

1. All modules must be tested against an AWS account with all optional variables tested.
2. Changes to modules should be tested to avoid breaking existing infrastructure.
3. Code should pass `pre-commit` checks.

pre-commit
----------
This repo uses Yelp's [pre-commit](https://pre-commit.com/) to manage some pre-commit hooks automatically.  
In order to use the hooks, make sure you have `pre-commit`, and `pylint` in your `$PATH`.  
Once in your path you should run `pre-commit install` in order to configure it. If you push commits that fail pre-commit, your PR will
not be merged.

poetry
------
This project uses [poetry](https://python-poetry.org/) for Python requirements
both for development and building the Docker container.

Python tests
------------
Coming soon ;)

Return to [README](README.md)
