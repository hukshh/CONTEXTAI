import os
import threading
from typing import List
import logging

logger = logging.getLogger(__name__)

# Mac-specific stability fix for OpenMP
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

class EmbeddingService:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self._model = None
        self.dimension = 384
        self._lock = threading.Lock()

    @property
    def model(self):
        with self._lock:
            if self._model is None:
                logger.info(f"Loading/Downloading embedding model ({self.model_name})...")
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded successfully.")
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
