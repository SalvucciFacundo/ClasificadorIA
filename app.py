import os
import sys
import threading
import webview
from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path
from typing import List, Dict

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_manager import DataManager
from model_manager import ModelManager

# Configuration
if getattr(sys, 'frozen', False):
    APP_DIR = sys._MEIPASS
    DATA_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = APP_DIR

# Initialize Flask
app = Flask(__name__, static_folder=os.path.join(APP_DIR, 'interfaz'), template_folder=os.path.join(APP_DIR, 'interfaz'))

# Managers
dm = DataManager(DATA_DIR)
mm = ModelManager(os.path.join(DATA_DIR, "modelo", "modelo_actual.pth"))

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/images/entrada/<path:filename>')
def serve_image(filename):
    return send_from_directory(dm.paths["entrada"], filename)

@app.route('/api/images', methods=['GET'])
def get_images():
    files = dm.scan_entrada()
    results = []
    for f in files:
        full_path = os.path.join(dm.paths["entrada"], f)
        prediction = mm.predict(full_path)
        results.append({
            "filename": f,
            "prediction": prediction,
            "url": f"/images/entrada/{f}"
        })
    return jsonify(results)

@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist('files[]')
    saved_files = []
    for file in files:
        if file.filename:
            path = dm.save_upload(file, file.filename)
            saved_files.append(file.filename)
            
    return jsonify({"message": f"Uploaded {len(saved_files)} files", "files": saved_files})

@app.route('/api/accept', methods=['POST'])
def accept_classification():
    data = request.json
    items = data.get('items', [])
    
    if not items:
        return jsonify({"error": "No items to process"}), 400
        
    # Process batch (move, index, log)
    stats = dm.process_batch(items)
    
    # Trigger training in background
    threading.Thread(target=run_training).start()
    
    return jsonify({"status": "success", "stats": stats})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    index = dm.load_index()
    real_count = sum(1 for v in index.values() if v["label"] == "real")
    ia_count = sum(1 for v in index.values() if v["label"] == "ia")
    return jsonify({
        "total_indexed": len(index),
        "real": real_count,
        "ia": ia_count
    })

def run_training():
    print("Starting background training...")
    data = dm.get_dataset_files()
    metrics = mm.train(data, epochs=1)
    print(f"Training finished: {metrics}")

def start_server():
    app.run(host='127.0.0.1', port=5000, threaded=True)

if __name__ == '__main__':
    # Start Flask in a separate thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    # Create window
    webview.create_window('Clasificador IA vs Real', 'http://127.0.0.1:5000', width=1280, height=800, resizable=True)
    webview.start()
