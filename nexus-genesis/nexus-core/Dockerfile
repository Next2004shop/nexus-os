# Production Build for NEXUS CORE
FROM python:3.11-slim

# Directive: Force real-time log streaming
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/init.d/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Directive: Expose port for Cloud Run
EXPOSE 8080

# Ignition command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
