# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]