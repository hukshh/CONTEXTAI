from backend.services.retrieval_service import retrieval_service
import os

print(f"Index total: {retrieval_service.index.ntotal}")
print(f"Metadata keys: {list(retrieval_service.metadata.keys())[:10]}...")
print(f"Documents tracked: {list(retrieval_service.doc_to_ids.keys())}")

# Check if 'sesd 3.pdf' has any chunks
if "sesd 3.pdf" in retrieval_service.doc_to_ids:
    num_chunks = len(retrieval_service.doc_to_ids["sesd 3.pdf"])
    print(f"'sesd 3.pdf' has {num_chunks} chunks indexed.")
else:
    print("'sesd 3.pdf' is NOT indexed yet.")

# Check uploads folder
if os.path.exists("uploads"):
    print(f"Files in uploads: {os.listdir('uploads')}")
