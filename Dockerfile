FROM python:3.12-slim

ENV POETRY_VERSION=1.8.0
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update && apt-get install -y \
    curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-root --no-dev

COPY . .

CMD ["poetry", "run", "python", "main.py"]
