FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy dependency files from parent directory
COPY ../pyproject.toml ../uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code from parent directory
COPY ../ ./

# Expose port
EXPOSE 8080

# Run the FastAPI server
CMD ["uv", "run", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080"]

