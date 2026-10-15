FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HOME=/app \
    PYTHONPATH=/app \
    YOLO_AUTOINSTALL=False

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

# Cache bust to ensure fresh dependency installation
ARG CACHEBUST=20261015-v2

# Install Python requirements using explicit python3 -m pip
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir -U pip setuptools wheel \
    && python3 -m pip install --no-cache-dir -r requirements.txt \
    && chmod -R a+rX /usr/local/lib/python3.12/site-packages

# Diagnostic & build-time verification as root
RUN python3 -c "import sys, site, lap; \
    print('--- ROOT BUILD-TIME DIAGNOSTICS ---'); \
    print('sys.executable:', sys.executable); \
    print('sys.path:', sys.path); \
    print('site-packages:', site.getsitepackages()); \
    print('lap file:', lap.__file__); \
    print('lap version:', lap.__version__); \
    from ultralytics import YOLO; \
    from ultralytics.trackers.utils import matching; \
    print('Root check: lap and ByteTrack matching successfully loaded')"

# Copy backend codebase
COPY . /app

# Ensure storage directories exist with proper permissions
RUN mkdir -p /app/uploads /app/results /app/faces /app/frames /app/exports /app/clips \
    && chown -R kestral:kestral /app

# Switch to non-root runtime user
USER kestral

# Non-root runtime user verification: fails Docker build if kestral user cannot import lap
RUN python3 -c "import sys, site, os, lap; \
    print('--- RUNTIME USER DIAGNOSTICS ---'); \
    print('uid:', os.getuid(), 'HOME:', os.environ.get('HOME')); \
    print('sys.executable:', sys.executable); \
    print('lap file:', lap.__file__); \
    print('lap version:', lap.__version__); \
    from ultralytics import YOLO; \
    from ultralytics.trackers.utils import matching; \
    print('Non-root runtime user: lap and ByteTrack matching verified successfully')"

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

CMD ["sh", "-c", "python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
