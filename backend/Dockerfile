FROM python:3.11-slim

# Stage 0: Copy official Deno binary (Deno 2.x, statically compiled, natively preferred by yt-dlp)
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

# Install system dependencies: FFmpeg, FFprobe, and Node.js 22 LTS
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create temporary storage directory with open permissions for cloud/HuggingFace non-root workers
RUN mkdir -p /tmp/downloader && chmod 777 /tmp/downloader

EXPOSE 8000 7860

# Critical memory limits for 512MB cloud containers:
# 1. PYTHONUNBUFFERED=1 ensures real-time log flushing
# 2. MALLOC_ARENA_MAX=2 restricts glibc heap allocation arenas, preventing memory fragmentation bloat
# 3. FFMPEG_THREADS=1 ensures child transcoding threads do not exceed container memory
ENV PYTHONUNBUFFERED=1 \
    MALLOC_ARENA_MAX=2 \
    FFMPEG_THREADS=1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --limit-concurrency 15"]
