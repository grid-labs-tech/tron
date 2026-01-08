FROM python:3.13-alpine

ARG _WORKDIR=/app

WORKDIR ${_WORKDIR}

RUN apk add --virtual .build-dependencies \
            --no-cache \
            python3-dev \
            build-base \
            linux-headers \
            pcre-dev \
            gcc \
            musl-dev \
            postgresql-libs \
            postgresql-dev

RUN apk add --no-cache pcre

COPY requirements.txt /tmp/

RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

COPY . ${_WORKDIR}

CMD uvicorn app.main:app --host 0.0.0.0 --reload