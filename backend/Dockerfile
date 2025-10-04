FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc \
    pkg-config \
    liblensfun-dev \
    libdbus-1-dev \
    libglib2.0-dev \
    libcairo2-dev \
    gobject-introspection \
    libgirepository1.0-dev \
    gir1.2-gtk-3.0 \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["sh", "-c", "uvicorn main:app --host ${SERVER_HOST:-0.0.0.0} --port ${SERVER_PORT:-8000}"]
