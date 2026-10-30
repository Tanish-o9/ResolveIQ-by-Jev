# ResolveIQ-by-Jev Production Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose server port
EXPOSE 8080

# Run uvicorn server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

