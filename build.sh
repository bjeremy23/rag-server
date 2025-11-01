#!/bin/bash
# Build script for RAG MCP Server

set -e

echo "Building RAG MCP Server Docker image..."
docker build -t rag-server:latest .

echo ""
echo "✓ Build complete!"
echo ""
echo "To run the server:"
echo "  docker run -i --rm -v \${HOME}/.rag_data:/data rag-server:latest"
echo ""
echo "To add to Jibberish, update ~/.vscode/mcp.json with:"
echo '  "rag": {'
echo '    "command": "docker",'
echo '    "args": ["run", "-i", "--rm", "-v", "${HOME}/.rag_data:/data", "rag-server:latest"],'
echo '    "disabled": false'
echo '  }'
