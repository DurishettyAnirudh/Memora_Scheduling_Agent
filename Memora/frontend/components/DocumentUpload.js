import { useState, useRef } from 'react';

const DocumentUpload = ({ onUploadSuccess }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [customTitle, setCustomTitle] = useState('');
    const fileInputRef = useRef(null);

    const allowedTypes = {
        'application/pdf': 'PDF files',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word documents',
        'text/plain': 'Text files'
    };

    const handleDragEnter = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        
        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileUpload(file);
        }
    };

    const handleFileUpload = async (file) => {
        // Validate file type
        if (!allowedTypes[file.type]) {
            setUploadStatus({
                type: 'error',
                message: `Unsupported file type. Supported: ${Object.values(allowedTypes).join(', ')}`
            });
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            setUploadStatus({
                type: 'error',
                message: 'File size must be less than 10MB'
            });
            return;
        }

        setUploadStatus({ type: 'loading', message: 'Uploading document...' });
        setUploadProgress(0);

        try {
            const formData = new FormData();
            formData.append('file', file);
            
            if (customTitle.trim()) {
                formData.append('title', customTitle.trim());
            }

            const response = await fetch('http://127.0.0.1:8000/documents/upload', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const result = await response.json();
                setUploadStatus({
                    type: result.success ? 'success' : 'warning',
                    message: result.message,
                    details: result
                });
                setCustomTitle('');
                if (onUploadSuccess) {
                    onUploadSuccess();
                }
            } else {
                const error = await response.json();
                setUploadStatus({
                    type: 'error',
                    message: `Upload failed: ${error.detail || 'Unknown error'}`
                });
            }
        } catch (error) {
            console.error('Upload error:', error);
            setUploadStatus({
                type: 'error',
                message: `Upload failed: ${error.message}`
            });
        }
    };

    return (
        <div className="space-y-6">
            {/* Upload Area */}
            <div 
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    isDragging 
                        ? 'border-blue-400 bg-blue-50' 
                        : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
            >
                <div className="space-y-4">
                    <div className="text-6xl">📄</div>
                    <div>
                        <h3 className="text-lg font-medium text-gray-900">
                            Upload Document
                        </h3>
                        <p className="text-sm text-gray-500 mt-1">
                            Drag and drop your files here, or click to browse
                        </p>
                    </div>
                    
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        📁 Choose File
                    </button>
                    
                    <input
                        ref={fileInputRef}
                        type="file"
                        className="hidden"
                        accept=".pdf,.docx,.txt"
                        onChange={handleFileSelect}
                    />
                </div>
                
                <div className="mt-4 text-xs text-gray-400">
                    Supported formats: PDF, Word (.docx), Text (.txt) • Max size: 10MB
                </div>
            </div>

            {/* Custom Title Input */}
            <div className="bg-white p-4 rounded-lg border">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Custom Title (Optional)
                </label>
                <input
                    type="text"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    placeholder="Override the filename with a custom title..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                    If left empty, the filename will be used as the title
                </p>
            </div>

            {/* Upload Status */}
            {uploadStatus && (
                <div className={`p-4 rounded-lg ${
                    uploadStatus.type === 'success' ? 'bg-green-50 border border-green-200' :
                    uploadStatus.type === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
                    uploadStatus.type === 'error' ? 'bg-red-50 border border-red-200' :
                    'bg-blue-50 border border-blue-200'
                }`}>
                    <div className="flex items-start">
                        <div className="flex-shrink-0">
                            {uploadStatus.type === 'success' && <span className="text-green-500">✅</span>}
                            {uploadStatus.type === 'warning' && <span className="text-yellow-500">⚠️</span>}
                            {uploadStatus.type === 'error' && <span className="text-red-500">❌</span>}
                            {uploadStatus.type === 'loading' && (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                            )}
                        </div>
                        <div className="ml-3 flex-1">
                            <p className={`text-sm font-medium ${
                                uploadStatus.type === 'success' ? 'text-green-800' :
                                uploadStatus.type === 'warning' ? 'text-yellow-800' :
                                uploadStatus.type === 'error' ? 'text-red-800' :
                                'text-blue-800'
                            }`}>
                                {uploadStatus.message}
                            </p>
                            
                            {uploadStatus.details && (
                                <div className="mt-2 text-xs text-gray-600">
                                    <p>Success: {uploadStatus.details.success ? 'Yes' : 'No'}</p>
                                    <p>Document ID: {uploadStatus.details.document_id}</p>
                                    {uploadStatus.details.document_type && (
                                        <p>Type: {uploadStatus.details.document_type}</p>
                                    )}
                                </div>
                            )}
                        </div>
                        
                        <button
                            onClick={() => setUploadStatus(null)}
                            className="flex-shrink-0 ml-4 text-gray-400 hover:text-gray-600"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            {/* Upload Tips */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-yellow-800 mb-2">💡 Upload Tips</h4>
                <ul className="text-xs text-yellow-700 space-y-1">
                    <li>• Upload project documents, meeting notes, or reference materials</li>
                    <li>• Memora will extract text content and make it searchable</li>
                    <li>• Documents enhance chat responses with relevant context</li>
                    <li>• All processing happens locally for privacy</li>
                </ul>
            </div>
        </div>
    );
};

export default DocumentUpload;