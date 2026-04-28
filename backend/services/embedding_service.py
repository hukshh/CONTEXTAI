import os
from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        # Using a popular, lightweight local model
        self.model_name = "all-MiniLM-L6-v2"
        self.model = SentenceTransformer(self.model_name)
        self.dimension = 384

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
