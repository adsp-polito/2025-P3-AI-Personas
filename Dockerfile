见，# Multi-stage build for smaller final image
FROM python:3.10-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY adsp/ ./adsp/
COPY scripts/ ./scripts/
COPY pyproject.toml setup.cfg ./

# Install the package
RUN pip install --no-cache-dir -e .

# Create directories for data
RUN mkdir -p data/raw data/processed data/interim

# Expose API port
EXPOSE 8000

# Run the API server
CMD ["python", "scripts/run_api.py"]
