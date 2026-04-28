import faiss
import numpy as np
from typing import List, Dict

class RetrievalService:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = [] # Stores chunk text and other metadata

    def add_documents(self, embeddings: List[List[float]], chunks: List[Dict]):
        """
        Adds embeddings and their corresponding chunks to the vector store.
        """
        vector_data = np.array(embeddings).astype('float32')
        self.index.add(vector_data)
        self.metadata.extend(chunks)

    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """
        Searches for the top-k most similar chunks.
        """
        if self.index.ntotal == 0:
            return []
            
        vector_query = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(vector_query, k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.metadata):
                results.append(self.metadata[idx])
                
        return results

# Singleton instance to persist in memory
retrieval_service = RetrievalService()
