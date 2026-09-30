FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      espeak-ng ffmpeg curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements.lock
COPY generate.py docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh
VOLUME ["/models", "/audio"]
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["--help"]
