import { useState, useEffect } from 'react';
import ChatInterface from '../components/ChatInterface';
import ChatSidebar from '../components/ChatSidebar';
import Link from 'next/link';

// Simple UUID generator
const generateId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

export default function ChatPage() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [chatSessions, setChatSessions] = useState([]);

    // Initialize first session on mount
    useEffect(() => {
        const savedSessions = localStorage.getItem('scheduling-agent-chat-sessions');
        if (savedSessions) {
            try {
                const parsedSessions = JSON.parse(savedSessions);
                setChatSessions(parsedSessions);
                if (parsedSessions.length > 0) {
                    setCurrentSessionId(parsedSessions[0].id);
                } else {
                    createNewSession();
                }
            } catch (error) {
                createNewSession();
            }
        } else {
            createNewSession();
        }
    }, []);

    const createNewSession = () => {
        const newSession = {
            id: generateId(),
            name: `Chat ${new Date().toLocaleDateString()}`,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            messageCount: 0,
            messages: []
        };
        
        const updatedSessions = [newSession, ...chatSessions];
        setChatSessions(updatedSessions);
        localStorage.setItem('scheduling-agent-chat-sessions', JSON.stringify(updatedSessions));
        setCurrentSessionId(newSession.id);
    };

    const handleSessionSelect = (sessionId) => {
        setCurrentSessionId(sessionId);
        setIsSidebarOpen(false); // Close sidebar on mobile after selection
    };

    const handleSessionUpdate = (sessionId, updates) => {
        const updatedSessions = chatSessions.map(session => 
            session.id === sessionId 
                ? { ...session, ...updates }
                : session
        );
        setChatSessions(updatedSessions);
        localStorage.setItem('scheduling-agent-chat-sessions', JSON.stringify(updatedSessions));
    };

    const handleDeleteSession = (sessionId) => {
        const updatedSessions = chatSessions.filter(session => session.id !== sessionId);
        setChatSessions(updatedSessions);
        localStorage.setItem('scheduling-agent-chat-sessions', JSON.stringify(updatedSessions));
        
        // Clear the session data
        const sessionKey = `scheduling-agent-session-${sessionId}`;
        localStorage.removeItem(sessionKey);
        
        // If we deleted the current session, switch to another or create new
        if (sessionId === currentSessionId) {
            if (updatedSessions.length > 0) {
                setCurrentSessionId(updatedSessions[0].id);
            } else {
                createNewSession();
            }
        }
    };

    const handleRenameSession = (sessionId, newName) => {
        const updatedSessions = chatSessions.map(session => 
            session.id === sessionId 
                ? { ...session, name: newName }
                : session
        );
        setChatSessions(updatedSessions);
        localStorage.setItem('scheduling-agent-chat-sessions', JSON.stringify(updatedSessions));
    };

    return (
        <div className="h-screen bg-gray-50 flex flex-col" key="chat-page">
            {/* Fixed Navbar */}
            <nav className="bg-white shadow-sm border-b p-4 fixed top-0 left-0 right-0 z-50">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                        <button
                            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title="Toggle chat sessions"
                        >
                            <div className="w-5 h-5">
                                <div className="w-full h-0.5 bg-gray-600 mb-1"></div>
                                <div className="w-full h-0.5 bg-gray-600 mb-1"></div>
                                <div className="w-full h-0.5 bg-gray-600"></div>
                            </div>
                        </button>
                        <h1 className="text-xl font-semibold">� Memora - AI Scheduling Assistant</h1>
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                            🟢 Local & Private
                        </span>
                    </div>
                    <div className="space-x-4">
                        <Link href="/chat" className="text-blue-600 font-medium border-b-2 border-blue-600 pb-1">
                            💬 Chat
                        </Link>
                        <Link href="/calendar" className="text-gray-600 hover:text-blue-600 transition-colors pb-1">
                            📅 Calendar
                        </Link>
                        <Link href="/documents" className="text-gray-600 hover:text-blue-600 transition-colors pb-1">
                            📚 Documents
                        </Link>
                    </div>
                </div>
            </nav>
            
            {/* Sidebar */}
            <ChatSidebar
                isOpen={isSidebarOpen}
                onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
                currentSessionId={currentSessionId}
                onSessionSelect={handleSessionSelect}
                onNewSession={createNewSession}
                onDeleteSession={handleDeleteSession}
                onRenameSession={handleRenameSession}
            />
            
            {/* Main Content Area */}
            <div className={`flex-1 pt-20 transition-all duration-300 ${
                isSidebarOpen ? 'lg:ml-80' : 'ml-0'
            }`}>
                <div className="max-w-4xl mx-auto h-full">
                    <ChatInterface 
                        key={`chat-interface-${currentSessionId}`}
                        currentSessionId={currentSessionId}
                        onSessionUpdate={handleSessionUpdate}
                    />
                </div>
            </div>
        </div>
    );
}