"""
Document management endpoints for the scheduling agent
These endpoints handle document upload, search, and management without affecting scheduling
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Form
from typing import List, Optional
import logging

from data.document_models import (
    Document, DocumentSearchResult, DocumentUploadResponse, 
    DocumentSearch, DocumentType, DocumentStatus
)
from data.document_processor import get_document_processor
from data.vector_db import get_vector_database
from data.document_storage import get_document_storage

# Setup logging
logger = logging.getLogger(__name__)

# Create router for document endpoints
documents_router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize services
processor = get_document_processor()
vector_db = get_vector_database()
storage = get_document_storage()


@documents_router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """Upload and process a document for document awareness"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read file content
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Use filename as title if not provided
        doc_title = title or file.filename
        
        # Process document
        document, chunks = processor.process_document(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Override title if provided
        if title:
            document.title = title
        
        # Store document file and metadata
        if not storage.store_document(document, file_content):
            raise HTTPException(status_code=500, detail="Failed to store document")
        
        # Store in vector database if chunks were extracted
        if chunks and document.status == DocumentStatus.INDEXED:
            if not vector_db.store_document(document, chunks):
                logger.warning(f"Failed to store embeddings for document {document.id}")
                document.status = DocumentStatus.ERROR
                document.metadata = {"error": "Failed to store embeddings", "chunks_count": len(chunks)}
                storage.update_document(document)
        
        logger.info(f"Successfully uploaded document: {document.title}")
        
        return DocumentUploadResponse(
            success=document.status == DocumentStatus.INDEXED,
            document_id=str(document.id),
            message=f"Document '{document.title}' uploaded and processed successfully!" if document.status == DocumentStatus.INDEXED else f"Document '{document.title}' uploaded but processing failed",
            document_type=str(document.document_type.value)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@documents_router.post("/search", response_model=List[DocumentSearchResult])
async def search_documents(search_request: DocumentSearch):
    """Search documents using natural language query"""
    try:
        results = vector_db.search_documents(
            query=search_request.query,
            limit=search_request.limit,
            document_type=search_request.document_type,
            similarity_threshold=search_request.similarity_threshold
        )
        
        logger.info(f"Search query '{search_request.query}' returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@documents_router.get("/search/{query}", response_model=List[DocumentSearchResult])
async def search_documents_simple(
    query: str,
    limit: int = Query(10, ge=1, le=50),
    document_type: Optional[str] = Query(None),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0)
):
    """Simple search endpoint for documents"""
    try:
        results = vector_db.search_documents(
            query=query,
            limit=limit,
            document_type=document_type,
            similarity_threshold=similarity_threshold
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error in simple search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@documents_router.get("/", response_model=List[Document])
async def list_documents(
    document_type: Optional[DocumentType] = Query(None),
    status: Optional[DocumentStatus] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=100)
):
    """List all documents with optional filtering"""
    try:
        documents = storage.list_documents(
            document_type=document_type,
            status=status,
            limit=limit
        )
        
        return documents
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@documents_router.get("/{document_id}", response_model=Document)
async def get_document(document_id: str):
    """Get document metadata by ID"""
    try:
        document = storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@documents_router.get("/{document_id}/similar", response_model=List[DocumentSearchResult])
async def get_similar_documents(
    document_id: str,
    limit: int = Query(5, ge=1, le=20)
):
    """Get documents similar to the specified document"""
    try:
        # Check if document exists
        document = storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        similar_docs = vector_db.get_similar_documents(document_id, limit)
        return similar_docs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar documents for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find similar documents: {str(e)}")


@documents_router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all associated data"""
    try:
        # Check if document exists
        document = storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from vector database
        vector_db.delete_document(document_id)
        
        # Delete from storage
        if not storage.delete_document(document_id):
            raise HTTPException(status_code=500, detail="Failed to delete document from storage")
        
        logger.info(f"Successfully deleted document: {document.title}")
        return {"message": f"Document '{document.title}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@documents_router.get("/stats/overview")
async def get_document_stats():
    """Get overview statistics for document storage and search"""
    try:
        storage_stats = storage.get_storage_stats()
        vector_stats = vector_db.get_document_stats()
        
        return {
            "storage": storage_stats,
            "vector_db": vector_stats,
            "system_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        return {
            "storage": {"error": str(e)},
            "vector_db": {"error": str(e)},
            "system_status": "error"
        }


@documents_router.get("/health/check")
async def document_health_check():
    """Health check for document system components"""
    try:
        storage_health = storage.health_check()
        vector_health = vector_db.health_check()
        
        overall_status = "healthy" if (
            storage_health.get("status") == "healthy" and 
            vector_health.get("status") == "healthy"
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "components": {
                "storage": storage_health,
                "vector_db": vector_health,
                "processor": {"status": "healthy"}  # Processor is stateless
            }
        }
        
    except Exception as e:
        logger.error(f"Error in document health check: {e}")
        return {
            "status": "error",
            "error": str(e)
        }