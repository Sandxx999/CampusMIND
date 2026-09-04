import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import AdminDashboard from './pages/AdminDashboard';
import Header from './components/Header';
import { getStoredUser, logoutUser, switchUserRole } from './lib/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'admin'

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

  const handleRoleChange = async (newRole) => {
    if (!user) return;
    try {
      const updatedUser = await switchUserRole(user.username, newRole);
      setUser(updatedUser);
    } catch (err) {
      console.error('Role change error:', err);
      // Fallback local update
      const updatedUser = { ...user, role: newRole };
      localStorage.setItem('campusmind_user', JSON.stringify(updatedUser));
      setUser(updatedUser);
    }
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
        onRoleChange={handleRoleChange}
      />

      {/* Main View Container */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {activeTab === 'chat' ? (
          <ChatPage user={user} />
        ) : (
          <AdminDashboard user={user} />
        )}
      </main>
    </div>
  );
}
