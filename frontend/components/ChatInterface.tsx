import React, { useState, useRef, useEffect } from 'react';
import { sendMessage, searchDocuments } from '../services/api';
import ReactMarkdown from 'react-markdown';

interface Source {
  document: string;
  page: number;
  snippet: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  isSearch?: boolean;
}

interface ChatInterfaceProps {
  selectedFiles: string[];
  onClearMessages?: () => void; // Used to signal clearing from parent
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ selectedFiles }) => {
  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [searchMessages, setSearchMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'chat' | 'search'>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // We expose a clear method if needed, or just watch for empty file list
  useEffect(() => {
    if (selectedFiles.length === 0 && chatMessages.length > 0) {
      // Optional: auto-clear or just show warning
    }
  }, [selectedFiles, chatMessages.length]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, searchMessages]);

  const handleModeSwitch = (newMode: 'chat' | 'search') => {
    if (newMode === mode) return;
    setMode(newMode);
    setInput('');
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    if (selectedFiles.length === 0) {
      alert("Please select at least one document from the sidebar.");
      return;
    }

    const userMessage = input.trim();
    setInput('');
    
    if (mode === 'chat') {
      setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    } else {
      setSearchMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    }
    
    setIsLoading(true);

    try {
      if (mode === 'chat') {
        const response = await sendMessage(userMessage, selectedFiles);
        setChatMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response.answer,
          sources: response.sources
        }]);
      } else {
        const response = await searchDocuments(userMessage, selectedFiles);
        setSearchMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response.results.length > 0 
            ? `Found ${response.results.length} relevant matches for your search:` 
            : "No direct matches found in your documents.",
          sources: response.results,
          isSearch: true
        }]);
      }
    } catch (error) {
      const errorMessage: Message = { role: 'assistant', content: "Sorry, I encountered an error. Please try again." };
      if (mode === 'chat') setChatMessages(prev => [...prev, errorMessage]);
      else setSearchMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const currentMessages = mode === 'chat' ? chatMessages : searchMessages;

  return (
    <div className="main-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Mode Toggle Header */}
      <div style={{ 
        padding: '16px 24px', 
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        backgroundColor: 'transparent',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={() => handleModeSwitch('chat')}
            className={`mode-toggle-button ${mode === 'chat' ? 'active' : ''}`}
            style={{ flex: 1, padding: '10px' }}
          >
            Chat Mode
          </button>
          <button 
            onClick={() => handleModeSwitch('search')}
            className={`mode-toggle-button ${mode === 'search' ? 'active' : ''}`}
            style={{ flex: 1, padding: '10px' }}
          >
            Search Mode
          </button>
        </div>
        <div style={{ 
          fontSize: '0.75rem', 
          textTransform: 'uppercase', 
          letterSpacing: '0.05em', 
          fontWeight: 700,
          color: 'var(--text-secondary)',
          textAlign: 'center',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span>{mode === 'chat' ? 'AI Assistant' : 'Semantic Search'}</span>
          <span style={{ opacity: 0.3 }}>|</span>
          <span style={{ color: selectedFiles.length > 0 ? '#818cf8' : '#ef4444' }}>
            {selectedFiles.length} File(s) Active
          </span>
        </div>
      </div>


      <div className="chat-messages" style={{ flex: 1, overflowY: 'auto' }}>
        {currentMessages.length === 0 ? (
          <div style={{ textAlign: 'center', marginTop: '80px', padding: '0 40px', color: 'var(--secondary-text)' }}>
            <h2 style={{ color: 'var(--foreground)', marginBottom: '12px' }}>
              {mode === 'chat' ? 'ContextAI Chat' : 'ContextAI Search'}
            </h2>
            {selectedFiles.length === 0 ? (
              <p style={{ color: '#ff4d4f', fontWeight: 500 }}>
                ⚠️ Please select at least one document from the sidebar to start.
              </p>
            ) : (
              <p style={{ lineHeight: '1.6' }}>
                {mode === 'chat' 
                  ? 'Ask complex questions and get AI-powered answers grounded in your documents.' 
                  : 'Directly search for phrases and keywords. No AI processing, just pure retrieval.'}
              </p>
            )}
          </div>
        ) : (
          currentMessages.map((msg, index) => (
            <div key={index} className={`message ${msg.role === 'user' ? 'user' : 'ai'}`}>
              <div className="message-sender">{msg.role === 'user' ? 'You' : (msg.isSearch ? 'Search Result' : 'Assistant')}</div>
              <div className="message-bubble">
                {msg.role === 'user' ? (
                  msg.content
                ) : (
                  <div className="markdown-body">
                    <ReactMarkdown children={msg.content} />
                  </div>
                )}
                
                {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                  <div style={{ 
                    marginTop: '16px', 
                    paddingTop: '12px', 
                    borderTop: '1px solid rgba(0,0,0,0.06)',
                    fontSize: '0.85rem',
                    color: 'var(--secondary-text)'
                  }}>
                    <div style={{ 
                      fontWeight: 600, 
                      color: 'var(--foreground)', 
                      marginBottom: '8px',
                      fontSize: '0.9rem' 
                    }}>
                      {msg.isSearch ? 'Direct References:' : 'Top References:'}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {msg.sources.map((source, i) => (
                        <div key={i} style={{ paddingLeft: '2px' }}>
                          <div style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '6px', 
                            marginBottom: '2px',
                            color: 'var(--foreground)',
                            fontWeight: 500
                          }}>
                            <span>•</span>
                            <span>{source.document} — Page {source.page}</span>
                          </div>
                          <div style={{ 
                            fontSize: '0.8rem', 
                            opacity: 0.7,
                            paddingLeft: '14px',
                            lineHeight: '1.5',
                            color: 'var(--secondary-text)'
                          }}>
                            "{source.snippet}"
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message ai">
            <div className="message-sender">{mode === 'chat' ? 'Assistant' : 'Search Engine'}</div>
            <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--secondary-text)' }}>
              {mode === 'chat' ? 'Thinking' : 'Searching'}
              <div className="loading-dots">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <div className="input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder={selectedFiles.length === 0 ? "Select a file to begin..." : (mode === 'chat' ? "Ask a question..." : "Enter keywords...")}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            disabled={isLoading || selectedFiles.length === 0}
          />
          <button 
            className="send-button" 
            onClick={handleSend}
            disabled={isLoading || !input.trim() || selectedFiles.length === 0}
          >
            {mode === 'chat' ? 'Send' : 'Search'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
