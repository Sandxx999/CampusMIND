import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import AdminDashboard from './pages/AdminDashboard';
import InstitutionalHub from './pages/InstitutionalHub';
import Header from './components/Header';
import { getStoredUser, logoutUser } from './lib/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat', 'hub', 'admin'

  useEffect(() => {
    const existingUser = getStoredUser();
    if (existingUser) {
      setUser(existingUser);
    }
  }, []);

  const handleLogout = () => {
    logoutUser();
    setUser(null);
  };

  if (!user) {
    return <LoginPage onLoginSuccess={(userData) => setUser(userData)} />;
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#080B14] text-[#F8FAFC] overflow-hidden selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Header Bar */}
      <Header
        user={user}
        onLogout={handleLogout}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
      />

      {/* Main View Container */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {activeTab === 'chat' ? (
          <ChatPage user={user} />
        ) : activeTab === 'hub' ? (
          <InstitutionalHub user={user} />
        ) : (
          <AdminDashboard user={user} />
        )}
      </main>
    </div>
  );
}
