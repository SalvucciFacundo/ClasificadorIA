import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models, transforms, datasets
from torch.utils.data import DataLoader, Dataset
from PIL import Image
import os
from pathlib import Path
from typing import List, Dict

class CustomDataset(Dataset):
    def __init__(self, file_list, labels, transform=None):
        self.file_list = file_list
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        img_path = self.file_list[idx]
        image = Image.open(img_path).convert("RGB")
        label = self.labels[idx]
        if self.transform:
            image = self.transform(image)
        return image, label

class ModelManager:
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.model = self._load_model()

    def _load_model(self):
        model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        num_ftrs = model.fc.in_features
        model.fc = nn.Linear(num_ftrs, 2)  # 2 classes: IA vs Real
        
        if self.model_path.exists():
            try:
                state_dict = torch.load(self.model_path, map_location=self.device)
                model.load_state_dict(state_dict)
                print(f"Model loaded from {self.model_path}")
            except Exception as e:
                print(f"Failed to load model: {e}. Starting fresh.")
        
        model = model.to(self.device)
        model.eval()
        return model

    def save_model(self):
        torch.save(self.model.state_dict(), self.model_path)
        print(f"Model saved to {self.model_path}")

    def predict(self, image_path: str) -> Dict:
        try:
            image = Image.open(image_path).convert("RGB")
            image = self.transform(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(image)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted = torch.max(probabilities, 1)
                
            label = "ia" if predicted.item() == 0 else "real" # Assuming 0=IA, 1=Real. Need to standardize this.
            # Let's standardize: 0 = IA, 1 = Real
            
            return {
                "label": label,
                "confidence": float(confidence.item())
            }
        except Exception as e:
            print(f"Error predicting {image_path}: {e}")
            return {"label": "error", "confidence": 0.0}

    def train(self, data_files: Dict[str, List[str]], epochs=5):
        """
        data_files: {'real': [paths], 'ia': [paths]}
        """
        self.model.train()
        
        # Prepare data
        files = data_files['ia'] + data_files['real']
        # 0 for IA, 1 for Real
        labels = [0] * len(data_files['ia']) + [1] * len(data_files['real'])
        
        if not files:
            print("No data to train on.")
            return {}

        dataset = CustomDataset(files, labels, self.transform)
        dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(self.model.parameters(), lr=0.001, momentum=0.9)
        
        metrics = {"accuracy": 0, "loss": 0}
        
        for epoch in range(epochs):
            running_loss = 0.0
            correct = 0
            total = 0
            
            for inputs, labels_batch in dataloader:
                inputs, labels_batch = inputs.to(self.device), labels_batch.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = criterion(outputs, labels_batch)
                loss.backward()
                optimizer.step()
                
                running_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels_batch.size(0)
                correct += (predicted == labels_batch).sum().item()
            
            epoch_acc = 100 * correct / total
            epoch_loss = running_loss / len(dataloader)
            print(f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f} - Acc: {epoch_acc:.2f}%")
            metrics = {"accuracy": epoch_acc, "loss": epoch_loss}

        self.save_model()
        self.model.eval()
        return metrics
