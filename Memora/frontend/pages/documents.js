import { useState, useEffect } from 'react';
import Link from 'next/link';
import DocumentUpload from '../components/DocumentUpload';
import DocumentSearch from '../components/DocumentSearch'; 
import DocumentList from '../components/DocumentList';

export default function DocumentsPage() {
    const [activeTab, setActiveTab] = useState('upload');
    const [documentStats, setDocumentStats] = useState({
        total_documents: 0,
        system_ready: false
    });

    // Load document statistics
    useEffect(() => {
        fetchDocumentStats();
    }, []);

    const fetchDocumentStats = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/documents/stats/overview');
            if (response.ok) {
                const data = await response.json();
                setDocumentStats({
                    total_documents: data.storage?.total_documents || 0,
                    system_ready: data.system_status === 'operational'
                });
            }
        } catch (error) {
            console.error('Error fetching document stats:', error);
        }
    };

    const tabs = [
        { id: 'upload', name: '📤 Upload', description: 'Add new documents' },
        { id: 'search', name: '🔍 Search', description: 'Find documents' },
        { id: 'manage', name: '📋 Manage', description: 'View and organize' }
    ];

    return (
        <div className="h-screen bg-gray-50 flex flex-col">
            {/* Fixed Navbar */}
            <nav className="bg-white shadow-sm border-b p-4 fixed top-0 left-0 right-0 z-50">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                        <h1 className="text-xl font-semibold">🤖 Memora - AI Scheduling Assistant</h1>
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                            🟢 Local & Private
                        </span>
                        {documentStats.total_documents > 0 && (
                            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                                📚 {documentStats.total_documents} documents
                            </span>
                        )}
                    </div>
                    <div className="space-x-4">
                        <Link href="/chat" className="text-gray-600 hover:text-blue-600 transition-colors pb-1">
                            💬 Chat
                        </Link>
                        <Link href="/calendar" className="text-gray-600 hover:text-blue-600 transition-colors pb-1">
                            📅 Calendar
                        </Link>
                        <Link href="/documents" className="text-blue-600 font-medium border-b-2 border-blue-600 pb-1">
                            📚 Documents
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <div className="flex-1 pt-20 px-4">
                <div className="max-w-6xl mx-auto h-full">
                    {/* Document System Status */}
                    <div className="mb-6">
                        <div className={`p-4 rounded-lg ${
                            documentStats.system_ready 
                                ? 'bg-green-50 border border-green-200' 
                                : 'bg-yellow-50 border border-yellow-200'
                        }`}>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <div className={`w-3 h-3 rounded-full ${
                                        documentStats.system_ready ? 'bg-green-500' : 'bg-yellow-500'
                                    }`}></div>
                                    <h2 className="text-lg font-semibold">
                                        📚 Document Awareness System
                                    </h2>
                                </div>
                                <div className="text-sm text-gray-600">
                                    {documentStats.total_documents > 0 
                                        ? `${documentStats.total_documents} documents indexed`
                                        : 'Ready to index documents'
                                    }
                                </div>
                            </div>
                            <p className="text-sm text-gray-600 mt-2">
                                {documentStats.system_ready
                                    ? 'Document awareness is active. Upload documents to enhance Memora\'s responses with your personal knowledge base.'
                                    : 'Upload your first document to enable document-aware scheduling assistance.'
                                }
                            </p>
                        </div>
                    </div>

                    {/* Tab Navigation */}
                    <div className="border-b border-gray-200 mb-6">
                        <nav className="-mb-px flex space-x-8">
                            {tabs.map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                                        activeTab === tab.id
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                                >
                                    <div className="flex flex-col items-center">
                                        <span>{tab.name}</span>
                                        <span className="text-xs text-gray-400 mt-1">{tab.description}</span>
                                    </div>
                                </button>
                            ))}
                        </nav>
                    </div>

                    {/* Tab Content */}
                    <div className="flex-1 overflow-hidden">
                        {activeTab === 'upload' && (
                            <DocumentUpload onUploadSuccess={fetchDocumentStats} />
                        )}
                        
                        {activeTab === 'search' && (
                            <DocumentSearch />
                        )}
                        
                        {activeTab === 'manage' && (
                            <DocumentList onDocumentChange={fetchDocumentStats} />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}