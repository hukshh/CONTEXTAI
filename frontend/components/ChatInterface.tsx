import React, { useState, useRef, useEffect } from 'react';
import { sendMessage } from '../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await sendMessage(userMessage);
      setMessages(prev => [...prev, { role: 'assistant', content: response.answer }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="main-panel">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', marginTop: '100px', color: 'var(--secondary-text)' }}>
            <h2 style={{ color: 'var(--foreground)', marginBottom: '10px' }}>ContextAI Assistant</h2>
            <p>Upload a PDF to get started. I can help you understand your documents.</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role === 'user' ? 'user' : 'ai'}`}>
              <div className="message-sender">{msg.role === 'user' ? 'You' : 'Assistant'}</div>
              <div className="message-bubble">{msg.content}</div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message ai">
            <div className="message-sender">Assistant</div>
            <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--secondary-text)' }}>
              Thinking
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
            placeholder="Ask a question about your documents..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            disabled={isLoading}
          />
          <button 
            className="send-button" 
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
