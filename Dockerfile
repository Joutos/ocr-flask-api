FROM python:3.11-slim

# 1. Instala dependências do sistema (removido jbig2enc que não existe no repo padrão)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    ghostscript \
    qpdf \
    unpaper \
    pngquant \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Instala dependências do Python
# Adicionei gunicorn para produção
RUN pip install --no-cache-dir \
    ocrmypdf \
    flask \
    gunicorn \
    werkzeug

WORKDIR /app

# Copia o seu código
COPY app.py .

# Garante permissões na pasta temporária
RUN mkdir -p /tmp && chmod 777 /tmp

EXPOSE 8080

# Rodando com Gunicorn para suportar concorrência no seu container
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "600", "app:app"]