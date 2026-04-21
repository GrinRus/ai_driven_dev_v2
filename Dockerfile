FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY . /app

RUN uv pip install --system -e ".[dev]"

ENTRYPOINT ["aidd"]
CMD ["--help"]
