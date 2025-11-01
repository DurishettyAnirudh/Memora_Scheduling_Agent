import { useState } from 'react';

const DocumentSearch = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [searchPerformed, setSearchPerformed] = useState(false);
    const [searchFilters, setSearchFilters] = useState({
        limit: 10,
        similarity_threshold: 0.7,
        document_type: ''
    });

    const documentTypes = [
        { value: '', label: 'All Types' },
        { value: 'GENERAL', label: 'General' },
        { value: 'PROJECT', label: 'Project' },
        { value: 'MEETING_NOTES', label: 'Meeting Notes' },
        { value: 'ACHIEVEMENT', label: 'Achievement' },
        { value: 'SKILL', label: 'Skill' },
        { value: 'REFERENCE', label: 'Reference' }
    ];

    const handleSearch = async (e) => {
        e.preventDefault();
        
        if (!searchQuery.trim()) {
            return;
        }

        setIsSearching(true);
        setSearchPerformed(true);

        try {
            const params = new URLSearchParams({
                limit: searchFilters.limit.toString(),
                similarity_threshold: searchFilters.similarity_threshold.toString()
            });

            if (searchFilters.document_type) {
                params.append('document_type', searchFilters.document_type);
            }

            const response = await fetch(
                `http://127.0.0.1:8000/documents/search/${encodeURIComponent(searchQuery)}?${params}`,
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (response.ok) {
                const results = await response.json();
                setSearchResults(results);
            } else {
                console.error('Search failed:', response.statusText);
                setSearchResults([]);
            }
        } catch (error) {
            console.error('Search error:', error);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    };

    const formatSimilarityScore = (score) => {
        return (score * 100).toFixed(1) + '%';
    };

    const getDocumentTypeIcon = (type) => {
        const iconMap = {
            'GENERAL': '📄',
            'PROJECT': '🚀',
            'MEETING_NOTES': '📝',
            'ACHIEVEMENT': '🏆',
            'SKILL': '🎯',
            'REFERENCE': '📚'
        };
        return iconMap[type] || '📄';
    };

    return (
        <div className="space-y-6">
            {/* Search Form */}
            <div className="bg-white p-6 rounded-lg border">
                <form onSubmit={handleSearch} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Search Query
                        </label>
                        <div className="flex space-x-2">
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search your documents... (e.g., 'project planning', 'meeting notes', 'technical skills')"
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                            <button
                                type="submit"
                                disabled={isSearching || !searchQuery.trim()}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                            >
                                {isSearching ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                        <span>Searching...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>🔍</span>
                                        <span>Search</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Search Filters */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                                Document Type
                            </label>
                            <select
                                value={searchFilters.document_type}
                                onChange={(e) => setSearchFilters({...searchFilters, document_type: e.target.value})}
                                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                                {documentTypes.map((type) => (
                                    <option key={type.value} value={type.value}>
                                        {type.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                        
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                                Max Results
                            </label>
                            <select
                                value={searchFilters.limit}
                                onChange={(e) => setSearchFilters({...searchFilters, limit: parseInt(e.target.value)})}
                                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                                <option value={5}>5 results</option>
                                <option value={10}>10 results</option>
                                <option value={20}>20 results</option>
                                <option value={50}>50 results</option>
                            </select>
                        </div>
                        
                        <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                                Similarity Threshold
                            </label>
                            <select
                                value={searchFilters.similarity_threshold}
                                onChange={(e) => setSearchFilters({...searchFilters, similarity_threshold: parseFloat(e.target.value)})}
                                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                                <option value={0.5}>50% - Broad</option>
                                <option value={0.6}>60% - Moderate</option>
                                <option value={0.7}>70% - Precise</option>
                                <option value={0.8}>80% - Strict</option>
                            </select>
                        </div>
                    </div>
                </form>
            </div>

            {/* Search Results */}
            {searchPerformed && (
                <div className="bg-white rounded-lg border">
                    <div className="p-4 border-b">
                        <h3 className="text-lg font-medium">
                            🔍 Search Results
                            {searchResults.length > 0 && (
                                <span className="text-sm text-gray-500 ml-2">
                                    ({searchResults.length} found)
                                </span>
                            )}
                        </h3>
                    </div>

                    <div className="divide-y">
                        {searchResults.length === 0 ? (
                            <div className="p-8 text-center text-gray-500">
                                <div className="text-4xl mb-2">🔍</div>
                                <p>No documents found matching your search.</p>
                                <p className="text-sm mt-1">Try different keywords or lower the similarity threshold.</p>
                            </div>
                        ) : (
                            searchResults.map((result, index) => (
                                <div key={index} className="p-4 hover:bg-gray-50 transition-colors">
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center space-x-2 mb-2">
                                                <span className="text-lg">
                                                    {getDocumentTypeIcon(result.metadata?.document_type)}
                                                </span>
                                                <h4 className="font-medium text-gray-900">
                                                    {result.title}
                                                </h4>
                                                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                                                    {formatSimilarityScore(result.score)} match
                                                </span>
                                            </div>
                                            
                                            <p className="text-sm text-gray-600 mb-2">
                                                {result.content_snippet}
                                            </p>
                                            
                                            <div className="flex items-center space-x-4 text-xs text-gray-500">
                                                <span>📄 {result.metadata?.file_name}</span>
                                                <span>🏷️ {result.metadata?.document_type?.replace('_', ' ')}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Search Tips */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-800 mb-2">🔍 Search Tips</h4>
                <ul className="text-xs text-blue-700 space-y-1">
                    <li>• Use natural language queries like "project deadlines" or "team meeting notes"</li>
                    <li>• Lower similarity threshold for broader results, higher for more precise matches</li>
                    <li>• Search works on document content, not just titles</li>
                    <li>• Results are ranked by semantic similarity to your query</li>
                </ul>
            </div>
        </div>
    );
};

export default DocumentSearch;