FROM python:3.11-slim

# Instala dependências do OCRmyPDF e Tesseract com suporte a português
RUN apt-get update && \
    apt-get install -y ocrmypdf tesseract-ocr tesseract-ocr-por ghostscript qpdf && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Instala Flask para API
RUN pip install flask

WORKDIR /app
COPY app.py .

EXPOSE 8080
CMD ["python3", "app.py"]
