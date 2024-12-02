# pull official base image
FROM python:3.12-slim

# set work directory
WORKDIR /usr/src/main

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ libpq-dev curl ncat ffmpeg libgl1 libglib2.0-0 && \
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
RUN poetry install --no-interaction --no-ansi --only main

# copy entrypoint.sh
COPY ./src/entrypoint.sh /usr/src/main/entrypoint.sh
RUN ["chmod", "+x", "/usr/src/main/entrypoint.sh"]

# copy project
COPY ./src/ /usr/src/main/
RUN ls -a

# run entrypoint.sh
# ENTRYPOINT ["sh", "/usr/src/main/entrypoint.sh"]