FROM python:3.10-slim

WORKDIR /app

# Install git for GitHub repository analysis
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# The requested start command 'uvicorn main:app' expects to run from the backend directory
WORKDIR /app/backend

# Expose port
EXPOSE 10000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
