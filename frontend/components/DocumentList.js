import { useState, useEffect } from 'react';

const DocumentList = ({ onDocumentChange }) => {
    const [documents, setDocuments] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [deleteConfirm, setDeleteConfirm] = useState(null);
    const [filters, setFilters] = useState({
        document_type: '',
        status: '',
        limit: 20
    });

    useEffect(() => {
        fetchDocuments();
    }, [filters]);

    const fetchDocuments = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams();
            
            if (filters.document_type) {
                params.append('document_type', filters.document_type);
            }
            if (filters.status) {
                params.append('status', filters.status);
            }
            if (filters.limit) {
                params.append('limit', filters.limit.toString());
            }

            const response = await fetch(`http://127.0.0.1:8000/documents/?${params}`);
            
            if (response.ok) {
                const data = await response.json();
                setDocuments(data);
            } else {
                setError('Failed to fetch documents');
            }
        } catch (err) {
            setError('Error connecting to server');
            console.error('Fetch error:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (documentId, title) => {
        try {
            const response = await fetch(`http://127.0.0.1:8000/documents/${documentId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setDocuments(documents.filter(doc => doc.id !== documentId));
                setDeleteConfirm(null);
                if (onDocumentChange) {
                    onDocumentChange();
                }
            } else {
                const error = await response.json();
                alert(`Failed to delete document: ${error.detail || 'Unknown error'}`);
            }
        } catch (err) {
            console.error('Delete error:', err);
            alert('Error deleting document');
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const getStatusIcon = (status) => {
        const statusMap = {
            'INDEXED': '✅',
            'PROCESSING': '⏳',
            'ERROR': '❌',
            'PENDING': '📝'
        };
        return statusMap[status] || '📄';
    };

    const getTypeIcon = (type) => {
        const typeMap = {
            'GENERAL': '📄',
            'PROJECT': '🚀',
            'MEETING_NOTES': '📝',
            'ACHIEVEMENT': '🏆',
            'SKILL': '🎯',
            'REFERENCE': '📚'
        };
        return typeMap[type] || '📄';
    };

    const documentTypes = [
        { value: '', label: 'All Types' },
        { value: 'GENERAL', label: 'General' },
        { value: 'PROJECT', label: 'Project' },
        { value: 'MEETING_NOTES', label: 'Meeting Notes' },
        { value: 'ACHIEVEMENT', label: 'Achievement' },
        { value: 'SKILL', label: 'Skill' },
        { value: 'REFERENCE', label: 'Reference' }
    ];

    const statusOptions = [
        { value: '', label: 'All Status' },
        { value: 'INDEXED', label: 'Indexed' },
        { value: 'PROCESSING', label: 'Processing' },
        { value: 'ERROR', label: 'Error' },
        { value: 'PENDING', label: 'Pending' }
    ];

    return (
        <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white p-4 rounded-lg border">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Document Type
                        </label>
                        <select
                            value={filters.document_type}
                            onChange={(e) => setFilters({...filters, document_type: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {documentTypes.map((type) => (
                                <option key={type.value} value={type.value}>
                                    {type.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Status
                        </label>
                        <select
                            value={filters.status}
                            onChange={(e) => setFilters({...filters, status: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {statusOptions.map((status) => (
                                <option key={status.value} value={status.value}>
                                    {status.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Results Limit
                        </label>
                        <select
                            value={filters.limit}
                            onChange={(e) => setFilters({...filters, limit: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value={10}>10 documents</option>
                            <option value={20}>20 documents</option>
                            <option value={50}>50 documents</option>
                            <option value={100}>100 documents</option>
                        </select>
                    </div>

                    <div className="flex items-end">
                        <button
                            onClick={fetchDocuments}
                            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            🔄 Refresh
                        </button>
                    </div>
                </div>
            </div>

            {/* Document List */}
            <div className="bg-white rounded-lg border">
                <div className="p-4 border-b">
                    <h3 className="text-lg font-medium">
                        📋 Your Documents
                        {!isLoading && (
                            <span className="text-sm text-gray-500 ml-2">
                                ({documents.length} {documents.length === 1 ? 'document' : 'documents'})
                            </span>
                        )}
                    </h3>
                </div>

                {isLoading ? (
                    <div className="p-8 text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                        <p className="text-gray-500">Loading documents...</p>
                    </div>
                ) : error ? (
                    <div className="p-8 text-center text-red-600">
                        <div className="text-4xl mb-2">❌</div>
                        <p>{error}</p>
                        <button
                            onClick={fetchDocuments}
                            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        >
                            Try Again
                        </button>
                    </div>
                ) : documents.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                        <div className="text-4xl mb-2">📚</div>
                        <p>No documents found.</p>
                        <p className="text-sm mt-1">Upload your first document to get started!</p>
                    </div>
                ) : (
                    <div className="divide-y">
                        {documents.map((doc) => (
                            <div key={doc.id} className="p-4 hover:bg-gray-50 transition-colors">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-2 mb-2">
                                            <span className="text-lg">
                                                {getTypeIcon(doc.document_type)}
                                            </span>
                                            <h4 className="font-medium text-gray-900">
                                                {doc.title}
                                            </h4>
                                            <span className={`text-xs px-2 py-1 rounded-full ${
                                                doc.status === 'INDEXED' ? 'bg-green-100 text-green-800' :
                                                doc.status === 'PROCESSING' ? 'bg-yellow-100 text-yellow-800' :
                                                doc.status === 'ERROR' ? 'bg-red-100 text-red-800' :
                                                'bg-gray-100 text-gray-800'
                                            }`}>
                                                {getStatusIcon(doc.status)} {doc.status}
                                            </span>
                                        </div>

                                        {doc.summary && (
                                            <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                                                {doc.summary}
                                            </p>
                                        )}

                                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                                            <span>📄 {doc.filename}</span>
                                            <span>📅 {formatDate(doc.upload_date)}</span>
                                            <span>💾 {formatFileSize(doc.file_size)}</span>
                                            <span>🏷️ {doc.document_type.replace('_', ' ')}</span>
                                        </div>

                                        {doc.key_insights && doc.key_insights.length > 0 && (
                                            <div className="mt-2">
                                                <div className="flex flex-wrap gap-1">
                                                    {doc.key_insights.slice(0, 3).map((insight, idx) => (
                                                        <span
                                                            key={idx}
                                                            className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded"
                                                        >
                                                            💡 {insight}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex items-center space-x-2 ml-4">
                                        <button
                                            onClick={() => setDeleteConfirm({ id: doc.id, title: doc.title })}
                                            className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                                            title="Delete document"
                                        >
                                            🗑️
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Delete Confirmation Modal */}
            {deleteConfirm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
                        <h3 className="text-lg font-medium mb-4">Confirm Delete</h3>
                        <p className="text-gray-600 mb-6">
                            Are you sure you want to delete <strong>"{deleteConfirm.title}"</strong>? 
                            This action cannot be undone.
                        </p>
                        <div className="flex space-x-3 justify-end">
                            <button
                                onClick={() => setDeleteConfirm(null)}
                                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => handleDelete(deleteConfirm.id, deleteConfirm.title)}
                                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DocumentList;