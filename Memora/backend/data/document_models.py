"""
Document models for RAG system - compatible with existing architecture
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class DocumentType(str, Enum):
    """Document classification types"""
    ACHIEVEMENT = "achievement"
    PROJECT = "project" 
    SKILL = "skill"
    REFERENCE = "reference"
    MEETING_NOTES = "meeting_notes"
    GENERAL = "general"


class DocumentStatus(str, Enum):
    """Document processing status"""
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class Document(BaseModel):
    """Document model compatible with existing system"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    filename: str
    original_filename: str
    file_path: str
    document_type: DocumentType = DocumentType.GENERAL
    content: str = ""
    summary: Optional[str] = None
    key_insights: List[str] = []
    status: DocumentStatus = DocumentStatus.PROCESSING
    file_size: int = 0
    mime_type: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class DocumentSearch(BaseModel):
    """Document search request"""
    query: str
    limit: int = 5
    document_type: Optional[DocumentType] = None


class DocumentSearchResult(BaseModel):
    """Document search result"""
    document_id: str
    title: str
    content_snippet: str
    document_type: str
    score: float
    metadata: Dict[str, Any] = {}


class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    success: bool
    document_id: Optional[str] = None
    message: str
    document_type: Optional[str] = None