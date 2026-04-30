# ---- Stage: Base ----
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for faiss-cpu
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the fastembed ONNX model so it's baked into the image.
# This avoids a slow cold-start download on Render on every deploy.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5')"

# Copy application code
COPY . .

# Create data dir (for local use; on Render, mount a persistent disk at /data)
RUN mkdir -p /data/uploads /data/storage

# Render injects PORT automatically; default to 8000 for local docker run
ENV PORT=8000
ENV BASE_PATH=/data

EXPOSE 8000

CMD ["python", "main.py"]
