FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.4.28 /uv /uvx /bin/

ADD . /app/

WORKDIR /app
RUN uv sync --frozen

CMD ["uv", "run", "main.py"]
