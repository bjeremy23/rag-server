FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies (using pre-built wheels, no build-essential needed)
RUN pip install --no-cache-dir \
    mcp>=1.0.0 \
    chromadb>=0.4.0 \
    sentence-transformers>=2.2.0 \
    langchain-text-splitters>=0.2.0

# Copy server code
COPY mcp_rag_server_simple.py /app/mcp_rag_server.py

# Prepare cache directory for pre-downloaded models (optional for offline builds)
RUN mkdir -p /root/.cache/huggingface/hub

# Copy pre-downloaded model cache if it exists (for offline environments)
# This directory is optional - if it doesn't exist, models will be downloaded on first run
COPY model_cache/hub /root/.cache/huggingface/hub

# Create data directory
RUN mkdir -p /data

# Set environment variable for data directory
ENV RAG_DATA_DIR=/data

# Make script executable
RUN chmod +x /app/mcp_rag_server.py

# Run the server
CMD ["python", "/app/mcp_rag_server.py"]
