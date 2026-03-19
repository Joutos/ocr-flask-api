import os
import subprocess
import tempfile
import logging
import shutil
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

@app.route("/ocr", methods=["POST"])
def ocr_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Campo 'file' ausente"}), 400

    file = request.files["file"]

    if not file or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Apenas PDF permitido"}), 400

    tmpdir = tempfile.mkdtemp()

    input_path = os.path.join(tmpdir, "input.pdf")
    unsigned_path = os.path.join(tmpdir, "unsigned.pdf")
    output_path = os.path.join(tmpdir, "output.pdf")

    try:
        file.save(input_path)

        subprocess.run(
            ["qpdf", "--remove-restrictions", input_path, unsigned_path],
            check=True
        )

        jobs = max(1, os.cpu_count() // 2)

        subprocess.run([
            "ocrmypdf",
            "-l", "por+eng",
            "--force-ocr",
            "--rotate-pages",
            "--optimize", "1", 
            "--output-type", "pdfa",
            "--pdf-renderer", "sandwich",
            "--jobs", str(jobs), 
            "--tesseract-oem", "1",
            "--tesseract-pagesegmode", "12",
            unsigned_path,
            output_path
        ], check=True)

        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ocr_{secure_filename(file.filename)}'
        )

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else "Erro desconhecido"
        logger.error(f"Erro no OCR: {error_msg}")
        return jsonify({"error": "Falha no processamento", "details": error_msg[:500]}), 500

    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return jsonify({"error": "Erro interno", "message": str(e)}), 500

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)