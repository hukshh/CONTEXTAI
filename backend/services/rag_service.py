import os
import fitz
import logging
from openai import OpenAI
from services.embedding_service import EmbeddingService
from services.retrieval_service import retrieval_service
from services.status_manager import status_manager
from utils.text_chunker import chunk_text
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from the backend folder
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)

class RAGService:
    def __init__(self):
        # Configure for Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not set. Chat features will fail.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        self.embedding_service = EmbeddingService()
        self.retrieval_service = retrieval_service
        self.model = "llama-3.3-70b-versatile" # Groq API model

    def process_document(self, file_path: str, filename: str) -> int:
        """
        Refactored highly-scalable document processing pipeline:
        1. Parse PDF page-by-page incrementally using PyMuPDF (fitz)
        2. Chunk page text incrementally
        3. Generate embeddings in batches of 32
        4. locked reload-add-save index
        5. Sync document to cloud storage if enabled
        Updates status dynamically at each step.
        """
        try:
            # 1. Initialize status
            status_manager.update_status(filename, "parsing", progress=0.0)
            
            # Clear existing version from vector index
            self.retrieval_service.delete_document(filename)
            
            # 2. Extract and Chunk Page-by-Page
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            if total_pages == 0:
                raise ValueError("PDF file is empty or corrupted")
                
            doc_chunks = []
            
            for i, page in enumerate(doc):
                # Parsing phase covers 0% to 40% progress
                progress = (i / total_pages) * 40.0
                status_manager.update_status(
                    filename, 
                    "parsing", 
                    progress=progress,
                    current_page=i + 1,
                    total_pages=total_pages
                )
                
                text = page.get_text()
                if not text.strip():
                    continue
                    
                page_chunks = chunk_text([{"text": text, "page_number": i + 1}], filename)
                if page_chunks:
                    doc_chunks.extend(page_chunks)
                    
            if not doc_chunks:
                raise ValueError("No readable text could be extracted from this PDF")
                
            # 3. Generate Embeddings in Batches (Covers 40% to 90% progress)
            all_embeddings = []
            batch_size = 32
            total_chunks = len(doc_chunks)
            
            for start_idx in range(0, total_chunks, batch_size):
                end_idx = min(start_idx + batch_size, total_chunks)
                progress = 40.0 + (start_idx / total_chunks) * 50.0
                status_manager.update_status(
                    filename, 
                    "embedding", 
                    progress=progress,
                    current_chunk=start_idx,
                    total_chunks=total_chunks
                )
                
                batch_chunks = doc_chunks[start_idx:end_idx]
                batch_texts = [c["text"] for c in batch_chunks]
                batch_embeddings = self.embedding_service.get_embeddings(batch_texts)
                all_embeddings.extend(batch_embeddings)
                
            # 4. Store in Vector Index (Covers 90% to 95% progress)
            status_manager.update_status(filename, "indexing", progress=90.0)
            self.retrieval_service.add_documents(all_embeddings, doc_chunks)
            
            # 5. Upload original document to cloud storage if enabled
            provider_type = os.getenv("STORAGE_PROVIDER", "local").lower().strip()
            if provider_type in ["s3", "supabase"]:
                status_manager.update_status(filename, "indexing", progress=95.0, message="Syncing document to cloud storage...")
                from services.storage_service import storage_service
                storage_service.upload_file(file_path, filename)
                
            # 6. Complete
            status_manager.update_status(filename, "ready", progress=100.0)
            logger.info(f"RAGService: Successfully ingested {filename} ({len(doc_chunks)} chunks).")
            return len(doc_chunks)
            
        except Exception as e:
            logger.error(f"RAGService: Error processing document {filename}: {e}", exc_info=True)
            status_manager.update_status(filename, "failed", error=str(e))
            return 0

    async def rewrite_query(self, query: str) -> str:
        """
        Uses LLM to expand short/vague queries into descriptive search queries.
        """
        if not self.client:
            return query
            
        prompt = f"""Rewrite the following user query to be a clear, detailed search query grounded in document context.
- If the query is short (e.g., "in detail", "more", "explain"), expand it (e.g., "Provide more details about the previous topic from the document").
- If the user asks for a "summary" or "overview", rewrite it as: "Provide a comprehensive overview of the main topics, key concepts, and important details discussed in the provided text."
Return ONLY the rewritten query text.

Original query: {query}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are a query expansion assistant."},
                         {"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error rewriting query: {e}")
            return query

    async def answer_question(self, question: str, selected_docs: list[str] = None):
        """
        Improved pipeline for query: Rewrite -> Embed -> Retrieve -> Generate
        """
        # 1. Detect if it's a summary request
        is_summary = any(word in question.lower() for word in ["summary", "summarize", "overview"])
        
        # 2. Rewrite query
        rewritten_query = await self.rewrite_query(question)
        
        # 3. Embed rewritten query
        import anyio
        query_embedding = await anyio.to_thread.run_sync(self.embedding_service.get_embedding, rewritten_query)
        
        # 4. Retrieve (Include filtering by selected_docs)
        k = 10 if is_summary else 5
        relevant_chunks = self.retrieval_service.search(query_embedding, k=k, selected_docs=selected_docs)
        
        if not relevant_chunks:
            if selected_docs:
                return {
                    "answer": f"No relevant information found in the selected documents: {', '.join(selected_docs)}.",
                    "sources": []
                }
            return {
                "answer": "I don't have any document context yet. Please upload a PDF and make sure it's selected!",
                "sources": []
            }
            
        # Combine context structure for LLM
        context = "\n---\n".join([f"[Source: {c['document_name']}, Page: {c['page_number']}]\n{c['text']}" for c in relevant_chunks])
        
        if not self.client:
            return {
                "answer": "Groq API key is missing. Please set it in the backend/.env file to enable chat features.",
                "sources": []
            }

        # 6. Generate response
        prompt = f"""Answer the question using the provided context below.

- If the user asks for a summary, use the provided context fragments to give a comprehensive overview of the topics mentioned.
- provide a detailed and helpful response based on the available information.
- If the answer is partially available, provide the best possible response from the context.
- ONLY say 'Not fully available in document' if the context is completely irrelevant to the question.

Context:
{context}

Question:
{rewritten_query}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful document assistant. You prioritize accuracy and context grounding."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            answer = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            return {"error": "LLM request failed"}
        
        # Extract top unique sources with cleaned snippets
        source_list = []
        seen_pages = set()
        
        for c in relevant_chunks:
            page_key = f"{c['document_name']}_{c['page_number']}"
            if page_key not in seen_pages:
                text = " ".join(c['text'].split())
                limit = 140
                if len(text) > limit:
                    snippet = text[:limit].rsplit(' ', 1)[0] + "..."
                else:
                    snippet = text
                
                # Remove UUID prefix (32 hex chars + underscore = 33 chars)
                doc_name = c['document_name']
                if len(doc_name) > 33 and doc_name[32] == '_':
                    doc_name = doc_name[33:]
                
                source_list.append({
                    "document": doc_name,
                    "page": c['page_number'],
                    "snippet": snippet
                })
                seen_pages.add(page_key)
            
            if len(source_list) >= 3:
                break
        
        return {
            "answer": answer,
            "sources": source_list,
            "rewritten_query": rewritten_query
        }

    def delete_file(self, filename: str) -> bool:
        """Removes file from storage, local cache, and vector store."""
        # 1. Remove from vector store
        deleted_from_store = self.retrieval_service.delete_document(filename)
        
        # 2. Delete from cloud storage if enabled
        from services.storage_service import storage_service
        deleted_from_storage = storage_service.delete_file(filename)
        
        # 3. Remove local file
        base_path = os.getenv("BASE_PATH", "./data")
        file_path = os.path.join(base_path, "uploads", filename)
        deleted_from_disk = False
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_from_disk = True
            except OSError:
                pass
                
        return deleted_from_store or deleted_from_storage or deleted_from_disk

    def clear_all(self):
        """Resets the entire system."""
        # 1. Reset vector store
        self.retrieval_service.clear_all()
        
        # 2. Clear local uploads folder and cloud files
        from services.storage_service import storage_service
        
        base_path = os.getenv("BASE_PATH", "./data")
        uploads_dir = os.path.join(base_path, "uploads")
        if os.path.exists(uploads_dir):
            for f in os.listdir(uploads_dir):
                if f.startswith("."):
                    continue
                storage_service.delete_file(f)
                try:
                    os.remove(os.path.join(uploads_dir, f))
                except OSError:
                    pass
        return True

rag_service = RAGService()
