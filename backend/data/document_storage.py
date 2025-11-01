"""
Document storage manager for handling file storage and metadata persistence
Designed to work alongside vector database with minimal system impact
"""

import os
import json
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

from data.document_models import Document, DocumentStatus, DocumentType


class DocumentStorage:
    """Handles document file storage and metadata persistence"""
    
    def __init__(self, storage_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Setup storage directories
        if storage_path is None:
            storage_path = os.path.join(os.path.dirname(__file__), '..', 'storage')
        
        self.base_path = Path(storage_path)
        self.files_path = self.base_path / 'files'
        self.metadata_path = self.base_path / 'metadata'
        
        # Create directories
        self.files_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)
        
        # Metadata file for document index
        self.index_file = self.metadata_path / 'documents.json'
        
        self.logger.info(f"Document storage initialized at {self.base_path}")

    def store_document(self, document: Document, file_content: bytes) -> bool:
        """Store document file and metadata"""
        try:
            # Generate file path
            file_extension = self._get_file_extension(document.filename)
            stored_filename = f"{document.id}{file_extension}"
            file_path = self.files_path / stored_filename
            
            # Store file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Update document with storage info
            document.file_path = str(file_path)
            document.original_filename = document.filename
            document.filename = stored_filename
            
            # Store metadata
            self._save_document_metadata(document)
            
            self.logger.info(f"Stored document {document.title} at {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing document {document.id}: {e}")
            return False

    def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve document metadata by ID"""
        try:
            documents = self._load_documents_index()
            doc_data = documents.get(str(document_id))
            
            if doc_data:
                return Document.model_validate(doc_data)
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving document {document_id}: {e}")
            return None

    def get_document_file(self, document_id: str) -> Optional[bytes]:
        """Retrieve document file content by ID"""
        try:
            document = self.get_document(document_id)
            if not document or not document.file_path:
                return None
            
            file_path = Path(document.file_path)
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    return f.read()
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading document file {document_id}: {e}")
            return None

    def list_documents(self, document_type: DocumentType = None, 
                      status: DocumentStatus = None, 
                      limit: int = None) -> List[Document]:
        """List documents with optional filtering"""
        try:
            documents = self._load_documents_index()
            doc_list = []
            
            for doc_data in documents.values():
                document = Document.model_validate(doc_data)
                
                # Apply filters
                if document_type and document.document_type != document_type:
                    continue
                if status and document.status != status:
                    continue
                
                doc_list.append(document)
            
            # Sort by created date (newest first)
            doc_list.sort(key=lambda x: x.created_at, reverse=True)
            
            # Apply limit
            if limit:
                doc_list = doc_list[:limit]
            
            return doc_list
            
        except Exception as e:
            self.logger.error(f"Error listing documents: {e}")
            return []

    def update_document(self, document: Document) -> bool:
        """Update document metadata"""
        try:
            documents = self._load_documents_index()
            documents[str(document.id)] = document.model_dump()
            
            with open(self.index_file, 'w') as f:
                json.dump(documents, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating document {document.id}: {e}")
            return False

    def delete_document(self, document_id: str) -> bool:
        """Delete document file and metadata"""
        try:
            document = self.get_document(document_id)
            if not document:
                return False
            
            # Delete file if exists
            if document.file_path and Path(document.file_path).exists():
                Path(document.file_path).unlink()
            
            # Remove from index
            documents = self._load_documents_index()
            if str(document_id) in documents:
                del documents[str(document_id)]
                
                with open(self.index_file, 'w') as f:
                    json.dump(documents, f, indent=2, default=str)
            
            self.logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            documents = self._load_documents_index()
            
            # Calculate statistics
            total_documents = len(documents)
            total_size = 0
            status_counts = {}
            type_counts = {}
            
            for doc_data in documents.values():
                total_size += doc_data.get('file_size', 0)
                
                status = doc_data.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                doc_type = doc_data.get('document_type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # Get disk usage
            disk_usage = shutil.disk_usage(self.base_path)
            
            return {
                "total_documents": total_documents,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "status_distribution": status_counts,
                "type_distribution": type_counts,
                "storage_path": str(self.base_path),
                "disk_free_gb": round(disk_usage.free / (1024**3), 2),
                "disk_total_gb": round(disk_usage.total / (1024**3), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}")
            return {"error": str(e)}

    def cleanup_orphaned_files(self) -> Dict[str, Any]:
        """Clean up files that don't have corresponding metadata"""
        try:
            documents = self._load_documents_index()
            tracked_files = set()
            
            # Get all tracked files
            for doc_data in documents.values():
                if doc_data.get('file_path'):
                    tracked_files.add(Path(doc_data['file_path']).name)
            
            # Find orphaned files
            orphaned_files = []
            for file_path in self.files_path.iterdir():
                if file_path.is_file() and file_path.name not in tracked_files:
                    orphaned_files.append(file_path)
            
            # Remove orphaned files
            removed_count = 0
            removed_size = 0
            
            for file_path in orphaned_files:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    removed_count += 1
                    removed_size += file_size
                except Exception as e:
                    self.logger.warning(f"Could not remove orphaned file {file_path}: {e}")
            
            return {
                "orphaned_files_found": len(orphaned_files),
                "files_removed": removed_count,
                "size_freed_mb": round(removed_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}

    def _save_document_metadata(self, document: Document):
        """Save document metadata to index"""
        documents = self._load_documents_index()
        documents[str(document.id)] = document.model_dump()
        
        with open(self.index_file, 'w') as f:
            json.dump(documents, f, indent=2, default=str)

    def _load_documents_index(self) -> Dict[str, Any]:
        """Load documents index from file"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading documents index: {e}")
            return {}

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        return Path(filename).suffix.lower()

    def health_check(self) -> Dict[str, Any]:
        """Check if storage system is healthy"""
        try:
            # Check if directories are accessible
            files_writable = os.access(self.files_path, os.W_OK)
            metadata_writable = os.access(self.metadata_path, os.W_OK)
            
            # Check index file
            index_readable = self.index_file.exists() and os.access(self.index_file, os.R_OK)
            
            # Get basic stats
            documents = self._load_documents_index()
            
            return {
                "status": "healthy" if files_writable and metadata_writable else "unhealthy",
                "files_directory_writable": files_writable,
                "metadata_directory_writable": metadata_writable,
                "index_file_readable": index_readable,
                "total_documents": len(documents),
                "storage_path": str(self.base_path)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global instance for reuse
_storage_instance = None

def get_document_storage() -> DocumentStorage:
    """Get document storage instance (singleton pattern)"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = DocumentStorage()
    return _storage_instance