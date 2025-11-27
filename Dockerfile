# Use Python 3.11 slim image
CMD ["python", "-m", "src.main"]
# Default command

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# Set environment variables

RUN mkdir -p /app/data/raw /app/data/processed /app/logs
# Create directories for data output

RUN poetry install --no-interaction --no-ansi
# Install the project itself

COPY . .
# Copy application code

RUN poetry install --no-interaction --no-ansi --no-root
# Install dependencies using Poetry

COPY pyproject.toml poetry.lock* ./
# Copy dependency files

RUN poetry config virtualenvs.create false
# Configure Poetry to not create virtual environments (we're in a container)

RUN pip install poetry==1.7.1
# Install Poetry

ENV PATH="/root/.cargo/bin:${PATH}"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# Install UV

    && rm -rf /var/lib/apt/lists/*
    build-essential \
    curl \
RUN apt-get update && apt-get install -y \
# Install system dependencies

WORKDIR /app
# Set working directory

FROM python:3.11-slim

