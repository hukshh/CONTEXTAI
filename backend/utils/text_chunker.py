import tiktoken
from typing import List, Dict

def chunk_text(pages_content: List[Dict], doc_name: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """
    Splits text into chunks with metadata.
    """
    tokenizer = tiktoken.get_encoding("cl100k_base")
    chunks = []
    
    for page in pages_content:
        text = page["text"]
        page_num = page["page_number"]
        
        tokens = tokenizer.encode(text)
        
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk_tokens = tokens[i : i + chunk_size]
            chunk_text = tokenizer.decode(chunk_tokens)
            
            chunks.append({
                "text": chunk_text,
                "document_name": doc_name,
                "page_number": page_num
            })
            
    return chunks
