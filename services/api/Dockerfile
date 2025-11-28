# API Service Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for fast package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Create a minimal src directory structure so the package can be installed
RUN mkdir -p src/database && touch src/__init__.py && touch src/database/__init__.py

# Install dependencies using uv pip install
RUN uv pip install --system --no-cache .

# Now copy the actual source code (this layer changes more frequently)
COPY src/ ./src/

# Set Python path and disable output buffering for Docker logs
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 8000

# Default command - run uvicorn
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
