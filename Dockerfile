# Use Python slim image for security and minimal size
FROM python:3.11-slim AS base

# Metadata
LABEL maintainer="Hulud Security"
LABEL description="Multi-Ecosystem Package Threat Scanner (npm, Maven/Gradle, pip)"
LABEL version="0.2.0"

# Create non-root user for security
RUN groupadd -r scanner && useradd -r -g scanner scanner

# Set up application directory
WORKDIR /app

# Install dependencies in a separate layer for caching
COPY pyproject.toml setup.py ./
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir pyyaml toml && \
    pip cache purge

# Copy application code and default CSV file
COPY src/ ./src/
COPY sha1-Hulud.csv ./

# Create workspace directory for user files
RUN mkdir -p /workspace && chown -R scanner:scanner /workspace /app

# Switch to non-root user
USER scanner

# Set workspace as working directory (where commands run)
WORKDIR /workspace

# Set entrypoint to the multi-ecosystem scanner CLI
ENTRYPOINT ["hulud-scan"]

# Default: scan current directory (workspace), use relative paths
# CSV auto-detected from /app/sha1-Hulud.csv
CMD ["--dir", ".", "--output-relative-paths"]
