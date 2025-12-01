import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
from pathlib import Path

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_manager import DataManager
from model_manager import ModelManager

# Configuration
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    APP_DIR = sys._MEIPASS # Bundled resources (interfaz)
    DATA_DIR = os.path.dirname(sys.executable) # External data (datasets, models)
else:
    # Running as script
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = APP_DIR

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Managers
dm = DataManager(DATA_DIR)
mm = ModelManager(os.path.join(DATA_DIR, "modelo", "modelo_actual.pth"))

# Models
class MoveRequest(BaseModel):
    filename: str
    label: str # 'real' or 'ia'

class TrainRequest(BaseModel):
    epochs: int = 1

# API Endpoints

@app.get("/api/images")
def get_images():
    """List images in entrada with pre-classification."""
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
    return results

@app.post("/api/move")
def move_image(req: MoveRequest, background_tasks: BackgroundTasks):
    try:
        dm.move_and_index(req.filename, req.label)
        
        # Trigger auto-training in background
        background_tasks.add_task(run_training)
        
        return {"status": "success", "message": f"Moved {req.filename} to {req.label}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_training():
    print("Starting background training...")
    data = dm.get_dataset_files()
    metrics = mm.train(data, epochs=1) # Short epoch for incremental
    print(f"Training finished: {metrics}")
    # Log metrics if needed

@app.get("/api/stats")
def get_stats():
    # Return simple stats from index
    index = dm.load_index()
    real_count = sum(1 for v in index.values() if v["label"] == "real")
    ia_count = sum(1 for v in index.values() if v["label"] == "ia")
    return {
        "total_indexed": len(index),
        "real": real_count,
        "ia": ia_count
    }

# Serve Images
# We need to serve 'entrada', 'dataset_base', 'clasificaciones' to show them in UI.
# Since they are absolute paths, we can mount them.
app.mount("/images/entrada", StaticFiles(directory=str(dm.paths["entrada"])), name="entrada")
# app.mount("/images/dataset_base", StaticFiles(directory=str(dm.paths["dataset_base"])), name="dataset_base") # If needed
# app.mount("/images/clasificaciones", StaticFiles(directory=str(dm.paths["clasificaciones"])), name="clasificaciones") # If needed

# Serve UI
# We'll serve the 'interfaz' folder as static, and index.html as root.
app.mount("/", StaticFiles(directory=os.path.join(APP_DIR, "interfaz"), html=True), name="ui")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
