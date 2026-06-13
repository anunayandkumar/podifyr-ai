FROM python:3.14-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ─── Builder stage ───────────────────────────────────────────────────────────
FROM base AS builder

COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

RUN pip install --no-cache-dir build && \
    python -m build --wheel --outdir /app/dist

# ─── Runtime stage ───────────────────────────────────────────────────────────
FROM base AS runtime

COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Non-root user for security
RUN useradd --create-home --shell /bin/bash podifyr
USER podifyr
WORKDIR /workspace

ENTRYPOINT ["podifyr-ai"]
CMD ["--help"]
