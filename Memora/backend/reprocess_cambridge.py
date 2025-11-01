#!/usr/bin/env python3
"""
Re-process the Cambridge certification document with OCR support
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))

from data.document_storage import get_document_storage
from data.document_processor import get_document_processor
from data.vector_db import get_vector_database

def reprocess_cambridge_certificate():
    """Re-process the Cambridge certificate with OCR"""
    
    print("🔍 Re-processing Cambridge certification document with OCR...")
    
    # Get instances
    storage = get_document_storage()
    processor = get_document_processor()
    vector_db = get_vector_database()
    
    # Find the Cambridge document
    documents = storage.list_documents()
    cambridge_docs = [doc for doc in documents if 'Cambridge' in doc.title]
    
    if not cambridge_docs:
        print("❌ No Cambridge documents found!")
        return
    
    cambridge_doc = cambridge_docs[0]
    print(f"📄 Found document: {cambridge_doc.title}")
    print(f"📊 Current content length: {len(cambridge_doc.content)} characters")
    
    # Get the file path
    file_path = os.path.join('storage', 'files', cambridge_doc.filename)
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 File path: {file_path}")
    print(f"📏 File size: {os.path.getsize(file_path)} bytes")
    
    # Read the file content
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    # Re-process with OCR
    print("🔄 Re-processing with OCR support...")
    try:
        processed_doc, chunks = processor.process_document(
            file_content, 
            cambridge_doc.filename, 
            "application/pdf"
        )
        
        print(f"✅ OCR processing completed!")
        print(f"📊 Extracted content length: {len(processed_doc.content)} characters")
        print(f"📚 Generated chunks: {len(chunks)}")
        
        if len(processed_doc.content) > 100:
            print(f"📝 Content preview: {processed_doc.content[:300]}...")
            
            # Update the document in storage
            cambridge_doc.content = processed_doc.content
            cambridge_doc.summary = processed_doc.summary
            cambridge_doc.key_insights = processed_doc.key_insights
            cambridge_doc.document_type = processed_doc.document_type
            cambridge_doc.status = processed_doc.status
            
            # Save updated document
            storage.update_document(cambridge_doc.id, {
                'content': cambridge_doc.content,
                'summary': cambridge_doc.summary,
                'key_insights': cambridge_doc.key_insights,
                'document_type': cambridge_doc.document_type,
                'status': cambridge_doc.status
            })
            
            print("💾 Updated document in storage")
            
            # Remove old vector entries and add new ones
            vector_db.delete_document_vectors(cambridge_doc.id)
            vector_db.add_document_vectors(cambridge_doc, chunks)
            
            print("🔍 Updated vector database with new content")
            
            # Test search
            print("\n🧪 Testing search capability...")
            search_results = vector_db.search_documents("cambridge certification", limit=3, similarity_threshold=0.1)
            print(f"Search results: {len(search_results)}")
            for result in search_results:
                print(f"  - {result.title} (score: {result.score:.3f})")
                print(f"    Content: {result.content_snippet[:100]}...")
            
        else:
            print("⚠️ OCR extraction still produced minimal content")
            print("This might indicate a complex PDF format or image quality issues")
            
    except Exception as e:
        print(f"❌ Error during OCR processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reprocess_cambridge_certificate()