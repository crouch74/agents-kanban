FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    tmux \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/.acp/logs /app/.acp/artifacts

# Install Python dependencies
# We copy core first since it's a dependency
COPY packages/core /app/packages/core
COPY apps/api/requirements-dev.txt /app/apps/api/requirements-dev.txt
RUN pip install --no-cache-dir -r apps/api/requirements-dev.txt

# Copy the rest of the source
COPY . /app

# Set environment
ENV PYTHONPATH="/app/apps/api:/app/packages/core/src"
ENV ACP_RUNTIME_HOME="/app/.acp"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Start with hot reload enabled
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--app-dir", "apps/api", "--reload-dir", "apps/api", "--reload-dir", "packages/core/src"]
