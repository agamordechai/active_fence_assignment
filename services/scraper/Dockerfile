# Scraper Service Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for fast package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Create a minimal src directory structure so the package can be installed
RUN mkdir -p src/collectors src/enrichers src/scorers && \
    touch src/__init__.py && \
    touch src/collectors/__init__.py && \
    touch src/enrichers/__init__.py && \
    touch src/scorers/__init__.py

# Install dependencies using uv pip install
RUN uv pip install --system --no-cache .

# Now copy the actual source code (this layer changes more frequently)
COPY src/ ./src/

# Set Python path and disable output buffering for Docker logs
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command - run the scraper
CMD ["python", "-m", "src.main"]
