import os
import subprocess
import tempfile
import logging
import shutil
import uuid
import gzip
import threading
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from queue import Queue
from threading import Thread
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "ocr_storage", "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "ocr_storage", "completed")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

task_queue = Queue()
job_status = {}


def worker(q, status_dict):
    logger.info(f"Worker iniciado. PID: {os.getpid()}")

    while True:

        if status_dict.get("cleanup_mode"):
            time.sleep(1)
            continue

        task = q.get()

        if task is None:
            break

        if not isinstance(task, tuple) or len(task) != 2:
            logger.error(f"Task inválida: {task}")
            continue

        task_id, original_filename = task

        logger.info(f"Worker recebeu task: {task_id}")

        input_path = os.path.join(UPLOAD_FOLDER, f"{task_id}.pdf")
        output_path = os.path.join(OUTPUT_FOLDER, f"{task_id}.pdf")
        unsigned_path = input_path + ".unsigned"

        status_dict[task_id] = "processing"

        try:
            subprocess.run(
                ["qpdf", "--remove-restrictions", input_path, unsigned_path],
                check=True, capture_output=True
            )

            jobs = max(1, (os.cpu_count() or 2) // 2)

            subprocess.run([
                "ocrmypdf",
                "-l", "por+eng",
                "--force-ocr",
                "--rotate-pages",
                "--optimize", "1",
                "--output-type", "pdfa",
                "--pdf-renderer", "sandwich",
                "--jobs", str(jobs),
                unsigned_path,
                output_path
            ], check=True, capture_output=True)

            logger.info(f"Task {task_id} concluída. Arquivo: {output_path}")
            status_dict[task_id] = "completed"

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode(
                errors="ignore") if e.stderr else "Subprocess failed"
            logger.error(f"OCR Error para {task_id}: {error_msg}")
            status_dict[task_id] = f"failed: {error_msg[:200]}"

        except Exception as e:
            logger.error(f"Erro inesperado no worker: {str(e)}")
            status_dict[task_id] = f"failed: {str(e)}"

        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(unsigned_path):
                os.remove(unsigned_path)


@app.route("/ocr", methods=["POST"])
def enqueue_ocr():
    global task_queue, job_status

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF allowed"}), 400

    task_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_FOLDER, f"{task_id}.pdf")
    file.save(save_path)

    job_status[task_id] = "queued"
    task_queue.put((task_id, secure_filename(file.filename)))
    logger.info(f"Task enfileirada: {task_id}")

    return jsonify({
        "task_id":   task_id,
        "status":    "queued",
        "check_url": f"/status/{task_id}"
    }), 202


@app.route("/status/", methods=["GET"])
def get_all_status():
    return jsonify(job_status)

@app.route("/status/<task_id>", methods=["GET"])
def get_status(task_id):
    status = job_status.get(task_id, "not_found")

    if status == "completed":
        return jsonify({
            "status":       status,
            "download_url": f"/download/{task_id}"
        })

    return jsonify({"status": status})


@app.route("/download/<task_id>", methods=["GET"])
def download_result(task_id):
    path = os.path.join(OUTPUT_FOLDER, f"{task_id}.pdf")
    logger.info(
        f"Download solicitado. Path: {path} | Existe: {os.path.exists(path)}")

    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name=f"ocr_result_{task_id}.pdf")

    return jsonify({"error": "File not found or still processing"}), 404


def clear_old_files():
    for folder in [OUTPUT_FOLDER]:
        files = os.listdir(folder)
        logger.info(f"Iniciando limpeza. Total de arquivos: {len(files)}")

        for filename in files:
            file_path = os.path.join(folder, filename)

            if not os.path.isfile(file_path):
                continue
            try:
                os.remove(file_path)
                logger.info(f"Removido: {file_path}")
            except Exception as e:
                logger.error(f"Erro ao remover {file_path}: {e}")

        remaining = os.listdir(folder)
        logger.info(f"Restaram {len(remaining)} arquivos após limpeza")


def blocking_cleanup(job_status):
    logger.info("Iniciando modo de limpeza...")

    job_status["cleanup_mode"] = True

    logger.info("Aguardando 5 minutos antes da limpeza...")
    time.sleep(300)

    clear_old_files()

    job_status["cleanup_mode"] = False
    logger.info("Limpeza finalizada, processamento liberado.")


def schedule_cleanup(job_status):
    while True:
        time.sleep(1500)
        blocking_cleanup(job_status)


if __name__ == "__main__":
    job_status["cleanup_mode"] = False

    cleanup_thread = threading.Thread(
        target=schedule_cleanup,
        args=(job_status,),
        daemon=True
    )
    cleanup_thread.start()

for i in range(3):
    t = Thread(target=worker, args=(task_queue, job_status), daemon=True)
    t.start()
    logger.info(f"Worker thread {i+1} iniciada")

    app.run(host="0.0.0.0", port=8080, debug=False)
