from flask import Flask, request, jsonify, send_file
import subprocess
import tempfile
import os

app = Flask(__name__)


@app.route("/ocr", methods=["POST"])
def ocr_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Envie um arquivo PDF com o campo 'file'"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Apenas arquivos PDF são aceitos"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.pdf")
        unsigned_path = os.path.join(tmpdir, "unsigned.pdf")
        output_path = os.path.join(tmpdir, "output.pdf")
        file.save(input_path)

        result = subprocess.run([
            "qpdf", "--remove-restrictions",
            input_path, unsigned_path
        ])
        
        result = subprocess.run([
            "ocrmypdf", "-l", "por", '--force-ocr',
            unsigned_path, output_path
        ])

        if result.returncode != 0:
            return jsonify({"error": "Falha ao processar o PDF"}), 500

        return send_file(output_path, mimetype="application/pdf")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
