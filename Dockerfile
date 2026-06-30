FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY evalforge/ evalforge/

RUN pip install --no-cache-dir -e ".[all]"

EXPOSE 7860

ENTRYPOINT ["evalforge"]
CMD ["serve"]
