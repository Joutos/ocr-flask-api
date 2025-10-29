# OCR Flask API  
API simples em Flask que adiciona uma camada de OCR para PDFs — ideal para arquivos baseados em imagem.

## Visão Geral  
Esta aplicação‑microserviço fornece um endpoint HTTP para receber documentos PDF (especialmente aqueles compostos por imagens) e aplicar reconhecimento óptico de caracteres (OCR). O resultado é um novo PDF com o texto reconhecido e/ou extração de texto bruto, conforme configuração.  

## Funcionalidades  
- Recebe arquivo PDF via upload HTTP.  
- Aplica OCR nas páginas que contêm imagens (ou todo o documento) para extrair texto.  
- Retorna:  
  - Um PDF com camada de texto extraída (searchable PDF), **ou**  
  - Texto bruto extraído (plaintext), dependendo da rota ou parâmetro.  
- Empacotado via Docker para fácil deploy.  

## Tecnologias Utilizadas  
- Python + Flask para a API.  
- Engine de OCR (por exemplo, Tesseract OCR).  
- Containerização via Docker.  
- Bibliotecas para manipulação de PDFs e imagens (PyMuPDF, pdf2image, etc.).  

## Pré‑requisitos  
- Docker instalado (para deploy via container) **ou**  
- Python 3.7+ + dependências via `pip`.  
- Para execução local: engine de OCR instalada no sistema.

## 🔧 Instalação & Execução  

### Usando Docker  
```bash
git clone https://github.com/Joutos/ocr-flask-api.git
cd ocr-flask-api
docker build -t ocr-flask-api .
docker run --rm -p 8080:8080 ocr-flask-api
```

### Endpoint

```/ocr```:

#### Método: `POST`
Endpoint responsável por processar o OCR de um arquivo PDF enviado via `multipart/form-data`.

#### Requisição
- **URL:** `http://localhost:8080/ocr`
- **Método:** `POST`
- **Content-Type:** `multipart/form-data`
- **Parâmetros do corpo (Body):**
  | Campo  | Tipo             | Obrigatório | Descrição                                   |
  | ------ | ---------------- | ----------- | ------------------------------------------- |
  | `file` | Arquivo (`.pdf`) | ✅           | O arquivo PDF que será processado pelo OCR. |

#### Exemplo via cURL
```bash
curl -X POST http://localhost:8080/ocr \
  -F "file=@/caminho/para/teste imagem.pdf" \
  --output output.pdf
  ```