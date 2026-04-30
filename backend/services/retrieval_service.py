import numpy as np
import os
import json
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        base_path = os.getenv("BASE_PATH", "./data")
        self.storage_dir = os.path.join(base_path, "storage")
        self.index_path = os.path.join(self.storage_dir, "vector.index")
        self.meta_path = os.path.join(self.storage_dir, "metadata.json")
        
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

        self.dimension = 384  # BGE-small-en-v1.5 via fastembed
        self.index = None
        self.metadata = {}
        self.doc_to_ids = {}
        self.next_id = 0
        
        # Load or create index
        if os.path.exists(self.index_path):
            try:
                import faiss
                loaded_index = faiss.read_index(self.index_path)

                # Safety: reset if stored index dimension doesn't match current dimension
                if loaded_index.d != self.dimension:
                    logger.warning(
                        f"Stored index dimension ({loaded_index.d}) != current dimension "
                        f"({self.dimension}). Resetting index."
                    )
                    self._init_empty()
                else:
                    self.index = loaded_index
                    with open(self.meta_path, "r") as f:
                        state = json.load(f)
                        # Convert string keys back to ints for metadata
                        self.metadata = {int(k): v for k, v in state["metadata"].items()}
                        self.doc_to_ids = state["doc_to_ids"]
                        self.next_id = int(state["next_id"])
                    logger.info(f"Loaded existing index with {self.index.ntotal} chunks.")
            except Exception as e:
                logger.warning(f"Failed to load index, creating new: {e}")
                self._init_empty()
        else:
            self._init_empty()

    def _init_empty(self):
        import faiss
        base_index = faiss.IndexFlatL2(self.dimension)
        self.index = faiss.IndexIDMap(base_index)
        self.metadata = {}
        self.doc_to_ids = {}
        self.next_id = 0

    def _save(self):
        try:
            import faiss
            faiss.write_index(self.index, self.index_path)
            # Ensure keys are strings for JSON
            serializable_meta = {str(k): v for k, v in self.metadata.items()}
            # Ensure IDs are standard ints
            serializable_doc_to_ids = {k: [int(x) for x in v] for k, v in self.doc_to_ids.items()}
            
            state = {
                "metadata": serializable_meta,
                "doc_to_ids": serializable_doc_to_ids,
                "next_id": int(self.next_id)
            }
            with open(self.meta_path, "w") as f:
                json.dump(state, f)
        except Exception as e:
            logger.error(f"Error saving index: {e}")

    def add_documents(self, vector_data: List[List[float]], chunks: List[Dict]):
        if not vector_data:
            return
        
        import faiss
        vector_data = np.array(vector_data).astype('float32')
        start_id = int(self.next_id)
        ids = np.array(range(start_id, start_id + len(chunks))).astype('int64')
        
        self.index.add_with_ids(vector_data, ids)
        
        doc_name = chunks[0]["document_name"]
        if doc_name not in self.doc_to_ids:
            self.doc_to_ids[doc_name] = []
            
        for i, chunk in enumerate(chunks):
            chunk_id = int(ids[i])
            self.metadata[chunk_id] = chunk
            self.doc_to_ids[doc_name].append(chunk_id)
            
        self.next_id = start_id + len(chunks)
        self._save()

    def delete_document(self, filename: str):
        if filename not in self.doc_to_ids:
            return False
            
        import faiss
        ids_to_remove = self.doc_to_ids[filename]
        id_selector = np.array(ids_to_remove).astype('int64')
        
        try:
            self.index.remove_ids(id_selector)
        except Exception as e:
            logger.warning(f"Warning: Manual ID removal failed ({e}), rebuilding index...")
            # Fallback for indices that don't support direct removal
            self.clear_all()
            return True

        for chunk_id in ids_to_remove:
            self.metadata.pop(chunk_id, None)
            
        del self.doc_to_ids[filename]
        self._save()
        return True

    def clear_all(self):
        self._init_empty()
        if os.path.exists(self.index_path): os.remove(self.index_path)
        if os.path.exists(self.meta_path): os.remove(self.meta_path)
        self._save()

    def search(self, query_embedding: List[float], k: int = 5, selected_docs: List[str] = None) -> List[Dict]:
        if self.index.ntotal == 0:
            return []
        
        import faiss
        vector_query = np.array([query_embedding]).astype('float32')
        search_k = k * 20 if selected_docs else k
        distances, ids = self.index.search(vector_query, min(search_k, self.index.ntotal))
        
        results = []
        for chunk_id in ids[0]:
            if chunk_id != -1:
                chunk = self.metadata.get(int(chunk_id))
                if chunk:
                    if not selected_docs or chunk["document_name"] in selected_docs:
                        results.append(chunk)
        
        return results[:k]

retrieval_service = RetrievalService()
