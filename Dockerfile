FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade zlib1g && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m pip uninstall -y pip

COPY app/ ./app/

RUN useradd --create-home --uid 10001 appuser

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

