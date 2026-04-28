import os
from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self._model = None
        self.dimension = 384

    @property
    def model(self):
        if self._model is None:
            print(f"Loading/Downloading embedding model ({self.model_name})... This may take a moment on the first run.")
            self._model = SentenceTransformer(self.model_name)
            print("Embedding model loaded successfully.")
        return self._model

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Converts a list of texts into embedding vectors locally.
        """
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def get_embedding(self, text: str) -> List[float]:
        """
        Converts a single text into an embedding vector.
        """
        return self.get_embeddings([text])[0]
