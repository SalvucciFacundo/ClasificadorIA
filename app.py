import os
import sys
import threading
import webview
from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path
from typing import List, Dict
import importlib.util
import time

# Configuration
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    if hasattr(sys, '_MEIPASS'):
        # Check if resources are bundled (Normal Exe)
        bundled_ui = os.path.join(sys._MEIPASS, 'ui')
        if os.path.exists(bundled_ui):
            # Normal Mode: Use bundled resources
            UI_DIR = bundled_ui
            LOGIC_DIR = os.path.join(sys._MEIPASS, 'logic')
            DATA_DIR = os.path.dirname(sys.executable) # Data always external
        else:
            # Optimized Mode: Resources are external
            EXE_DIR = os.path.dirname(sys.executable)
            UI_DIR = os.path.join(EXE_DIR, 'ui')
            LOGIC_DIR = os.path.join(EXE_DIR, 'logic')
            DATA_DIR = EXE_DIR
    else:
        # OneDir mode
        EXE_DIR = os.path.dirname(sys.executable)
        UI_DIR = os.path.join(EXE_DIR, 'ui')
        LOGIC_DIR = os.path.join(EXE_DIR, 'logic')
        DATA_DIR = EXE_DIR
else:
    # Running as script
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))
    UI_DIR = os.path.join(EXE_DIR, 'ui')
    LOGIC_DIR = os.path.join(EXE_DIR, 'logic')
    DATA_DIR = EXE_DIR

# Check for UI directory
if not os.path.exists(UI_DIR):
    # Fallback for development (if 'interfaz' exists in current dir)
    dev_ui = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interfaz')
    if not getattr(sys, 'frozen', False) and os.path.exists(dev_ui):
        UI_DIR = dev_ui
        print(f"Using development UI at: {UI_DIR}")
    else:
        print(f"Archivo de interfaz no encontrado en: {UI_DIR}")
        # We continue, but Flask might fail if accessed.

# Logging System
log_buffer = []
log_lock = threading.Lock()

def add_log(message: str, level: str = "INFO"):
    timestamp = time.strftime("%H:%M:%S")
    with log_lock:
        log_buffer.append(f"[{timestamp}] [{level}] {message}")
        if len(log_buffer) > 1000:  # Keep last 1000 logs
            log_buffer.pop(0)

# Redirect stdout/stderr to capture prints
class StreamLogger:
    def __init__(self, original, level="INFO"):
        self.original = original
        self.level = level
        # Flask messages to ignore (they're not real errors)
        self.ignore_patterns = [
            "WARNING: This is a development server",
            "* Running on",
            "Press CTRL+C to quit",
            "GET /",
            "POST /",
            "\" 200 -",  # Successful requests
            "\" 304 -",  # Not modified (cached)
            "\" 404 -",  # Not found (favicon, etc.)
            ".well-known",
            "favicon.ico"
        ]

    def write(self, message):
        self.original.write(message)
        msg = message.strip()
        
        if not msg:
            return
            
        # Filter out Flask's normal HTTP logs when coming from stderr
        if self.level == "ERROR":
            # Check if it's a Flask HTTP log or dev server message
            should_ignore = any(pattern in msg for pattern in self.ignore_patterns)
            if should_ignore:
                return  # Don't log it
        
        add_log(msg, self.level)

    def flush(self):
        self.original.flush()

sys.stdout = StreamLogger(sys.stdout, "INFO")
sys.stderr = StreamLogger(sys.stderr, "ERROR")

# Dynamic Logic Loading
def load_logic_module(module_name, file_name):
    """
    Tries to load a module from LOGIC_DIR/file_name.py.
    Falls back to importing module_name from standard path.
    """
    external_path = os.path.join(LOGIC_DIR, f"{file_name}.py")
    
    if os.path.exists(external_path):
        try:
            spec = importlib.util.spec_from_file_location(module_name, external_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            add_log(f"Cargado módulo externo: {file_name}.py", "INFO")
            return module
        except Exception as e:
            add_log(f"Error cargando módulo externo {file_name}: {e}", "ERROR")
            # Fallback to internal
    
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        add_log(f"Error importando módulo interno {module_name}: {e}", "CRITICAL")
        raise e

# Load Managers
try:
    dm_module = load_logic_module('data_manager', 'data_manager')
    mm_module = load_logic_module('model_manager', 'model_manager')
    
    DataManager = dm_module.DataManager
    ModelManager = mm_module.ModelManager
except Exception as e:
    add_log(f"Fatal error loading managers: {e}", "CRITICAL")
    sys.exit(1)

# Initialize Flask
app = Flask(__name__, static_folder=UI_DIR, template_folder=UI_DIR)

# Managers Initialization
print(f"DEBUG: Initializing managers with DATA_DIR: {DATA_DIR}")
dm = DataManager(DATA_DIR)
mm = ModelManager(os.path.join(DATA_DIR, "modelo", "modelo_actual.pth"))

# Check dataset on startup
try:
    stats = dm.get_detailed_stats()
    if not stats["dataset_base_exists"]:
        add_log("Dataset base no encontrado. Crear carpeta o cargar imágenes.", "WARNING")
    else:
        add_log(f"Dataset base encontrado. Imágenes aprendidas: {stats['total_learned']}", "INFO")
except Exception as e:
    add_log(f"Error checking stats: {e}", "ERROR")

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
    try:
        files = dm.scan_entrada()
        results = []
        for f in files:
            full_path = os.path.join(dm.paths["entrada"], f)
            try:
                prediction = mm.predict(full_path)
            except Exception as e:
                add_log(f"Error clasificando {f}: {e}", "ERROR")
                prediction = "Error"
            
            results.append({
                "filename": f,
                "prediction": prediction,
                "url": f"/images/entrada/{f}"
            })
        return jsonify(results)
    except Exception as e:
        add_log(f"Error escaneando entrada: {e}", "ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist('files[]')
    saved_files = []
    errors = []
    
    for file in files:
        if file.filename:
            try:
                path = dm.save_upload(file, file.filename)
                saved_files.append(file.filename)
                add_log(f"Imagen cargada: {file.filename}", "INFO")
            except Exception as e:
                error_msg = f"Error cargando {file.filename}: {e}"
                errors.append(error_msg)
                add_log(error_msg, "ERROR")
            
    return jsonify({
        "message": f"Uploaded {len(saved_files)} files", 
        "files": saved_files,
        "errors": errors
    })

@app.route('/api/accept', methods=['POST'])
def accept_classification():
    data = request.json
    items = data.get('items', [])
    
    if not items:
        return jsonify({"error": "No items to process"}), 400
        
    # Process batch (move, index, log)
    try:
        stats = dm.process_batch(items)
        add_log(f"Procesado lote: {stats}", "INFO")
        
        # Trigger training in background
        threading.Thread(target=run_training).start()
        
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        add_log(f"Error procesando lote: {e}", "ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(dm.get_detailed_stats())

@app.route('/api/logs', methods=['GET'])
def get_logs():
    with log_lock:
        return jsonify(log_buffer)

@app.route('/api/remove', methods=['POST'])
def remove_image():
    """Remove an image from the entrada folder"""
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    
    try:
        image_path = os.path.join(dm.paths["entrada"], filename)
        
        if not os.path.exists(image_path):
            return jsonify({"error": "File not found"}), 404
        
        os.remove(image_path)
        add_log(f"Imagen eliminada: {filename}", "INFO")
        
        return jsonify({"status": "success", "message": f"Deleted {filename}"})
    except Exception as e:
        add_log(f"Error eliminando {filename}: {e}", "ERROR")
        return jsonify({"error": str(e)}), 500


def run_training():
    print("Starting background training...")
    try:
        data = dm.get_dataset_files()
        metrics = mm.train(data, epochs=1)
        print(f"Training finished: {metrics}")
    except Exception as e:
        print(f"Training failed: {e}")

def start_server():
    # Disable reloader to avoid issues in thread
    app.run(host='127.0.0.1', port=5000, threaded=True, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in a separate thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    # Create window
    # Hot reload logic: if we are in dev mode, we might want to enable dev tools
    debug_mode = not getattr(sys, 'frozen', False)
    
    webview.create_window('Clasificador IA vs Real', 'http://127.0.0.1:5000', width=1280, height=800, resizable=True)
    webview.start(debug=debug_mode)
