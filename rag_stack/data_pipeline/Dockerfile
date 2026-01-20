FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin

COPY pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --group prod --group pipeline --no-dev

# Copy pipeline code from build context (rag_stack/)
COPY data_pipeline/ ./data_pipeline/

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []
