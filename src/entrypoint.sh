#!/bin/bash

if [ "$DATABASE" = "postgres" ]; then
    echo "Waiting for PostgreSQL..."

    # Check if PostgreSQL is up and running
    while ! nc -z "$SQL_HOST" "$SQL_PORT"; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Run Django management commands
python manage.py migrate
python manage.py collectstatic --no-input --clear

# Run the main command
exec "$@"
