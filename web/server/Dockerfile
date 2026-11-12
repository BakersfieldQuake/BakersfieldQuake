# Runtime image for the dedicated server and the bakoweb bridge (both run from mounted folders).
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends zlib1g libjpeg62-turbo python3 \
    && rm -rf /var/lib/apt/lists/*
