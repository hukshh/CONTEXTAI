import os
from openai import OpenAI
from services.embedding_service import EmbeddingService
from services.retrieval_service import retrieval_service
from utils.pdf_loader import extract_text_from_pdf
from utils.text_chunker import chunk_text
from dotenv import load_dotenv
import logging

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

    def process_document(self, file_path: str, filename: str):
        """
        Full pipeline for document processing: Load -> Chunk -> Embed -> Store
        Runs in a background thread to avoid blocking the event loop.
        """
        try:
            # 1. Clear existing version
            self.retrieval_service.delete_document(filename)
            
            # 2. Extract
            logger.info(f"Extracting text from {filename}...")
            pages_content = extract_text_from_pdf(file_path)
            
            # 3. Chunk
            logger.info(f"Chunking text for {filename}...")
            chunks = chunk_text(pages_content, filename)
            
            if not chunks:
                logger.warning(f"No text extracted from {filename}")
                return 0
                
            # 4. Embed
            texts = [c["text"] for c in chunks]
            logger.info(f"Generating embeddings for {len(texts)} chunks of {filename}...")
            embeddings = self.embedding_service.get_embeddings(texts)
            
            # 5. Store
            logger.info(f"Storing {len(chunks)} chunks in vector database for {filename}...")
            self.retrieval_service.add_documents(embeddings, chunks)
            
            logger.info(f"Success: Processed {filename} ({len(chunks)} chunks)")
            return len(chunks)
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            return 0

    async def rewrite_query(self, query: str) -> str:
        """
        Uses LLM to expand short/vague queries into descriptive search queries.
        Returns 'GIBBERISH_INPUT' sentinel if the query is meaningless.
        """
        if not self.client:
            return query
            
        prompt = f"""You are a query expansion assistant for a document Q&A system.

Rules:
- If the query is a real question or topic, rewrite it as a clear, detailed search query.
- If the query is short but meaningful (e.g., "more", "explain"), expand it to "Provide more details about the previous topic from the document".
- If the query asks for a "summary" or "overview", rewrite it as: "Provide a comprehensive overview of the main topics, key concepts, and important details discussed in the provided text."
- If the query is random characters, gibberish, keyboard smashing, or completely meaningless (e.g., "sdfghjkl", "asdfgh", "qwerty", "zxcvbn"), return ONLY the exact text: GIBBERISH_INPUT

Return ONLY the rewritten query text, or GIBBERISH_INPUT if meaningless.

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
        Full RAG pipeline: Validate -> Rewrite -> Embed -> Retrieve -> Generate
        """
        # 1. Fast local gibberish check before any API call
        #    If the input has no recognisable words (all chars are consonant clusters
        #    with no spaces or vowels), reject immediately.
        stripped = question.strip()
        words = stripped.split()
        VOWELS = set("aeiouAEIOU")
        real_words = [w for w in words if any(c in VOWELS for c in w) or len(w) <= 2]
        if len(words) > 0 and len(real_words) == 0:
            return {
                "answer": "Your message doesn't seem to contain a recognisable question. Please type something meaningful and try again.",
                "sources": []
            }

        # 2. Detect if it's a summary request
        is_summary = any(word in question.lower() for word in ["summary", "summarize", "overview"])
        
        # 3. Rewrite query (LLM-assisted expansion)
        rewritten_query = await self.rewrite_query(question)

        # Check if the LLM flagged the input as gibberish
        if rewritten_query == "GIBBERISH_INPUT":
            return {
                "answer": "Your message doesn't seem to contain a recognisable question. Please type something meaningful and try again.",
                "sources": []
            }
        
        # 3. Embed rewritten query (Run in thread to avoid blocking event loop)
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

    def delete_file(self, filename: str):
        """Removes file from disk and vector store."""
        # 1. Remove from vector store
        deleted_from_store = self.retrieval_service.delete_document(filename)
        
        # 2. Remove from disk
        base_path = os.getenv("BASE_PATH", "./data")
        file_path = os.path.join(base_path, "uploads", filename)
        deleted_from_disk = False
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_from_disk = True
            except OSError:
                pass
                
        return deleted_from_store or deleted_from_disk

    def clear_all(self):
        """Resets the entire system."""
        # 1. Reset vector store
        self.retrieval_service.clear_all()
        
        # 2. Clear uploads folder
        base_path = os.getenv("BASE_PATH", "./data")
        uploads_dir = os.path.join(base_path, "uploads")
        if os.path.exists(uploads_dir):
            for f in os.listdir(uploads_dir):
                os.remove(os.path.join(uploads_dir, f))
        return True

rag_service = RAGService()
