import fitz
from typing import List, Dict

def extract_text_from_pdf(file_path: str) -> List[Dict]:
    """
    Extracts text from each page of a PDF file using PyMuPDF (fitz).
    Returns a list of dictionaries containing text and page number.
    """
    doc = fitz.open(file_path)
    pages_content = []
    
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages_content.append({
                "text": text,
                "page_number": i + 1
            })
            
    return pages_content
