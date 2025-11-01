"""
Vector database handler using ChromaDB for document embeddings
Designed for efficient storage and retrieval with minimal performance impact
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import uuid

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from data.document_models import Document, DocumentSearchResult


class VectorDatabase:
    """Handles vector storage and similarity search using ChromaDB"""
    
    def __init__(self, storage_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Setup storage directory
        if storage_path is None:
            storage_path = os.path.join(os.path.dirname(__file__), '..', 'storage', 'vectordb')
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.storage_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = 384
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.logger.info(f"Vector database initialized at {self.storage_path}")

    def store_document(self, document: Document, chunks: List[str]) -> bool:
        """Store document chunks with embeddings"""
        try:
            if not chunks:
                self.logger.warning(f"No chunks to store for document {document.id}")
                return False
            
            # Generate embeddings for all chunks
            embeddings = self.embedding_model.encode(chunks, convert_to_tensor=False)
            
            # Prepare data for ChromaDB
            chunk_ids = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document.id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                
                metadata = {
                    "document_id": str(document.id),
                    "document_title": document.title,
                    "document_type": str(document.document_type.value),
                    "chunk_index": i,
                    "file_name": document.filename,
                    "upload_date": document.created_at.isoformat()
                }
                metadatas.append(metadata)
            
            # Store in ChromaDB
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings.tolist(),
                documents=chunks,
                metadatas=metadatas
            )
            
            self.logger.info(f"Stored {len(chunks)} chunks for document {document.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing document {document.id}: {e}")
            # Print error for debugging
            print(f"Vector DB storage error for document {document.id}: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False

    def search_documents(self, query: str, limit: int = 10, document_type: str = None, 
                        similarity_threshold: float = 0.7) -> List[DocumentSearchResult]:
        """Search for relevant documents based on query"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_tensor=False)
            
            # Prepare search filters
            where_filter = {}
            if document_type:
                where_filter["document_type"] = document_type
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=limit,
                where=where_filter if where_filter else None
            )
            
            # Process results
            search_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    # Calculate similarity score (ChromaDB returns distances, convert to similarity)
                    distance = results['distances'][0][i]
                    similarity = max(0, 1 - distance)  # Convert distance to similarity
                    
                    if similarity >= similarity_threshold:
                        result = DocumentSearchResult(
                            document_id=results['metadatas'][0][i]['document_id'],
                            title=results['metadatas'][0][i]['document_title'],
                            content_snippet=results['documents'][0][i][:300] + "..." if len(results['documents'][0][i]) > 300 else results['documents'][0][i],
                            document_type=results['metadatas'][0][i]['document_type'],
                            score=similarity,
                            metadata={
                                "chunk_index": results['metadatas'][0][i]['chunk_index'],
                                "file_name": results['metadatas'][0][i]['file_name']
                            }
                        )
                        search_results.append(result)
            
            self.logger.info(f"Found {len(search_results)} relevant documents for query: {query[:50]}...")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {e}")
            return []

    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document"""
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"document_id": str(document_id)}
            )
            
            if results['ids']:
                # Delete all chunks
                self.collection.delete(
                    ids=results['ids']
                )
                self.logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            else:
                self.logger.warning(f"No chunks found for document {document_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {e}")
            return False

    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about stored documents"""
        try:
            collection_stats = {
                "total_chunks": self.collection.count(),
                "collection_name": self.collection.name
            }
            
            # Get document type distribution
            all_metadata = self.collection.get()['metadatas']
            type_counts = {}
            document_counts = set()
            
            for metadata in all_metadata:
                doc_type = metadata.get('document_type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                document_counts.add(metadata.get('document_id', ''))
            
            collection_stats.update({
                "total_documents": len(document_counts),
                "document_types": type_counts
            })
            
            return collection_stats
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

    def get_similar_documents(self, document_id: str, limit: int = 5) -> List[DocumentSearchResult]:
        """Find documents similar to a given document"""
        try:
            # Get chunks for the source document
            source_chunks = self.collection.get(
                where={"document_id": str(document_id)}
            )
            
            if not source_chunks['documents']:
                return []
            
            # Find similar documents using the first chunk as reference
            results = self.collection.query(
                query_texts=[source_chunks['documents'][0]],
                n_results=limit + 5,  # Get extra to filter out the source document
                where={"document_id": {"$ne": str(document_id)}}
            )
            
            # Process results
            similar_docs = []
            seen_docs = set()
            
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    doc_id = results['metadatas'][0][i]['document_id']
                    
                    if doc_id not in seen_docs and len(similar_docs) < limit:
                        seen_docs.add(doc_id)
                        
                        distance = results['distances'][0][i]
                        similarity = max(0, 1 - distance)
                        
                        result = DocumentSearchResult(
                            document_id=doc_id,
                            title=results['metadatas'][0][i]['document_title'],
                            content_snippet=results['documents'][0][i][:200] + "...",
                            document_type=results['metadatas'][0][i]['document_type'],
                            score=similarity,
                            metadata={
                                "file_name": results['metadatas'][0][i]['file_name']
                            }
                        )
                        similar_docs.append(result)
            
            return similar_docs
            
        except Exception as e:
            self.logger.error(f"Error finding similar documents: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """Check if vector database is healthy"""
        try:
            # Test basic operations
            test_embedding = self.embedding_model.encode(["test"], convert_to_tensor=False)
            collection_count = self.collection.count()
            
            return {
                "status": "healthy",
                "embedding_model_loaded": True,
                "collection_accessible": True,
                "total_chunks": collection_count,
                "embedding_dimension": self.embedding_dim
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global instance for reuse
_vector_db_instance = None

def get_vector_database() -> VectorDatabase:
    """Get vector database instance (singleton pattern)"""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDatabase()
    return _vector_db_instance
