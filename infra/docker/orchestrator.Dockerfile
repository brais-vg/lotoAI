FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY src/services/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/services/orchestrator ./orchestrator
COPY src/services/__init__.py ./services/__init__.py

# Configurar PYTHONPATH
ENV PYTHONPATH=/app

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 8090

CMD ["uvicorn", "orchestrator.app:app", "--host", "0.0.0.0", "--port", "8090"]
