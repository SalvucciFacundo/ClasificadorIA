import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class SubclassifierManager:
    """Manages subclassification of 'Real' images into specific categories"""
    
    CATEGORIES = [
        'asiaticas',
        'bimbo',
        'castanas',
        'colores',
        'grupo',
        'lenceria',
        'morenas',
        'morochas',
        'otros',
        'pelirrojas',
        'rubias'
    ]
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.source_dir = self.base_dir / "clasificaciones" / "real"
        self.target_base_dir = self.base_dir / "subclasificadas" / "reales"
        self.index_file = self.base_dir / "index" / "subclassification_index.json"
        
        # Create directory structure
        self._create_directories()
        
    def _create_directories(self):
        """Create all necessary directories for subclassification"""
        self.target_base_dir.mkdir(parents=True, exist_ok=True)
        
        for category in self.CATEGORIES:
            category_dir = self.target_base_dir / category
            category_dir.mkdir(exist_ok=True)
        
        # Ensure index directory exists
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        
    def load_index(self) -> Dict:
        """Load subclassification index"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_index(self, index: Dict):
        """Save subclassification index"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def scan_source_images(self) -> List[str]:
        """Scan images in clasificaciones/real folder"""
        if not self.source_dir.exists():
            return []
        
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        images = []
        
        for file in self.source_dir.iterdir():
            if file.is_file() and file.suffix.lower() in valid_extensions:
                images.append(file.name)
        
        return sorted(images)
    
    def predict_category(self, image_path: str) -> Dict:
        """
        Predict category for an image.
        For now, returns a placeholder. Will be replaced with actual ML model.
        """
        # TODO: Implement actual ML prediction per category
        # For now, return a default prediction
        return {
            "category": "otros",  # Default category
            "confidence": 0.5
        }
    
    def move_to_category(self, filename: str, category: str) -> bool:
        """Move image from source to target category folder"""
        if category not in self.CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        
        source_path = self.source_dir / filename
        target_path = self.target_base_dir / category / filename
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {filename}")
        
        # Move file
        shutil.move(str(source_path), str(target_path))
        
        # Update index
        index = self.load_index()
        index[filename] = {
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "source": "clasificaciones/real"
        }
        self.save_index(index)
        
        return True
    
    def process_batch(self, items: List[Dict]) -> Dict:
        """
        Process a batch of subclassification items.
        items: [{"filename": "img.jpg", "category": "rubias"}, ...]
        """
        stats = {category: 0 for category in self.CATEGORIES}
        errors = []
        
        for item in items:
            filename = item.get('filename')
            category = item.get('category')
            
            try:
                self.move_to_category(filename, category)
                stats[category] += 1
            except Exception as e:
                errors.append(f"Error processing {filename}: {str(e)}")
        
        return {
            "stats": stats,
            "errors": errors,
            "total_processed": sum(stats.values())
        }
    
    def get_category_stats(self) -> Dict:
        """Get statistics for each category"""
        stats = {}
        
        for category in self.CATEGORIES:
            category_dir = self.target_base_dir / category
            if category_dir.exists():
                count = len([f for f in category_dir.iterdir() if f.is_file()])
                stats[category] = count
            else:
                stats[category] = 0
        
        # Count pending images in source
        stats['pending'] = len(self.scan_source_images())
        
        return stats
    
    def get_images_for_ui(self) -> List[Dict]:
        """Get images with predictions for UI display"""
        images = self.scan_source_images()
        results = []
        
        for img in images:
            img_path = self.source_dir / img
            prediction = self.predict_category(str(img_path))
            
            results.append({
                "filename": img,
                "prediction": prediction,
                "url": f"/images/clasificaciones/real/{img}"
            })
        
        return results
    
    def remove_image(self, filename: str) -> bool:
        """Remove an image from the source folder"""
        source_path = self.source_dir / filename
        
        if not source_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        os.remove(source_path)
        return True
