FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy the rest of the code
COPY . .

# Expose port
EXPOSE 8000

# Run the CLI or server
CMD ["legal-agent", "start-server"]