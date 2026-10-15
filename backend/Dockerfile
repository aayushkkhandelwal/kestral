FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install OS dependencies for OpenCV, YuNet, and image manipulation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user
RUN groupadd -r kestral && useradd -r -g kestral -d /app -s /sbin/nologin kestral

WORKDIR /app

# Install Python requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "import lap; from ultralytics import YOLO; print('Dependencies validated: lap and ultralytics import successfully')"

# Copy backend codebase
COPY . /app

# Ensure storage directories exist with proper permissions
RUN mkdir -p /app/uploads /app/results /app/faces /app/frames /app/exports \
    && chown -R kestral:kestral /app

USER kestral

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
