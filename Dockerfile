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

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Prepare cache directory
RUN mkdir -p /root/.cache/huggingface

# Create data directory
RUN mkdir -p /data

# Set environment variable for data directory
ENV RAG_DATA_DIR=/data

# Make script executable
RUN chmod +x /app/mcp_rag_server.py

# Run the server via entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
