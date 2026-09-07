# --- web app -----------------------------------------------------------------
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm ci
COPY web/ ./
RUN npm run build

# --- server ------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
COPY --from=web /web/dist ./web/dist
ENV RECORDSHELF_DATA_DIR=/app/data \
    RECORDSHELF_LAYOUT_FILE=/app/config/shelf.yaml \
    RECORDSHELF_WEB_DIST=/app/web/dist
VOLUME ["/app/data", "/app/config"]
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "recordshelf", "serve"]
