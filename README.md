# RAG MCP Server

A Model Context Protocol (MCP) server for document vectorization and semantic search using RAG (Retrieval Augmented Generation).

## Features

- **Document Ingestion**: Add documents with automatic chunking and vectorization
- **Semantic Search**: Find relevant information using natural language queries
- **Metadata Support**: Tag documents with custom metadata and filter searches
- **Persistent Storage**: ChromaDB-based vector storage with persistence
- **Efficient Embeddings**: Uses sentence-transformers for fast local embeddings

## Tools Provided

### 1. `add_document`
Add and vectorize a document for RAG search.

**Parameters:**
- `content` (string, required): The document content to vectorize
- `doc_id` (string, required): Unique identifier for the document
- `metadata` (object, optional): Document metadata (title, author, source, date)

**Example:**
```json
{
  "content": "Python is a high-level programming language...",
  "doc_id": "python_intro",
  "metadata": {
    "title": "Introduction to Python",
    "author": "John Doe",
    "source": "python_guide.pdf"
  }
}
```

### 2. `search`
Perform semantic search across all vectorized documents.

**Parameters:**
- `query` (string, required): The search query
- `n_results` (integer, optional): Number of results to return (default: 5, max: 20)
- `filter_metadata` (object, optional): Filter by metadata (e.g., `{"author": "John Doe"}`)

**Example:**
```json
{
  "query": "How do I use Python lists?",
  "n_results": 3
}
```

### 3. `delete_document`
Delete a document and all its chunks from the vector database.

**Parameters:**
- `doc_id` (string, required): The document ID to delete

**Example:**
```json
{
  "doc_id": "python_intro"
}
```

### 4. `list_documents`
List all documents in the vector database with their metadata.

**Parameters:** None

## Installation

### Option 1: Docker (Recommended)

Build the Docker image:
```bash
cd /home/brownjer/bin/mcp/rag-server
docker build -t rag-server:latest .
```

### Option 2: Local Python

Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### For Jibberish Integration

Add to `~/.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "rag": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "${HOME}/.rag_data:/data",
        "rag-server:latest"
      ],
      "disabled": false
    }
  }
}
```

Or for local Python installation:
```json
{
  "mcpServers": {
    "rag": {
      "command": "python",
      "args": [
        "/home/brownjer/bin/mcp/rag-server/mcp_rag_server.py"
      ],
      "env": {
        "RAG_DATA_DIR": "${HOME}/.rag_data"
      },
      "disabled": false
    }
  }
}
```

## Usage Examples

### Add a Document
```bash
# Using jibberish with MCP
?add a document about kubernetes with content "Kubernetes is a container orchestration platform..." and id "k8s_intro"
```

### Search Documents
```bash
?search for information about container orchestration
```

### List All Documents
```bash
?list all documents in the RAG database
```

### Delete a Document
```bash
?delete document with id "k8s_intro"
```

## Data Storage

Documents are stored in ChromaDB with persistence:
- **Docker**: `/data` volume (mapped to host directory)
- **Local**: `$RAG_DATA_DIR` environment variable (default: `/tmp/rag_data`)

## Technical Details

- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Chunking Strategy**: Recursive character splitting with 500 char chunks, 50 char overlap
- **Vector DB**: ChromaDB with persistent storage
- **Similarity Metric**: Cosine similarity

## Advanced Usage

### Custom Metadata Filtering

Search only documents from a specific author:
```json
{
  "query": "machine learning",
  "filter_metadata": {"author": "John Doe"}
}
```

### Batch Document Import

You can create a script to import multiple documents:
```python
import asyncio
# Use MCP client to call add_document for each file
```

## Troubleshooting

**Issue**: Server fails to start
- Check Docker logs: `docker logs <container_id>`
- Verify data directory permissions

**Issue**: Search returns no results
- Ensure documents have been added with `list_documents`
- Try increasing `n_results`

**Issue**: Slow embedding generation
- First run downloads the embedding model (~80MB)
- Subsequent runs use cached model

## Future Enhancements

- [ ] Support for PDF, DOCX, and other file formats
- [ ] Hybrid search (vector + keyword/BM25)
- [ ] Reranking with cross-encoders
- [ ] Multiple embedding model options
- [ ] Cloud vector DB support (Pinecone, Weaviate)
- [ ] Document update/versioning
