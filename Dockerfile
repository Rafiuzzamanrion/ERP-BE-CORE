FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY app/ app/
COPY .env .env
EXPOSE 5000
CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "5000"]
