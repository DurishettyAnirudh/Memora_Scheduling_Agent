import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const ChatInterface = ({ currentSessionId, onSessionUpdate }) => {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    // Load specific session messages
    useEffect(() => {
        if (currentSessionId) {
            const sessionKey = `scheduling-agent-session-${currentSessionId}`;
            const savedMessages = localStorage.getItem(sessionKey);
            
            if (savedMessages) {
                try {
                    const parsedMessages = JSON.parse(savedMessages);
                    setMessages(parsedMessages);
                } catch (error) {
                    console.error('Error loading session messages:', error);
                    setMessages([]);
                }
            } else {
                // New session - start empty
                setMessages([]);
            }
        }
    }, [currentSessionId]);

    // Save session messages whenever they change
    useEffect(() => {
        if (currentSessionId && messages.length > 0) {
            const sessionKey = `scheduling-agent-session-${currentSessionId}`;
            localStorage.setItem(sessionKey, JSON.stringify(messages));
            
            // Update session metadata
            if (onSessionUpdate) {
                onSessionUpdate(currentSessionId, {
                    messages: messages,
                    messageCount: messages.length,
                    updatedAt: new Date().toISOString()
                });
            }
        }
    }, [messages, currentSessionId, onSessionUpdate]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userMessage = { role: 'user', content: inputValue };
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await axios.post('http://localhost:8000/chat', {
                message: inputValue
            });

            const assistantMessage = { 
                role: 'assistant', 
                content: response.data.response 
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage = { 
                role: 'assistant', 
                content: '❌ Sorry, I encountered an error. Please make sure:\n• The backend server is running\n• Ollama is running with qwen2.5:7b model\n\nTry again in a moment!' 
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    // Function to clear current session
    const clearCurrentSession = () => {
        if (currentSessionId) {
            const sessionKey = `scheduling-agent-session-${currentSessionId}`;
            localStorage.removeItem(sessionKey);
            setMessages([]);
            
            if (onSessionUpdate) {
                onSessionUpdate(currentSessionId, {
                    messages: [],
                    messageCount: 0,
                    updatedAt: new Date().toISOString()
                });
            }
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Chat History - Scrollable Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{maxHeight: 'calc(100vh - 200px)'}}>
                {messages.length === 0 && (
                    <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border-l-4 border-blue-400 shadow-sm">
                        <h3 className="font-bold text-xl text-gray-800 mb-3">� Meet Memora - Your Personal AI Assistant!</h3>
                        <p className="text-gray-600 mb-4">
                            Powered by <strong>Qwen 2.5 7B</strong> running locally on your machine for complete privacy.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-white p-4 rounded-lg">
                                <h4 className="font-semibold text-blue-600 mb-2">📅 Smart Scheduling</h4>
                                <ul className="text-sm text-gray-600 space-y-1">
                                    <li>• "Schedule meeting tomorrow at 3pm"</li>
                                    <li>• "What do I have today?"</li>
                                    <li>• "Delete all tasks for tomorrow"</li>
                                    <li>• "Find my doctor appointments"</li>
                                </ul>
                            </div>
                            <div className="bg-white p-4 rounded-lg">
                                <h4 className="font-semibold text-purple-600 mb-2">💬 Natural Conversation</h4>
                                <ul className="text-sm text-gray-600 space-y-1">
                                    <li>• Ask me any questions</li>
                                    <li>• Get explanations & advice</li>
                                    <li>• Discuss any topic</li>
                                    <li>• Just chat naturally!</li>
                                </ul>
                            </div>
                        </div>
                        <p className="text-sm text-gray-500 mt-4 text-center">
                            Start typing below to begin our conversation...
                        </p>
                    </div>
                )}
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`p-4 rounded-lg max-w-[80%] ${
                            message.role === 'user'
                                ? 'bg-blue-500 text-white ml-auto'
                                : 'bg-gray-100 text-gray-800 mr-auto'
                        }`}
                    >
                        <pre className="whitespace-pre-wrap font-sans">{message.content}</pre>
                    </div>
                ))}
                {isLoading && (
                    <div className="bg-gray-100 text-gray-800 mr-auto max-w-[80%] p-4 rounded-lg">
                        <div className="flex items-center space-x-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                            <span>Thinking...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            
            {/* Fixed Chat Input Bar */}
            <div className="border-t bg-white p-4 shadow-lg">
                <div className="max-w-4xl mx-auto">
                    <div className="flex space-x-2 mb-2">
                        <button
                            onClick={clearCurrentSession}
                            className="text-xs text-gray-500 hover:text-red-500 transition-colors"
                            title="Clear current session"
                        >
                            🗑️ Clear Session
                        </button>
                        <span className="text-xs text-gray-400">
                            💾 Session auto-saved • {messages.length} messages
                        </span>
                    </div>
                    <form onSubmit={sendMessage} className="flex space-x-2">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="Ask me anything or manage your schedule... (e.g., 'Explain quantum physics' or 'Schedule meeting tomorrow at 3pm')"
                            className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !inputValue.trim()}
                            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {isLoading ? '⏳' : 'Send'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;