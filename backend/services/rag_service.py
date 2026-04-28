import os
from openai import OpenAI
from backend.services.embedding_service import EmbeddingService
from backend.services.retrieval_service import retrieval_service
from backend.utils.pdf_loader import extract_text_from_pdf
from backend.utils.text_chunker import chunk_text
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        # Configure for xAI (Grok)
        api_key = os.getenv("XAI_API_KEY")
        if not api_key or api_key == "your_key_here":
            print("WARNING: XAI_API_KEY not set. Chat features will fail.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
        self.embedding_service = EmbeddingService()
        self.retrieval_service = retrieval_service
        self.model = "grok-beta" # xAI Model

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

    async def answer_question(self, question: str):
        """
        Full pipeline for query: Embed -> Retrieve -> Generate
        """
        # 1. Embed query
        query_embedding = self.embedding_service.get_embedding(question)
        
        # 2. Retrieve
        relevant_chunks = self.retrieval_service.search(query_embedding, k=5)
        
        if not relevant_chunks:
            return {
                "answer": "No documents uploaded yet. Please upload a PDF first.",
                "sources": []
            }

        # 3. Combine context
        context = "\n---\n".join([c["text"] for c in relevant_chunks])
        
        if not self.client:
            return {
                "answer": "Grok API key is missing. Please set it in the backend/.env file to enable chat features.",
                "sources": []
            }

        # 4. Generate response
        prompt = f"""Answer the question ONLY using the context below.
If the answer is not present, say 'Not found in document'.

Context:
{context}

Question:
{question}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that answers questions based on provided documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            answer = response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Grok API: {e}")
            answer = f"Error calling Grok API: {str(e)}"
        
        # Extract sources
        sources = list(set([c["document_name"] for c in relevant_chunks]))
        
        return {
            "answer": answer,
            "sources": sources
        }

rag_service = RAGService()
