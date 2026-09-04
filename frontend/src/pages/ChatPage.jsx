import React, { useState } from 'react';
import ChatWindow from '../components/ChatWindow';
import { sendChatMessage } from '../lib/api';

export default function ChatPage({ user }) {
  const [messages, setMessages] = useState([]);
  const [currentSources, setCurrentSources] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (userText) => {
    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await sendChatMessage(userText);
      const assistantMsg = {
        id: data.query_id || Date.now().toString(),
        queryId: data.query_id,
        sender: 'assistant',
        text: data.answer,
        sources: data.sources || [],
        confidence: data.confidence,
        isFallback: data.is_fallback,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      if (data.sources && data.sources.length > 0) {
        setCurrentSources(data.sources);
      }
    } catch (err) {
      console.error('Chat error:', err);
      let errorDetail = "System could not process request — please verify backend API server connection.";
      if (err.response) {
        if (err.response.status === 401) {
          errorDetail = "Session expired or invalid authentication token. Please refresh or log in again to continue.";
        } else if (err.response.data && err.response.data.detail) {
          errorDetail = `Request failed (${err.response.status}): ${err.response.data.detail}`;
        } else {
          errorDetail = `Server error (${err.response.status}). Please check backend API server status.`;
        }
      } else if (err.request) {
        errorDetail = "Backend API server is unreachable. Please verify that the FastAPI backend is running on http://localhost:8000.";
      }

      const errorMsg = {
        id: Date.now().toString(),
        sender: 'assistant',
        isError: true,
        text: errorDetail,
        sources: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setCurrentSources([]);
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#080B14]">
      <ChatWindow
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        currentSources={currentSources}
        onClearChat={handleClearChat}
      />
    </div>
  );
}
