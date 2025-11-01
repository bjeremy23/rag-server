# RAG MCP Server

A Model Context Protocol (MCP) server for document vectorization and semantic search using RAG (Retrieval Augmented Generation).

## Features

- **Document Ingestion**: Add documents with automatic chunking and vectorization
- **Semantic Search**: Find relevant information using natural language queries
- **Metadata Support**: Tag documents with custom metadata and filter searches
- **Persistent Storage**: ChromaDB-based vector storage with persistence
- **Efficient Embeddings**: Uses sentence-transformers for fast local embeddings

## Tools Provided

### 1. `add_file`
Add and vectorize a file from the filesystem for RAG search.

**Parameters:**
- `file_path` (string, required): **Full absolute path** to the file on the filesystem
- `doc_id` (string, optional): Unique identifier for the document (defaults to filename)
- `metadata` (object, optional): Document metadata (title, author, source, date)

**Important Requirements:**
- **Must use full absolute path**: The file path must be complete (e.g., `/localdata/brownjer/docs/readme.txt`)
- **Directory must be mounted**: The file's parent directory must be mounted as a volume in the Docker container through the MCP configuration JSON
- The file must be readable by the container user

**Example:**
```json
{
  "file_path": "/localdata/brownjer/documents/python_guide.txt",
  "doc_id": "python_intro",
  "metadata": {
    "title": "Introduction to Python",
    "author": "John Doe"
  }
}
```

**MCP Configuration Requirement:**

For the `add_file` tool to access your filesystem, you must mount the appropriate directories in your MCP configuration. In `mcp.json`:

```json
{
  "mcpServers": {
    "rag": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/localdata/brownjer:/localdata/brownjer:ro",
        "-v", "/localdata/brownjer/.rag_data:/data",
        "rag-server:latest"
      ],
      "disabled": false
    }
  }
}
```

**Note**: 
- The `--rm` flag automatically removes the container when it exits
- The `:ro` (read-only) flag is recommended for source directories to prevent accidental modifications
- The container is created fresh for each jibberish session

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

Add to `~/.jbrsh-mcp-servers.json`:

```json
{
  "rag": {
    "enabled": true,
    "command": "docker",
    "args": [
      "run",
      "-i",
      "--rm",
      "-v", "/localdata/brownjer:/localdata/brownjer:ro",
      "-v", "/home/brownjer:/home/brownjer:ro",
      "-v", "/localdata/brownjer/.rag_data:/data",
      "rag-server:latest"
    ],
    "description": "RAG server for document vectorization and semantic search",
    "tool_prefix": "rag"
  }
}
```

Or for local Python installation:
```json
{
  "rag": {
    "enabled": true,
    "command": "python",
    "args": [
      "/home/brownjer/bin/mcp/rag-server/mcp_rag_server.py"
    ],
    "env": {
      "RAG_DATA_DIR": "/localdata/brownjer/.rag_data"
    },
    "description": "RAG server for document vectorization and semantic search",
    "tool_prefix": "rag"
  }
}
```

## Usage Examples

### Add a File from Filesystem
```bash
# Using jibberish with MCP - must use full absolute path
?add file /localdata/brownjer/documents/kubernetes-guide.txt to the RAG database

# With custom document ID and metadata
?add file /localdata/brownjer/notes/python-tutorial.md with id "python_basics" to the RAG database
```

**Important**: The directory containing the file (e.g., `/localdata/brownjer/documents/`) must be mounted in your Docker container configuration.

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

