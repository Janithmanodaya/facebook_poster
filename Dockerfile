FROM ghcr.io/library/python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (include image libraries required by Pillow to avoid runtime segfaults)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg62-turbo \
    zlib1g \
    libpng16-16 \
    libwebp7 \
    libtiff6 \
    libfreetype6 \
 && rm -rf /var/lib/apt/lists/*

/apt/lists/*

# Copy and install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app /app/app
COPY client /app/client

# Expose port (platforms usually provide PORT; default to 8080)
EXPOSE 8080
ENV PORT=8080

# Optional API key (set via environment at deploy)
# ENV API_KEY=""

# Use shell form so ${PORT} is honored by the platform if provided
CMD sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}'
