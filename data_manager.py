import os
import json
import shutil
import time
import hashlib
import sys
from typing import List, Dict, Optional
from pathlib import Path

class DataManager:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        
        self.paths = {
            "dataset_base_real": self.base_path / "dataset_base" / "real",
            "dataset_base_ia": self.base_path / "dataset_base" / "ia",
            "clasificaciones_real": self.base_path / "clasificaciones" / "real",
            "clasificaciones_ia": self.base_path / "clasificaciones" / "ia",
            "entrada": self.base_path / "entrada",
            "index": self.base_path / "index" / "dataset_index.json",
            "logs": self.base_path / "logs" / "historial_correcciones.json",
        }
        self._ensure_files()

    def _ensure_files(self):
        # Ensure directories
        self.paths["index"].parent.mkdir(parents=True, exist_ok=True)
        self.paths["logs"].parent.mkdir(parents=True, exist_ok=True)

        if not self.paths["index"].exists():
            # Try to copy from bundled resource if frozen
            if getattr(sys, 'frozen', False):
                bundled_index = Path(sys._MEIPASS) / "index" / "dataset_index.json"
                if bundled_index.exists():
                    try:
                        shutil.copy(str(bundled_index), str(self.paths["index"]))
                        print(f"Copied bundled index to {self.paths['index']}")
                    except Exception as e:
                        print(f"Failed to copy bundled index: {e}")
            
            # If still doesn't exist (copy failed or not frozen/bundled), create empty
            if not self.paths["index"].exists():
                with open(self.paths["index"], "w") as f:
                    json.dump({}, f)

        if not self.paths["logs"].exists():
            with open(self.paths["logs"], "w") as f:
                json.dump([], f)

    def get_file_hash(self, file_path: Path) -> str:
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def load_index(self) -> Dict:
        with open(self.paths["index"], "r") as f:
            return json.load(f)

    def save_index(self, index_data: Dict):
        with open(self.paths["index"], "w") as f:
            json.dump(index_data, f, indent=4)

    def log_action(self, action: Dict):
        with open(self.paths["logs"], "r") as f:
            logs = json.load(f)
        logs.append(action)
        with open(self.paths["logs"], "w") as f:
            json.dump(logs, f, indent=4)

    def scan_entrada(self) -> List[str]:
        """Returns list of image files in entrada that are not indexed."""
        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        files = []
        index = self.load_index()
        
        # Create a set of existing hashes to avoid duplicates if needed, 
        # but user said "if image already in index, don't reclassify".
        # We'll check by filename first for speed, then hash if needed? 
        # User said "timestamp and hash... to avoid reprocessing".
        # For now, let's just list files in entrada.
        
        for f in self.paths["entrada"].iterdir():
            if f.suffix.lower() in valid_extensions:
                files.append(str(f.name))
        return files

    def save_upload(self, file_storage, filename: str) -> str:
        """Saves an uploaded file to the entrada directory."""
        target_path = self.paths["entrada"] / filename
        file_storage.save(str(target_path))
        return str(target_path)

    def process_batch(self, items: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Process a batch of accepted images.
        items: list of {'filename': str, 'label': str}
        Returns stats of processed items.
        """
        processed = {"real": 0, "ia": 0, "errors": 0}
        
        index = self.load_index()
        
        for item in items:
            filename = item['filename']
            label = item['label']
            
            src = self.paths["entrada"] / filename
            if not src.exists():
                print(f"File not found: {filename}")
                processed["errors"] += 1
                continue
                
            dest_folder = self.paths[f"clasificaciones_{label}"]
            dest = dest_folder / filename
            
            try:
                # Calculate hash
                file_hash = self.get_file_hash(src)
                
                # Move file
                shutil.move(str(src), str(dest))
                
                # Update index
                entry = {
                    "path": str(dest),
                    "label": label,
                    "origin": "clasificaciones",
                    "timestamp": time.time(),
                    "hash": file_hash
                }
                index[file_hash] = entry
                
                # Log
                self.log_action({
                    "action": "accept",
                    "file": filename,
                    "destination": label,
                    "timestamp": time.time()
                })
                
                processed[label] += 1
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                processed["errors"] += 1
                
        self.save_index(index)
        return processed

    def get_dataset_files(self) -> Dict[str, List[str]]:
        """Returns all files for training (base + clasificaciones)"""
        data = {"real": [], "ia": []}
        
        # Base
        for f in self.paths["dataset_base_real"].iterdir():
            data["real"].append(str(f))
        for f in self.paths["dataset_base_ia"].iterdir():
            data["ia"].append(str(f))
            
        # Clasificaciones
        for f in self.paths["clasificaciones_real"].iterdir():
            data["real"].append(str(f))
        for f in self.paths["clasificaciones_ia"].iterdir():
            data["ia"].append(str(f))
            
        return data
