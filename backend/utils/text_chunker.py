from typing import List, Dict

CHUNK_CHARS = 2500   # ~500 tokens at avg 5 chars/token
OVERLAP_CHARS = 250  # ~10% overlap to preserve context across chunk boundaries


def chunk_text(pages_content: List[Dict], doc_name: str,
               chunk_size: int = CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> List[Dict]:
    """
    Splits page text into overlapping character-based chunks with metadata.
    Character splitting is equivalent to token splitting for RAG purposes and
    requires no external tokenizer library.
    """
    chunks = []

    for page in pages_content:
        text = page["text"]
        page_num = page["page_number"]

        if not text.strip():
            continue

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Avoid tiny trailing chunks (less than 10% of chunk size)
            if len(chunk.strip()) < chunk_size // 10 and chunks:
                # Append leftover text to the last chunk instead
                last = chunks[-1]
                if last["page_number"] == page_num:
                    last["text"] = last["text"] + " " + chunk.strip()
                    break

            chunks.append({
                "text": chunk.strip(),
                "document_name": doc_name,
                "page_number": page_num
            })

            # Advance by (chunk_size - overlap) to create sliding window
            start += chunk_size - overlap

    return chunks
