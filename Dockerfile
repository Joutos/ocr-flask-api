FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    ghostscript \
    qpdf \
    unpaper \
    pngquant \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    ocrmypdf \
    flask \
    gunicorn

WORKDIR /app
COPY app.py .

# ⚡ usa tmpfs do sistema (mais rápido que disco)
ENV TMPDIR=/tmp

EXPOSE 8080

CMD ["gunicorn", \
    "--bind", "0.0.0.0:8080", \
    "--workers", "3", \
    "--threads", "2", \
    "--timeout", "600", \
    "--preload", \
    "app:app"]