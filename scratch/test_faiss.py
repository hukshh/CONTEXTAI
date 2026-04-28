import faiss
import numpy as np

try:
    d = 64
    nb = 100
    nq = 5
    xb = np.random.random((nb, d)).astype('float32')
    xq = np.random.random((nq, d)).astype('float32')
    index = faiss.IndexFlatL2(d)
    index.add(xb)
    D, I = index.search(xq, 4)
    print("FAISS working correctly")
    print(I)
except Exception as e:
    print(f"FAISS error: {e}")
