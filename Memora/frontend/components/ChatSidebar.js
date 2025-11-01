import { useState, useEffect } from 'react';

const ChatSidebar = ({ 
    isOpen, 
    onToggle, 
    currentSessionId, 
    onSessionSelect, 
    onNewSession, 
    onDeleteSession,
    onRenameSession 
}) => {
    const [chatSessions, setChatSessions] = useState([]);
    const [renamingSessionId, setRenamingSessionId] = useState(null);
    const [renameValue, setRenameValue] = useState('');

    // Load chat sessions from localStorage
    useEffect(() => {
        const savedSessions = localStorage.getItem('scheduling-agent-chat-sessions');
        if (savedSessions) {
            try {
                const parsedSessions = JSON.parse(savedSessions);
                setChatSessions(parsedSessions);
            } catch (error) {
                console.error('Error loading chat sessions:', error);
                setChatSessions([]);
            }
        }
    }, []);

    // Save sessions to localStorage whenever they change
    useEffect(() => {
        if (chatSessions.length > 0) {
            localStorage.setItem('scheduling-agent-chat-sessions', JSON.stringify(chatSessions));
        }
    }, [chatSessions]);

    const handleRename = (sessionId, newName) => {
        const updatedSessions = chatSessions.map(session => 
            session.id === sessionId 
                ? { ...session, name: newName || `Chat ${new Date(session.createdAt).toLocaleDateString()}` }
                : session
        );
        setChatSessions(updatedSessions);
        onRenameSession(sessionId, newName);
        setRenamingSessionId(null);
        setRenameValue('');
    };

    const handleDelete = (sessionId) => {
        const updatedSessions = chatSessions.filter(session => session.id !== sessionId);
        setChatSessions(updatedSessions);
        onDeleteSession(sessionId);
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString();
        }
    };

    const getSessionPreview = (session) => {
        if (session.messages && session.messages.length > 0) {
            const lastUserMessage = session.messages
                .filter(msg => msg.role === 'user')
                .pop();
            if (lastUserMessage) {
                return lastUserMessage.content.substring(0, 50) + '...';
            }
        }
        return 'New conversation';
    };

    return (
        <>
            {/* Overlay for mobile */}
            {isOpen && (
                <div 
                    className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden" 
                    onClick={onToggle}
                />
            )}
            
            {/* Sidebar */}
            <div className={`fixed left-0 top-20 h-full bg-white border-r border-gray-200 shadow-lg transform transition-transform duration-300 ease-in-out z-50 ${
                isOpen ? 'translate-x-0' : '-translate-x-full'
            } w-80`}>
                
                {/* Sidebar Header */}
                <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-lg font-semibold text-gray-800">💬 Chat Sessions</h2>
                        <button
                            onClick={onToggle}
                            className="p-1 hover:bg-gray-100 rounded text-gray-500"
                        >
                            ✕
                        </button>
                    </div>
                    
                    <button
                        onClick={onNewSession}
                        className="w-full flex items-center space-x-2 p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                        <span>➕</span>
                        <span>New Chat</span>
                    </button>
                </div>

                {/* Sessions List */}
                <div className="flex-1 overflow-y-auto p-2">
                    {chatSessions.length === 0 ? (
                        <div className="text-center text-gray-500 mt-8">
                            <div className="text-4xl mb-2">💭</div>
                            <p className="text-sm">No chat sessions yet</p>
                            <p className="text-xs text-gray-400 mt-1">Start a new conversation to create your first session</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {chatSessions.map((session) => (
                                <div
                                    key={session.id}
                                    className={`group p-3 rounded-lg border cursor-pointer transition-all ${
                                        session.id === currentSessionId
                                            ? 'bg-blue-50 border-blue-200 shadow-sm'
                                            : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                                    }`}
                                    onClick={() => onSessionSelect(session.id)}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1 min-w-0">
                                            {renamingSessionId === session.id ? (
                                                <input
                                                    type="text"
                                                    value={renameValue}
                                                    onChange={(e) => setRenameValue(e.target.value)}
                                                    onBlur={() => handleRename(session.id, renameValue)}
                                                    onKeyPress={(e) => {
                                                        if (e.key === 'Enter') {
                                                            handleRename(session.id, renameValue);
                                                        }
                                                    }}
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="w-full text-sm font-medium bg-transparent border-none outline-none"
                                                    autoFocus
                                                />
                                            ) : (
                                                <h3 className="text-sm font-medium text-gray-800 truncate">
                                                    {session.name}
                                                </h3>
                                            )}
                                            
                                            <p className="text-xs text-gray-500 mt-1 truncate">
                                                {getSessionPreview(session)}
                                            </p>
                                            
                                            <div className="flex items-center justify-between mt-2">
                                                <span className="text-xs text-gray-400">
                                                    {formatDate(session.updatedAt)}
                                                </span>
                                                <span className="text-xs text-gray-400">
                                                    {session.messageCount || 0} messages
                                                </span>
                                            </div>
                                        </div>
                                        
                                        <div className="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setRenamingSessionId(session.id);
                                                    setRenameValue(session.name);
                                                }}
                                                className="p-1 hover:bg-gray-200 rounded text-gray-400 hover:text-gray-600"
                                                title="Rename session"
                                            >
                                                ✏️
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    if (confirm('Delete this chat session?')) {
                                                        handleDelete(session.id);
                                                    }
                                                }}
                                                className="p-1 hover:bg-red-100 rounded text-gray-400 hover:text-red-600"
                                                title="Delete session"
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

                {/* Sidebar Footer */}
                <div className="p-4 border-t border-gray-200 bg-gray-50">
                    <div className="text-xs text-gray-500 space-y-1">
                        <div className="flex items-center space-x-1">
                            <span>💾</span>
                            <span>All chats saved locally</span>
                        </div>
                        <div className="flex items-center space-x-1">
                            <span>🔒</span>
                            <span>Your data stays private</span>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default ChatSidebar;