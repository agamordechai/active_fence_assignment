# Multi-stage build for smaller final image
FROM python:3.11-slim

WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/data/raw /app/data/processed /app/logs /app/config

# Copy only requirements first for better layer caching
COPY requirements.txt ./

# Install dependencies (this layer will be cached unless requirements.txt changes)
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files (changes frequently, so separate layer)
COPY src/ ./src/


# Set Python path
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.main"]
