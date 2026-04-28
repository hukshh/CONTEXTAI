from pypdf import PdfReader
from typing import List, Dict

def extract_text_from_pdf(file_path: str) -> List[Dict]:
    """
    Extracts text from each page of a PDF file.
    Returns a list of dictionaries containing text and page number.
    """
    reader = PdfReader(file_path)
    pages_content = []
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text.strip():
            pages_content.append({
                "text": text,
                "page_number": i + 1
            })
            
    return pages_content
