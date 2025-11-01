"""
Document awareness enhancement for the scheduling agent
Provides contextual document information without disrupting scheduling operations
"""

import logging
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime

from data.vector_db import get_vector_database
from data.document_storage import get_document_storage
from data.document_models import DocumentSearchResult


class DocumentContext(TypedDict):
    """Context information from document search"""
    relevant_documents: List[DocumentSearchResult]
    context_summary: str
    search_performed: bool
    search_query: str


class DocumentAwareEnhancement:
    """Enhances agent responses with document context when relevant"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vector_db = get_vector_database()
        self.storage = get_document_storage()
        
    def should_use_documents(self, user_message: str, operation: str) -> bool:
        """Determine if document context would be helpful for this request"""
        
        # Don't interfere with core scheduling operations
        scheduling_operations = {
            'create', 'list', 'list_date', 'delete', 'delete_selective', 
            'delete_date', 'move', 'update', 'context_update', 'replace', 
            'postpone', 'search', 'create_bulk'
        }
        
        if operation in scheduling_operations:
            # Only add document context for certain types of scheduling queries
            # that might benefit from additional information
            message_lower = user_message.lower()
            
            # Help with scheduling decisions or planning
            if any(phrase in message_lower for phrase in [
                'what should i', 'help me plan', 'suggest', 'recommend',
                'available', 'free time', 'schedule around', 'conflict with',
                'project deadline', 'meeting about', 'work on'
            ]):
                return True
            
            return False
        
        # For chat operations, use documents when relevant
        if operation == 'chat':
            message_lower = user_message.lower()
            
            # Questions that might benefit from document context
            if any(phrase in message_lower for phrase in [
                'tell me about', 'what do you know', 'information about',
                'details on', 'explain', 'help with', 'how to', 'what is',
                'project', 'document', 'file', 'work', 'task', 'meeting',
                'achievement', 'skill', 'experience', 'certification', 'certificate',
                'all certifications', 'my certifications', 'what certifications',
                'list certificates', 'diploma', 'course', 'qualification'
            ]):
                return True
        
        return False
    
    def get_document_context(self, user_message: str, limit: int = 3) -> DocumentContext:
        """Retrieve relevant document context for the user's message"""
        
        try:
            message_lower = user_message.lower()
            
            # For broad queries like "all certifications", search by document type
            if any(phrase in message_lower for phrase in ['all certifications', 'all certificates', 'my certifications', 'what certifications', 'list certificates']):
                # Get all achievement/certification documents
                all_docs = self.storage.list_documents()
                relevant_docs = []
                
                for doc in all_docs:
                    if (doc.document_type == 'achievement' or 
                        any(word in doc.title.lower() for word in ['certificate', 'certification', 'diploma', 'award']) or
                        any(word in doc.content.lower() for word in ['certificate', 'certification', 'diploma', 'completion'])):
                        
                        # Create a search result-like object
                        from data.document_models import DocumentSearchResult
                        search_result = DocumentSearchResult(
                            title=doc.title,
                            content_snippet=doc.content[:300],  # First 300 chars
                            score=1.0,  # High relevance for direct matches
                            document_type=doc.document_type,
                            metadata=doc.metadata or {}
                        )
                        relevant_docs.append(search_result)
                
                if relevant_docs:
                    context_summary = f"Found {len(relevant_docs)} certification/achievement document(s)"
                    return DocumentContext(
                        relevant_documents=relevant_docs,
                        context_summary=context_summary,
                        search_performed=True,
                        search_query="all certifications"
                    )
            
            # Extract key terms for document search
            search_query = self._extract_search_terms(user_message)
            
            if not search_query:
                return DocumentContext(
                    relevant_documents=[],
                    context_summary="No relevant search terms found",
                    search_performed=False,
                    search_query=""
                )
            
            # Search for relevant documents
            results = self.vector_db.search_documents(
                query=search_query,
                limit=limit,
                similarity_threshold=0.1  # Much lower threshold for more inclusive results
            )
            
            # Create context summary
            context_summary = self._create_context_summary(results, search_query)
            
            return DocumentContext(
                relevant_documents=results,
                context_summary=context_summary,
                search_performed=True,
                search_query=search_query
            )
            
        except Exception as e:
            self.logger.error(f"Error getting document context: {e}")
            return DocumentContext(
                relevant_documents=[],
                context_summary=f"Error retrieving document context: {str(e)}",
                search_performed=False,
                search_query=""
            )
    
    def enhance_response(self, original_response: str, document_context: DocumentContext) -> str:
        """Enhance the agent's response with document context"""
        
        if not document_context['search_performed'] or not document_context['relevant_documents']:
            return original_response
        
        # Add document context to response
        enhanced_response = original_response
        
        if len(document_context['relevant_documents']) > 0:
            enhanced_response += f"\n\n📚 **Related Information:**\n{document_context['context_summary']}"
            
            # Add quick reference to relevant documents
            doc_refs = []
            for doc in document_context['relevant_documents'][:2]:  # Limit to top 2
                snippet = doc.content_snippet[:100] + "..." if len(doc.content_snippet) > 100 else doc.content_snippet
                doc_refs.append(f"• **{doc.title}**: {snippet}")
            
            if doc_refs:
                enhanced_response += f"\n\n🔍 **Relevant Documents:**\n" + "\n".join(doc_refs)
        
        return enhanced_response
    
    def _extract_search_terms(self, message: str) -> str:
        """Extract relevant search terms from user message"""
        
        # Check for specific important keywords first
        message_lower = message.lower()
        
        # For certificate/achievement queries, be more inclusive
        if any(word in message_lower for word in ['certificate', 'certification', 'cambridge', 'achievement', 'diploma', 'course']):
            # Extract key terms more permissively for certificate queries
            important_terms = []
            words = message.lower().split()
            
            for word in words:
                clean_word = word.strip('.,!?;:()[]{}"\'-')
                # Include more words for certificate queries
                if (len(clean_word) >= 2 and 
                    clean_word not in {'the', 'and', 'for', 'with', 'can', 'you', 'what', 'how', 'when', 'where', 'why', 'do', 'is', 'are', 'of', 'to', 'in', 'on', 'at'}):
                    important_terms.append(clean_word)
            
            # Add specific certificate phrases
            for phrase in ['cambridge certification', 'cambridge certificate', 'cambridge english', 'level c1', 'empower course']:
                if phrase in message_lower:
                    important_terms.append(phrase)
            
            # Remove duplicates and limit
            unique_terms = list(dict.fromkeys(important_terms))  # Remove duplicates while preserving order
            return ' '.join(unique_terms[:5])  # Limit to 5 terms
        
        # Remove common scheduling words that aren't useful for document search
        scheduling_words = {
            'schedule', 'create', 'add', 'delete', 'remove', 'move', 'update',
            'tomorrow', 'today', 'yesterday', 'time', 'date', 'at', 'on',
            'am', 'pm', 'morning', 'afternoon', 'evening', 'night'
        }
        
        # Extract potential key terms
        words = message.lower().split()
        search_terms = []
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,!?;:()[]{}"\'-')
            
            # Skip if too short, is a scheduling word, or is common
            if (len(clean_word) < 3 or 
                clean_word in scheduling_words or 
                clean_word in {'the', 'and', 'for', 'with', 'can', 'you', 'what', 'how', 'when', 'where', 'why'}):
                continue
            
            search_terms.append(clean_word)
        
        # Also look for phrases that might be important
        for phrase in ['project management', 'team meeting', 'client work', 'development task', 'research work']:
            if phrase in message_lower:
                search_terms.append(phrase)
        
        return ' '.join(search_terms[:5])  # Limit to 5 terms
    
    def _create_context_summary(self, results: List[DocumentSearchResult], search_query: str) -> str:
        """Create a summary of the document context"""
        
        if not results:
            return f"No documents found related to '{search_query}'"
        
        # Group by document type if available
        type_groups = {}
        for result in results:
            doc_type = result.metadata.get('document_type', 'general')
            if doc_type not in type_groups:
                type_groups[doc_type] = []
            type_groups[doc_type].append(result)
        
        summary_parts = []
        
        if len(results) == 1:
            summary_parts.append(f"Found 1 relevant document about '{search_query}'")
        else:
            summary_parts.append(f"Found {len(results)} relevant documents about '{search_query}'")
        
        # Add type breakdown if multiple types
        if len(type_groups) > 1:
            type_summary = []
            for doc_type, docs in type_groups.items():
                type_name = doc_type.replace('_', ' ').title()
                type_summary.append(f"{len(docs)} {type_name}")
            summary_parts.append(f"Types: {', '.join(type_summary)}")
        
        return ". ".join(summary_parts) + "."
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about document availability for context"""
        try:
            storage_stats = self.storage.get_storage_stats()
            vector_stats = self.vector_db.get_document_stats()
            
            return {
                "total_documents": storage_stats.get("total_documents", 0),
                "total_chunks": vector_stats.get("total_chunks", 0),
                "document_types": storage_stats.get("type_distribution", {}),
                "system_ready": storage_stats.get("total_documents", 0) > 0
            }
        except Exception as e:
            self.logger.error(f"Error getting document stats: {e}")
            return {"system_ready": False, "error": str(e)}


# Global instance for reuse
_enhancement_instance = None

def get_document_enhancement() -> DocumentAwareEnhancement:
    """Get document enhancement instance (singleton pattern)"""
    global _enhancement_instance
    if _enhancement_instance is None:
        _enhancement_instance = DocumentAwareEnhancement()
    return _enhancement_instance