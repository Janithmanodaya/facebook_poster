FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app /app/app
COPY client /app/client

# Expose port for Northflank
EXPOSE 8080

# Optional API key (set via environment at deploy)
# ENV API_KEY=""

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]