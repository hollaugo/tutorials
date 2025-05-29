# Use an official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN pip install --upgrade pip && pip install uv

# Copy project files
COPY . /app/

# Install Python dependencies with uv
RUN uv pip install -r requirements.txt --system || true

# Render uses the PORT environment variable, default to 8005 if not set
ENV PORT=8005

# Expose the port (Render will override this with their own PORT)
EXPOSE $PORT

# Start the MCP server
CMD python server.py