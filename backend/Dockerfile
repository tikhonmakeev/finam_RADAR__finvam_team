FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    liblensfun-dev \
    libdbus-1-dev \
    libglib2.0-dev \
    libcairo2-dev \
    libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
