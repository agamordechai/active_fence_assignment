# Use Python 3.11 slim image
FROM python:3.11-slim
# Set working directory
WORKDIR /app
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Copy dependency files first for better caching
COPY pyproject.toml README.md ./
# Create a minimal src directory structure so the package can be installed
RUN mkdir -p src && touch src/__init__.py
# Install dependencies using uv pip install
# The . tells uv to install the package and its dependencies from pyproject.toml
RUN uv pip install --system --no-cache .
# Now copy the actual source code (this layer changes more frequently)
COPY src/ ./src/
# Set Python path
ENV PYTHONPATH=/app
CMD ["python", "-m", "src.main"]
