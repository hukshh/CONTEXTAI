import faiss
import numpy as np
from typing import List, Dict

class RetrievalService:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        # Use IndexIDMap to support efficient removal by ID
        self.base_index = faiss.IndexFlatL2(dimension)
        self.index = faiss.IndexIDMap(self.base_index)
        self.metadata = {} # Maps unique_id -> chunk
        self.doc_to_ids = {} # Maps filename -> list of unique_ids
        self.next_id = 0

    def add_documents(self, embeddings: List[List[float]], chunks: List[Dict]):
        """
        Adds embeddings with unique IDs to the vector store.
        """
        if not chunks:
            return
            
        doc_name = chunks[0]["document_name"]
        
        # Generate unique IDs for these chunks
        start_id = self.next_id
        ids = np.array(range(start_id, start_id + len(chunks))).astype('int64')
        self.next_id += len(chunks)
        
        # Add to FAISS
        vector_data = np.array(embeddings).astype('float32')
        self.index.add_with_ids(vector_data, ids)
        
        # Store metadata and track IDs for this document
        for i, chunk_id in enumerate(ids):
            self.metadata[int(chunk_id)] = chunks[i]
            
        if doc_name not in self.doc_to_ids:
            self.doc_to_ids[doc_name] = []
        self.doc_to_ids[doc_name].extend(ids.tolist())

    def search(self, query_embedding: List[float], k: int = 5, selected_docs: List[str] = None) -> List[Dict]:
        """
        Searches for the top-k most similar chunks using ID mapping.
        """
        if self.index.ntotal == 0:
            return []
            
        vector_query = np.array([query_embedding]).astype('float32')
        
        # We retrieve more than k to handle filtering by selected_docs
        search_k = k * 20 if selected_docs else k
        distances, ids = self.index.search(vector_query, search_k)
        
        results = []
        for chunk_id in ids[0]:
            if chunk_id != -1:
                chunk = self.metadata.get(int(chunk_id))
                if chunk:
                    if not selected_docs or chunk["document_name"] in selected_docs:
                        results.append(chunk)
            
            if len(results) >= k:
                break
                
        return results

    def delete_document(self, filename: str):
        """
        Fast deletion using IndexIDMap.remove_ids. No rebuilding required.
        """
        if filename not in self.doc_to_ids:
            return False
            
        ids_to_remove = self.doc_to_ids[filename]
        
        # 1. Remove from FAISS index
        id_selector = np.array(ids_to_remove).astype('int64')
        self.index.remove_ids(id_selector)
        
        # 2. Remove from metadata dictionary
        for chunk_id in ids_to_remove:
            if chunk_id in self.metadata:
                del self.metadata[chunk_id]
        
        # 3. Clear from doc_to_ids mapping
        del self.doc_to_ids[filename]
        
        return True

    def clear_all(self):
        """
        Resets the entire vector store.
        """
        self.base_index = faiss.IndexFlatL2(self.dimension)
        self.index = faiss.IndexIDMap(self.base_index)
        self.metadata = {}
        self.doc_to_ids = {}
        self.next_id = 0

retrieval_service = RetrievalService()
