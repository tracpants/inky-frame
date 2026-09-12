# Inky Frame - Docker image for development and Pi deployment
# For Pi deployment, build with: docker build --platform linux/arm64 -t inky-frame .

FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenjp2-7 \
    libtiff6 \
    libatlas-base-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .
COPY templates/ templates/
COPY widgets/ widgets/

# Create data directory
RUN mkdir -p /app/data/photos

# Expose port
EXPOSE 5000

# Environment
ENV FLASK_APP=app.py
ENV DATA_DIR=/app/data
ENV PYTHONPATH=/app

# Default to Flask for development, can be overridden for production
CMD ["python", "app.py"]
