FROM python:3.13-alpine

ARG _WORKDIR=/app

WORKDIR ${_WORKDIR}

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT="/venv"

RUN --mount=type=cache,target=/root/.cache/uv \
    apk add --no-cache --virtual .build-deps \
        build-base \
        python3-dev \
        linux-headers \
        pcre-dev \
        postgresql-dev \
        musl-dev \
        gcc \
    && apk add --no-cache \
        pcre \
        libpq 

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project \
    && apk del .build-deps

ENV PATH="/venv/bin:$PATH"

CMD uvicorn app.main:app --host 0.0.0.0 --reload