# Mi AI Service - RunPod Docker Image
# ==================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Mi AI Service Team"
LABEL version="2.0.0"
LABEL description="Arabic-focused AI image generation service with Supabase integration"

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Work directory
WORKDIR /workspace/mi-ai-service-runpod

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    fonts-dejavu-core \
    fonts-liberation \
    libfontconfig1 \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    libmagickwand-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /workspace/mi-ai-service-runpod/{logs,backups,outputs,temp}
RUN mkdir -p /tmp/generated_images

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy application files
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Create non-root user for security
RUN groupadd -r miservice && useradd -r -g miservice -d /workspace/mi-ai-service-runpod -s /bin/bash miservice

# Set proper permissions
RUN chown -R miservice:miservice /workspace/mi-ai-service-runpod
RUN chown -R miservice:miservice /tmp/generated_images

# Switch to non-root user
USER miservice

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000
EXPOSE 9090

# Volume mounts for persistent data
VOLUME ["/workspace/mi-ai-service-runpod/logs", "/workspace/mi-ai-service-runpod/backups", "/tmp/generated_images"]

# Default command
CMD ["python3", "main.py"]
