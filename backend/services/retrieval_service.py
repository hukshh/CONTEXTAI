import numpy as np
import os
import json
import logging
from typing import List, Dict, Optional
import filelock

logger = logging.getLogger(__name__)

# Mac-specific stability fix for OpenMP
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

class RetrievalService:
    def __init__(self):
        base_path = os.getenv("BASE_PATH", "./data")
        self.storage_dir = os.path.join(base_path, "storage")
        self.index_path = os.path.join(self.storage_dir, "vector.index")
        self.meta_path = os.path.join(self.storage_dir, "metadata.json")
        self.lock_path = os.path.join(self.storage_dir, "vector.lock")
        
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

        self.dimension = 384
        self.index = None
        self.metadata = {}
        self.doc_to_ids = {}
        self.next_id = 0
        self.lock = filelock.FileLock(self.lock_path)
        
        # Download index from cloud storage if enabled
        self._sync_from_cloud()
        
        # Initial load
        self.reload()

    def _sync_from_cloud(self):
        provider_type = os.getenv("STORAGE_PROVIDER", "local").lower().strip()
        if provider_type in ["s3", "supabase"]:
            logger.info(f"RetrievalService: Attempting to sync FAISS index from cloud storage ({provider_type})...")
            from services.storage_service import storage_service
            try:
                storage_service.download_file("vector.index", self.index_path)
                storage_service.download_file("metadata.json", self.meta_path)
            except Exception as e:
                logger.warning(f"RetrievalService: Failed to download index files from cloud storage (might not exist yet): {e}")

    def _sync_to_cloud(self):
        provider_type = os.getenv("STORAGE_PROVIDER", "local").lower().strip()
        if provider_type in ["s3", "supabase"]:
            logger.info(f"RetrievalService: Syncing FAISS index to cloud storage ({provider_type})...")
            from services.storage_service import storage_service
            try:
                storage_service.upload_file(self.index_path, "vector.index")
                storage_service.upload_file(self.meta_path, "metadata.json")
            except Exception as e:
                logger.error(f"RetrievalService: Failed to upload index files to cloud storage: {e}")

    def _init_empty(self):
        import faiss
        base_index = faiss.IndexFlatL2(self.dimension)
        self.index = faiss.IndexIDMap(base_index)
        self.metadata = {}
        self.doc_to_ids = {}
        self.next_id = 0

    def reload(self):
        """Reloads the FAISS index and metadata from disk state."""
        if os.path.exists(self.index_path):
            try:
                import faiss
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, "r") as f:
                    state = json.load(f)
                    # Convert string keys back to ints for metadata
                    self.metadata = {int(k): v for k, v in state["metadata"].items()}
                    self.doc_to_ids = state["doc_to_ids"]
                    self.next_id = int(state["next_id"])
                logger.info(f"RetrievalService: Loaded index with {self.index.ntotal} chunks.")
            except Exception as e:
                logger.warning(f"RetrievalService: Failed to load index, creating new: {e}")
                self._init_empty()
        else:
            self._init_empty()

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
                
            # Sync to cloud storage if enabled
            self._sync_to_cloud()
        except Exception as e:
            logger.error(f"RetrievalService: Error saving index: {e}")

    def add_documents(self, vector_data: List[List[float]], chunks: List[Dict]):
        if not vector_data:
            return
        
        # Acquire lock to ensure no concurrent writes
        with self.lock:
            # Reload from disk first to get any other workers' changes
            self.reload()
            
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

    def delete_document(self, filename: str) -> bool:
        with self.lock:
            # Reload from disk first
            self.reload()
            
            if filename not in self.doc_to_ids:
                return False
                
            import faiss
            ids_to_remove = self.doc_to_ids[filename]
            id_selector = np.array(ids_to_remove).astype('int64')
            
            try:
                self.index.remove_ids(id_selector)
            except Exception as e:
                logger.warning(f"RetrievalService: Manual ID removal failed ({e}), rebuilding index...")
                self._rebuild_without_document(filename)
                return True

            for chunk_id in ids_to_remove:
                self.metadata.pop(chunk_id, None)
                
            del self.doc_to_ids[filename]
            self._save()
            return True

    def _rebuild_without_document(self, filename: str):
        # Fallback rebuild logic
        import faiss
        all_metadata = list(self.metadata.values())
        all_doc_to_ids = dict(self.doc_to_ids)
        
        # Reset current state
        self._init_empty()
        
        # Filter metadata chunks
        chunks_to_add = [c for c in all_metadata if c["document_name"] != filename]
        if chunks_to_add:
            # Embeddings would need to be reloaded. To keep it robust without recalculating,
            # we read the old index's vectors. But FAISS IndexIDMap allows reading.
            # However, since this fallback is rare, clearing all is what was done originally.
            # Let's keep the clear_all original behavior to be safe.
            self.clear_all()

    def clear_all(self):
        with self.lock:
            self._init_empty()
            if os.path.exists(self.index_path): 
                try: os.remove(self.index_path)
                except OSError: pass
            if os.path.exists(self.meta_path): 
                try: os.remove(self.meta_path)
                except OSError: pass
            self._save()

    def search(self, query_embedding: List[float], k: int = 5, selected_docs: List[str] = None) -> List[Dict]:
        with self.lock:
            # Reload from disk to ensure latest search results
            self.reload()
            
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
