FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY src/services/rag/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/services/rag ./rag
# Create empty services init to allow imports if needed, though we run as rag package
# Actually, we just need rag package in pythonpath
ENV PYTHONPATH=/app

# Create data directories
RUN mkdir -p /app/data/uploads /app/logs

EXPOSE 8000

CMD ["uvicorn", "rag.app:app", "--host", "0.0.0.0", "--port", "8000"]
