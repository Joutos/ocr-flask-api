from flask import Flask, request, jsonify, send_file, after_this_request
import subprocess
import tempfile
import os
import shutil

app = Flask(__name__)


@app.route("/ocr", methods=["POST"])
def ocr_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Envie um arquivo PDF com o campo 'file'"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Apenas arquivos PDF são aceitos"}), 400

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

        subprocess.run([
            "ocrmypdf",
            "-l", "por+eng",
            "--force-ocr",
            "--oversample", "300",
            "--rotate-pages",
            "--deskew",
            "--clean",
            "--clean-final",
            "--optimize", "3",
            "--output-type", "pdfa",
            "--pdf-renderer", "sandwich",
            "--jobs", "4",
            "--tesseract-oem", "1",
            "--tesseract-pagesegmode", "12",
            unsigned_path,
            output_path
        ], check=True)

    except subprocess.CalledProcessError:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return jsonify({"error": "Falha ao processar o PDF"}), 500

    @after_this_request
    def cleanup(response):
        shutil.rmtree(tmpdir, ignore_errors=True)
        return response

    return send_file(output_path, mimetype="application/pdf")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
