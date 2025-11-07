#!/usr/bin/env python3
"""
MCP RAG Server - Document Vectorization and Semantic Search
Simple JSON-RPC implementation over stdio
"""

import json
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Vector DB and embeddings
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Document processing
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)


class RAGServer:
    """Simple JSON-RPC MCP Server for RAG."""
    
    def __init__(self, data_dir: str = "/data"):
        """Initialize the RAG server."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with PersistentClient for automatic persistence
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.data_dir / "chroma")
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection("documents")
            logger.info("Loaded existing collection")
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name="documents",
                metadata={"description": "Document collection for RAG"}
            )
            logger.info("Created new collection")
        
        # Lazy-load embedding model
        self.model = None
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def _get_model(self):
        """Lazy-load the embedding model."""
        if self.model is None:
            logger.info("Loading embedding model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded")
        return self.model
    
    def send_response(self, request_id, result):
        """Send JSON-RPC response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        print(json.dumps(response), flush=True)
    
    def send_error(self, request_id, code, message):
        """Send JSON-RPC error response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        print(json.dumps(response), flush=True)
    
    def handle_initialize(self, request_id, params):
        """Handle initialize request."""
        result = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "rag-server",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {}
            }
        }
        self.send_response(request_id, result)
    
    def handle_tools_list(self, request_id):
        """Handle tools/list request."""
        tools = [
            {
                "name": "add_file",
                "description": "Read a file from the filesystem and add it to the RAG database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "Path to file"},
                        "doc_id": {"type": "string", "description": "Optional document ID"},
                        "metadata": {"type": "object", "description": "Optional metadata"}
                    },
                    "required": ["filepath"]
                }
            },
            {
                "name": "search",
                "description": "Semantic search across documents",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "n_results": {"type": "integer", "description": "Number of results", "default": 5},
                        "filter_metadata": {"type": "object", "description": "Metadata filters"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "delete_document",
                "description": "Delete a document",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "doc_id": {"type": "string", "description": "Document ID to delete"}
                    },
                    "required": ["doc_id"]
                }
            },
            {
                "name": "list_documents",
                "description": "List all documents",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        self.send_response(request_id, {"tools": tools})
    
    def handle_tools_call(self, request_id, params):
        """Handle tools/call request."""
        try:
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            if name == "add_file":
                result = self.add_file(**arguments)
            elif name == "search":
                result = self.search(**arguments)
            elif name == "delete_document":
                result = self.delete_document(**arguments)
            elif name == "list_documents":
                result = self.list_documents()
            else:
                self.send_error(request_id, -32601, f"Unknown tool: {name}")
                return
            
            self.send_response(request_id, {"content": [{"type": "text", "text": result}]})
            
        except Exception as e:
            logger.error(f"Error in tool {name}: {e}", exc_info=True)
            self.send_error(request_id, -32603, f"Error: {str(e)}")
    
    def add_file(self, filepath: str, doc_id: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """Add a file to the RAG database."""
        if metadata is None:
            metadata = {}
        
        file_path = Path(filepath).expanduser().resolve()
        
        if not file_path.exists():
            return f"Error: File not found: {filepath}"
        
        if not file_path.is_file():
            return f"Error: Not a file: {filepath}"
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return f"Error: Unable to read file as text: {filepath}"
        
        if doc_id is None:
            doc_id = file_path.stem
        
        metadata.update({
            "filepath": str(file_path),
            "filename": file_path.name,
            "file_extension": file_path.suffix
        })
        
        result = self.add_document(content, doc_id, metadata)
        return f"✓ Successfully imported file: {file_path.name}\n  - Full path: {file_path}\n  - File size: {len(content)} characters\n{result}"
    
    def add_document(self, content: str, doc_id: str, metadata: Optional[Dict] = None) -> str:
        """Add and vectorize a document."""
        if metadata is None:
            metadata = {}
        
        # Chunk the document
        chunks = self.text_splitter.split_text(content)
        logger.info(f"Split document {doc_id} into {len(chunks)} chunks")
        
        # Generate embeddings
        model = self._get_model()
        embeddings = model.encode(chunks, show_progress_bar=False).tolist()
        
        # Prepare data
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        chunk_metadata = [
            {**metadata, "doc_id": doc_id, "chunk_index": i, "total_chunks": len(chunks)}
            for i in range(len(chunks))
        ]
        
        # Store in vector DB
        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=chunk_metadata,
            ids=chunk_ids
        )
        
        result = f"✓ Successfully added document '{doc_id}'\n  - Chunks created: {len(chunks)}\n  - Embedding dimensions: {len(embeddings[0])}"
        if metadata:
            result += f"\n  - Metadata: {json.dumps(metadata, indent=2)}"
        
        logger.info(f"Added document {doc_id}")
        return result
    
    def search(self, query: str, n_results: int = 5, filter_metadata: Optional[Dict] = None) -> str:
        """Perform semantic search."""
        model = self._get_model()
        query_embedding = model.encode([query], show_progress_bar=False).tolist()
        
        search_kwargs = {
            "query_embeddings": query_embedding,
            "n_results": n_results
        }
        
        if filter_metadata:
            search_kwargs["where"] = filter_metadata
        
        results = self.collection.query(**search_kwargs)
        
        if not results['documents'][0]:
            return "No results found."
        
        response_lines = [f"Found {len(results['documents'][0])} relevant chunks:\n"]
        
        for i, (doc, dist, metadata) in enumerate(zip(
            results['documents'][0],
            results['distances'][0],
            results['metadatas'][0]
        )):
            similarity = 1 - (dist / 2)
            response_lines.append(f"\n--- Result {i+1} (Similarity: {similarity:.3f}) ---")
            response_lines.append(f"Document: {metadata.get('doc_id', 'unknown')}")
            if 'title' in metadata:
                response_lines.append(f"Title: {metadata['title']}")
            response_lines.append(f"Chunk: {metadata.get('chunk_index', '?')} / {metadata.get('total_chunks', '?')}")
            response_lines.append(f"\nContent:\n{doc}")
        
        return "\n".join(response_lines)
    
    def delete_document(self, doc_id: str) -> str:
        """Delete a document."""
        results = self.collection.get(where={"doc_id": doc_id})
        
        if not results['ids']:
            return f"Document '{doc_id}' not found."
        
        self.collection.delete(ids=results['ids'])
        return f"✓ Deleted document '{doc_id}' ({len(results['ids'])} chunks removed)"
    
    def list_documents(self) -> str:
        """List all documents."""
        results = self.collection.get()
        
        if not results['ids']:
            return "No documents in the database."
        
        docs = {}
        for metadata in results['metadatas']:
            doc_id = metadata.get('doc_id', 'unknown')
            if doc_id not in docs:
                docs[doc_id] = {
                    'chunks': 0,
                    'metadata': {k: v for k, v in metadata.items() 
                                if k not in ['doc_id', 'chunk_index', 'total_chunks']}
                }
            docs[doc_id]['chunks'] += 1
        
        response_lines = [f"Total documents: {len(docs)}\n"]
        
        for doc_id, info in docs.items():
            response_lines.append(f"\n📄 {doc_id}")
            response_lines.append(f"   Chunks: {info['chunks']}")
            if info['metadata']:
                for key, value in info['metadata'].items():
                    response_lines.append(f"   {key}: {value}")
        
        return "\n".join(response_lines)
    
    def run(self):
        """Main server loop."""
        logger.info("Starting RAG MCP Server...")
        logger.info("Server ready, waiting for requests...")
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                request_id = request.get("id")
                method = request.get("method")
                params = request.get("params", {})
                
                if method == "initialize":
                    self.handle_initialize(request_id, params)
                elif method == "tools/list":
                    self.handle_tools_list(request_id)
                elif method == "tools/call":
                    self.handle_tools_call(request_id, params)
                else:
                    self.send_error(request_id, -32601, f"Method not found: {method}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                self.send_error(None, -32700, f"Parse error: {e}")
            except Exception as e:
                logger.error(f"Error processing request: {e}", exc_info=True)
                self.send_error(request.get("id") if 'request' in locals() else None, -32603, f"Internal error: {e}")


def main():
    """Entry point."""
    import os
    data_dir = os.getenv("RAG_DATA_DIR", "/tmp/rag_data")
    server = RAGServer(data_dir=data_dir)
    server.run()


if __name__ == "__main__":
    main()
