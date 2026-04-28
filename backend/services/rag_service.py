import os
from openai import OpenAI
from backend.services.embedding_service import EmbeddingService
from backend.services.retrieval_service import retrieval_service
from backend.utils.pdf_loader import extract_text_from_pdf
from backend.utils.text_chunker import chunk_text
from dotenv import load_dotenv

# Load environment variables from the backend folder
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)

class RAGService:
    def __init__(self):
        # Configure for Groq (OpenAI-compatible)
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("WARNING: GROQ_API_KEY not set. Chat features will fail.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        self.embedding_service = EmbeddingService()
        self.retrieval_service = retrieval_service
        self.model = "llama-3.3-70b-versatile" # High-performance Groq model

    async def process_document(self, file_path: str, filename: str):
        """
        Full pipeline for document processing: Load -> Chunk -> Embed -> Store
        """
        # 1. Extract
        pages_content = extract_text_from_pdf(file_path)
        
        # 2. Chunk
        chunks = chunk_text(pages_content, filename)
        
        # 3. Embed
        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_service.get_embeddings(texts)
        
        # 4. Store
        self.retrieval_service.add_documents(embeddings, chunks)
        
        return len(chunks)

    async def rewrite_query(self, query: str) -> str:
        """
        Uses LLM to expand short/vague queries into descriptive search queries.
        """
        if not self.client:
            return query
            
        prompt = f"""Rewrite the following user query to be a clear, detailed search query grounded in document context.
If the query is short (e.g., "in detail", "more", "explain"), expand it appropriately (e.g., "Provide more details about the previous topic from the document").
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
            print(f"Error rewriting query: {e}")
            return query

    async def answer_question(self, question: str):
        """
        Improved pipeline for query: Rewrite -> Embed -> Retrieve -> Generate
        """
        # 1. Rewrite query for better retrieval
        rewritten_query = await self.rewrite_query(question)
        
        # 2. Embed rewritten query
        query_embedding = self.embedding_service.get_embedding(rewritten_query)
        
        # 3. Retrieve (top-k=5)
        relevant_chunks = self.retrieval_service.search(query_embedding, k=5)
        
        if not relevant_chunks:
            return {
                "answer": "No documents uploaded yet. Please upload a PDF first.",
                "sources": []
            }

        # 4. Combine context structure
        context = "\n---\n".join([f"[Source: {c['document_name']}, Page: {c['page_number']}]\n{c['text']}" for c in relevant_chunks])
        
        if not self.client:
            return {
                "answer": "Grok API key is missing. Please set it in the backend/.env file to enable chat features.",
                "sources": []
            }

        # 5. Generate response with balanced grounding and helpfulness
        prompt = f"""Answer the question using ONLY the provided context below.

- If the full answer is available, provide a complete and detailed response.
- If only partial information is available, provide the best possible answer based on the context and clearly mention that the information is incomplete.
- If no relevant information is found in the context at all, only then say: 'Not fully available in document.'

Context:
{context}

Question:
{rewritten_query}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful document assistant. You prioritize accuracy and context grounding, but you provide partial information if it helps answer the query."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            answer = response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            answer = f"Error calling LLM API: {str(e)}"
        
        # Extract sources
        sources = list(set([c["document_name"] for c in relevant_chunks]))
        
        return {
            "answer": answer,
            "sources": sources,
            "rewritten_query": rewritten_query # Included for transparency
        }

rag_service = RAGService()
