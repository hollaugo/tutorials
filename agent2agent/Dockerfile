# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./pyproject.toml
COPY uv.lock ./uv.lock
RUN pip install --upgrade pip && pip install uv && uv pip install --system --editable .

# Copy project
COPY . .

# Expose port
EXPOSE 10000

# Set environment for Render
ENV PORT=10000

# Start the server
CMD ["uvicorn", "app.api_server:app", "--host", "0.0.0.0", "--port", "10000"] 