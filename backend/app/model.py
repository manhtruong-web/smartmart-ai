"""Mô hình trích xuất đặc trưng ảnh dùng ResNet18 đã huấn luyện trước."""

from functools import lru_cache

import numpy as np
import torch
from PIL import Image
from torchvision.models import ResNet18_Weights, resnet18


@lru_cache(maxsize=1)
def get_feature_model():
    weights = ResNet18_Weights.DEFAULT
    model = resnet18(weights=weights)
    model.fc = torch.nn.Identity()
    model.eval()
    return model, weights.transforms()


def extract_feature(image: Image.Image) -> np.ndarray:
    model, transform = get_feature_model()
    tensor = transform(image.convert("RGB")).unsqueeze(0)
    with torch.inference_mode():
        vector = model(tensor).squeeze(0).numpy().astype("float32")
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector
