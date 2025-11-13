# Use Python 3.10 slim base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for TensorFlow and HDF5
RUN apt-get update && apt-get install -y --no-install-recommends \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scripts directory
COPY scripts/ scripts/

# Expose port 8000
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the FastAPI application
CMD ["python", "scripts/inference/app.py"]
