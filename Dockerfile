# Multi-stage build: First stage to copy uv
FROM ghcr.io/astral-sh/uv:latest AS uv

# Second stage: Main application
FROM python:3.11-slim

WORKDIR /app

# Install uv from the first stage
COPY --from=uv /uv /usr/local/bin/uv

# Create necessary directories
RUN mkdir -p /app/data/raw /app/data/processed /app/logs /app/config

# Copy project files
COPY pyproject.toml ./
COPY requirements.txt* ./
COPY src/ ./src/

# Install dependencies using pip as fallback if uv sync fails
RUN if [ -f "requirements.txt" ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        uv pip install --system praw pandas numpy transformers torch scikit-learn nltk spacy requests aiohttp python-dotenv pydantic pydantic-settings loguru schedule apscheduler ratelimit; \
    fi

# Set Python path
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.main"]
