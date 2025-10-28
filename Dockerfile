# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.toml README.md ./

# Install dependencies without installing the current project
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Copy source code
COPY src/ ./src/

# Install the current project
RUN poetry install --only-root

# Create a non-root user with specific UID/GID for better host compatibility
RUN groupadd -g 1000 hermes && \
    useradd -u 1000 -g 1000 --create-home --shell /bin/bash hermes && \
    chown -R hermes:hermes /app
USER hermes

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["poetry", "run", "uvicorn", "hermesbaby.hermes.main:app", "--host", "0.0.0.0", "--port", "8000"]