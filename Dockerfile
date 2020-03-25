FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

LABEL maintainer "leblancfg"

ENV POETRY_VERSION=1.0.5

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /pysetup
COPY ./poetry.lock ./pyproject.toml /pysetup/

RUN poetry config virtualenvs.create false \
  && poetry install
