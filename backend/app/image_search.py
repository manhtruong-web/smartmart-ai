"""Đọc metadata FAISS và tìm ảnh gần nhất."""

import json
from pathlib import Path

import faiss
import numpy as np

from .model import extract_feature


class ImageIndex:
    def __init__(self, index_dir: Path):
        self.index_path = index_dir / "products.index"
        self.metadata_path = index_dir / "metadata.json"
        self.index = faiss.read_index(str(self.index_path)) if self.index_path.exists() else None
        self.metadata = (
            json.loads(self.metadata_path.read_text(encoding="utf-8"))
            if self.metadata_path.exists()
            else []
        )

    def search(self, image, top_k: int) -> list[dict]:
        if self.index is None or not self.metadata:
            raise RuntimeError("Chưa có FAISS index. Hãy chạy scripts/build_index.py trước.")
        query = np.expand_dims(extract_feature(image), axis=0)
        scores, indexes = self.index.search(query, min(top_k, self.index.ntotal))
        return [
            {**self.metadata[int(index)], "similarity": round(float(score), 4)}
            for score, index in zip(scores[0], indexes[0])
            if index >= 0
        ]
