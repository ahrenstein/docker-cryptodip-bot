#
# Copyright 2021, Matthew Ahrenstein, All Rights Reserved.
#
# Maintainers:
# - Matthew Ahrenstein: matt@ahrenstein.com
#
# See LICENSE
#

FROM python:3.8
LABEL maintainer = "Matthew Ahrenstein <matt@ahrenstein.com>"

# Copy the source code and poetry config to /app
COPY ./SourceCode/ /app
COPY pyproject.toml /app/

# Configure the Python environment using poetry
WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

# Make sure logging to stdout works
ENV PYTHONUNBUFFERED=0

# Run the bot
CMD ["python", "-u", "/app/cryptodip_bot.py", "-c", "/config/config.json"]
