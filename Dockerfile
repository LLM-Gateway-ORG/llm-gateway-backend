# pull official base image
FROM python:3.12-slim

# set work directory
WORKDIR /usr/src/main

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ libpq-dev curl ncat && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# install python dependencies
RUN pip install --upgrade pip \
    && pip install ruamel.yaml.clib psycopg2-binary

# Install Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# install project dependencies
COPY pyproject.toml poetry.lock* /usr/src/main/
RUN poetry install --no-dev --no-interaction --no-ansi

# copy entrypoint.sh
COPY ./src/entrypoint.sh /usr/src/main/entrypoint.sh
# Ensure entrypoint.sh is executable
RUN chmod +x /usr/src/main/entrypoint.sh

# copy project
COPY ./src/ /usr/src/main/

# run entrypoint.sh
CMD sh /usr/src/main/entrypoint.sh