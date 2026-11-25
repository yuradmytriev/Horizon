# Use Python 3.11 slim image
# Pinned by digest: a re-tagged upstream image can't change what gets built.
FROM python:3.11-slim@sha256:61e01f72680f86a5279ad510818ab7b2ee9f049822589d4e34e33e044360356c

# Set working directory
WORKDIR /app

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:0.13.10@sha256:a3ea1357342c1a4bf9a0c53a3deb1b55379aefa037338d8113d5771efa01774f /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY data ./data
COPY profiles ./profiles
COPY .env.example .env.example

# Install optional extras from a comma-separated list, e.g. "trafilatura,openbb".
ARG EXTRAS=""
RUN set -eu; \
    set --; \
    if [ -n "$EXTRAS" ]; then \
        case "$EXTRAS" in ,*|*,|*,,*) echo "Invalid EXTRAS list: $EXTRAS" >&2; exit 2 ;; esac; \
        old_ifs=$IFS; IFS=,; \
        for extra in $EXTRAS; do \
            case "$extra" in [._-]*|*[._-]|*[!A-Za-z0-9._-]*) echo "Invalid extra: $extra" >&2; exit 2 ;; esac; \
            set -- "$@" --extra "$extra"; \
        done; \
        IFS=$old_ifs; \
    fi; \
    uv sync --frozen --no-dev "$@"

# Runtime data is mounted here; keep the image and process unprivileged.
# Only data/ is writable by the runtime user; app code stays root-owned.
RUN useradd --create-home --uid 10001 horizon \
    && mkdir -p /app/data && chown -R horizon:horizon /app/data

# Create volume mount points
VOLUME ["/app/data"]

# Set environment variables
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER horizon

# Run the application
# Run the venv binary directly: `uv run` could re-resolve and download packages at runtime.
ENTRYPOINT ["/app/.venv/bin/horizon"]
CMD []
