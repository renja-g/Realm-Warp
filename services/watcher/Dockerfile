FROM python:3.12.2-bullseye as builder

WORKDIR /app

RUN pip install poetry==1.8.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

COPY services/watcher/pyproject.toml services/watcher/poetry.lock ./

COPY libs/db_models/ /libs/db_models

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --only main --no-root


FROM python:3.12.2-slim-bullseye as runtime

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY .env ./
COPY services/watcher/main.py /app/services/watcher/


ENTRYPOINT ["python", "./services/watcher/main.py"]
