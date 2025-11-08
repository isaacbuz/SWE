# Multi-stage Dockerfile for FastAPI API service
# Optimized for production use with minimal final image size

# Stage 1: Builder - Install dependencies and compile packages
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY apps/api/requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim

# Set metadata labels
LABEL maintainer="AI-First SWE Company"
LABEL description="FastAPI service for AI-First SWE Company"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY apps/api/ /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (change as needed for your API)
EXPOSE 8000

# Health check configuration
# IMPORTANT: Adjust the path and timeout based on your actual health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - start Uvicorn server
# IMPORTANT: Update the module and app paths to match your FastAPI application
# For example: python -m uvicorn src.main:app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Alternative configurations for development/debug:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#
# Alternative with gunicorn for better production performance:
# RUN pip install gunicorn
# CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# Notes on production optimization:
# 1. This image uses multi-stage builds to minimize final size
# 2. Non-root user (appuser) for security
# 3. Health checks included for orchestration
# 4. Python compiled packages are cached in virtual environment
# 5. Build dependencies are excluded from final image
# 6. Image size is approximately 300-400MB depending on dependencies
# 7. For even smaller images, consider using python:3.11-alpine (may have compatibility issues)
