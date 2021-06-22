Crypto Dip Buying Bot: Testing
==============================
I test this bot against Coinbase Pro sandbox first then against my live Coinbase Pro account.

Testing Requirements
--------------------
All code tested must follow these testing rules:

1. All code must be tested against the exchanges it supports with all optional variables tested.
2. Changes to code should be tested to avoid breaking existing infrastructure.
3. Code should pass `pre-commit` checks.

pre-commit
----------
This repo uses Yelp's [pre-commit](https://pre-commit.com/) to manage some pre-commit hooks automatically.  
In order to use the hooks, make sure you have `pre-commit`, and `pylint` in your `$PATH`.  
Once in your path you should run `pre-commit install` in order to configure it. If you push commits that fail pre-commit, your PR will
not be merged.

Local Docker
------------
You can run Docker using locally built containers via

    docker-compose -f test-compose.yml up -d

Just make sure you create the proper config files first

poetry
------
This project uses [poetry](https://python-poetry.org/) for Python requirements
both for development and building the Docker container.

Python tests
------------
Coming soon ;)

Return to [README](README.md)
