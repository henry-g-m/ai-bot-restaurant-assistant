# Multi-stage build for Python FastAPI application
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder (system site-packages, readable by appuser)
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/
COPY static/ ./static/
COPY data/ ./data/
COPY pyproject.toml setup.py ./

# Install the application package
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Azure Container Apps will map this)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/docs')" || exit 1

# Run the application
CMD ["uvicorn", "restaurant_bot.main:app", "--host", "0.0.0.0", "--port", "8000"]
