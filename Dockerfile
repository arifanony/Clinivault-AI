# Clinivault AI production image (M7, DECISION-021).
#
# Build:  docker build -t clinivault-ai .
# Run:    docker run --rm -p 8000:8000 \
#           -e GOOGLE_API_KEY=<key> \
#           [-v hf-cache:/home/appuser/.cache/huggingface] \
#           clinivault-ai [--provider hash]
#
# Notes:
# - Live generation needs GOOGLE_API_KEY in the environment (never baked
#   into the image). `--provider hash` is the keyless smoke path.
# - Production E5 retrieval (--provider e5, the default) needs the
#   `intfloat/e5-small-v2` weights in the Hugging Face cache: mount a
#   populated cache volume (shown above) or extend this image with an
#   explicit, audited download step. The app fails loud when the cache
#   is absent; it never falls back silently.

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv/clinivault/src

WORKDIR /srv/clinivault

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Corpus artifacts: the API loads its 727-chunk index from data/ at
# startup (load_store resolves paths from the repo root), so the image
# must carry the parsed corpus and the production E5 embeddings.
# Only the E5 tree is copied - the other embedded-* trees are
# experiment baselines, not needed at runtime. Without these lines
# the container crashes on boot with FileNotFoundError for
# data/parsed/.../T2D-001.parsed.json and /health never serves.
COPY data/parsed ./data/parsed
COPY data/embedded-intfloat--e5-small-v2 ./data/embedded-intfloat--e5-small-v2

RUN pip install --no-cache-dir .

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /srv/clinivault
USER appuser

EXPOSE 8000

CMD ["python", "-m", "clinivault_ai.api", "--host", "0.0.0.0", "--port", "8000"]
