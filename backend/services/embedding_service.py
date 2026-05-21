import logging
from typing import List
import os

logger = logging.getLogger(__name__)

# Model is baked into the Docker image at /root/.cache/fastembed
# For local dev it auto-downloads once and caches in ~/.cache/fastembed
FASTEMBED_CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR", None)


class EmbeddingService:
    def __init__(self):
        from fastembed import TextEmbedding
        self.model_name = "BAAI/bge-small-en-v1.5"
        self.dimension = 384  # bge-small-en-v1.5 outputs 384-dim vectors
        logger.info(f"Initializing embedding model: {self.model_name}")
        kwargs = {"model_name": self.model_name}
        if FASTEMBED_CACHE_DIR:
            kwargs["cache_dir"] = FASTEMBED_CACHE_DIR
        self._model = TextEmbedding(**kwargs)
        logger.info("Embedding model ready.")

    def get_embeddings(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """
        Converts a list of texts into embedding vectors locally via fastembed.
        fastembed uses a lightweight ONNX runtime (~60MB), not PyTorch (~2GB).
        Total embedding stack: ~130MB vs ~2.5GB for sentence-transformers+torch.
        """
        if not texts:
            return []
        embeddings_iter = self._model.embed(texts, batch_size=batch_size)
        return [e.tolist() for e in embeddings_iter]

    def get_embedding(self, text: str) -> List[float]:
        """Converts a single text into an embedding vector."""
        return self.get_embeddings([text])[0]
