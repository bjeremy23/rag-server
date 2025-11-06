#!/bin/bash
# Entrypoint script that handles optional model cache

# The server code will download models if they don't exist
exec python /app/mcp_rag_server.py "$@"
