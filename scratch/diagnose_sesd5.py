import fitz
import sys

path = "backend/data/uploads/fb4be41fb2e84c88a3f5c03149acebe6_sesd 5.pdf"
try:
    doc = fitz.open(path)
    print(f"Number of pages in PDF: {len(doc)}")
    text_found = False
    for i in range(min(5, len(doc))):
        page = doc[i]
        text = page.get_text()
        print(f"Page {i+1} text length: {len(text)}")
        if text.strip():
            print(f"Page {i+1} snippet: {text[:200]}")
            text_found = True
    if not text_found:
        print("No text could be extracted from the first 5 pages using page.get_text().")
except Exception as e:
    print(f"Error opening or reading PDF: {e}")
