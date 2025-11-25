FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-por tesseract-ocr-eng ghostscript qpdf pngquant \
    libxml2 libxslt1.1 unpaper libjpeg62-turbo libpng16-16 libtiff6 jbig2 \ 
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir ocrmypdf

RUN pip install flask

WORKDIR /app
COPY app.py .

EXPOSE 8080
CMD ["python3", "app.py"]
