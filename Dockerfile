# Stage 1: Build environment
FROM python:3.12-slim AS builder

# Set work directory
WORKDIR /usr/src/main

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1

# Install system dependencies required for building dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir --upgrade pip poetry && \
    poetry config virtualenvs.create false

# Copy only dependency files
COPY pyproject.toml poetry.lock* /usr/src/main/

# Install project dependencies
RUN poetry install --no-dev --no-interaction --no-ansi --no-cache

# Stage 2: Runtime environment
FROM python:3.12-slim

# Set work directory
WORKDIR /usr/src/main

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl ncat ffmpeg libgl1 libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY ./src/ /usr/src/main/

# Copy entrypoint script and set permissions
COPY --chown=1000:1000 --chmod=755 ./src/entrypoint.sh /usr/src/main/entrypoint.sh

# Final command
CMD ["/usr/src/main/entrypoint.sh"]
