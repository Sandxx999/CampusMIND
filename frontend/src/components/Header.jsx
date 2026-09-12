import React from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  BookOpen,
  Cpu,
  GraduationCap,
  LogOut,
  ShieldCheck,
  Sparkles,
  UserCheck,
} from 'lucide-react';

const ROLE_DISPLAY = {
  student: { icon: GraduationCap, label: 'Student Role', badge: 'bg-sky-500/15 text-sky-700 border-sky-300/60' },
  faculty: { icon: UserCheck, label: 'Faculty Role', badge: 'bg-purple-500/15 text-purple-700 border-purple-300/60' },
  admin: { icon: ShieldCheck, label: 'Admin Role', badge: 'bg-amber-500/15 text-amber-700 border-amber-300/60' },
};

export default function Header({ user, onLogout, activeTab, onSelectTab }) {
  const currentRole = ROLE_DISPLAY[user?.role] || ROLE_DISPLAY.student;
  const CurrentRoleIcon = currentRole.icon;

  return (
    <header className="glass-mirror-navbar sticky top-0 z-50 px-4 py-3.5 transition-all duration-300 md:px-8">
      <div className="mx-auto flex max-w-[1700px] items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <motion.div whileHover={{ scale: 1.08, rotate: 4 }} className="relative">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-sky-400 via-indigo-500 to-purple-500 p-[1.5px] shadow-lg shadow-sky-500/20">
              <div className="flex h-full w-full items-center justify-center rounded-[14px] bg-white/90 backdrop-blur-md">
                <Sparkles className="w-5.5 h-5.5 animate-pulse text-sky-600" />
              </div>
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-white bg-emerald-500 shadow-sm" title="RAG Vector Engine Active" />
          </motion.div>
          <div>
            <h1 className="font-display text-xl font-black tracking-tight text-slate-900 md:text-2xl">
              CampusMind <span className="ml-1.5 rounded-full border border-sky-300/50 bg-sky-500/15 px-2.5 py-0.5 text-xs font-extrabold uppercase tracking-wider text-sky-600">AI</span>
            </h1>
            <p className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-slate-600">
              <Cpu className="w-3.5 h-3.5 text-sky-600" />
              <span>Campus RAG Assistant</span>
            </p>
          </div>
        </div>

        <nav className="hidden items-center gap-2 rounded-2xl border border-white/80 bg-white/40 p-1.5 shadow-inner backdrop-blur-xl lg:flex">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onSelectTab('chat')}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-extrabold tracking-wide transition-all ${activeTab === 'chat' ? 'border border-white/60 bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 text-white shadow-md shadow-sky-500/30' : 'text-slate-700 hover:bg-white/60 hover:text-slate-900'}`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Assistant Chat</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onSelectTab('hub')}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-extrabold tracking-wide transition-all ${activeTab === 'hub' ? 'border border-white/60 bg-gradient-to-r from-sky-500 via-indigo-600 to-purple-600 text-white shadow-md shadow-sky-500/30' : 'text-slate-700 hover:bg-white/60 hover:text-slate-900'}`}
          >
            <GraduationCap className="w-4 h-4" />
            <span>Campus Intelligence</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onSelectTab('analytics')}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-extrabold tracking-wide transition-all ${activeTab === 'analytics' ? 'border border-white/60 bg-gradient-to-r from-emerald-500 via-teal-600 to-sky-600 text-white shadow-md shadow-emerald-500/30' : 'text-slate-700 hover:bg-white/60 hover:text-slate-900'}`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Academic Analytics</span>
          </motion.button>
          {user?.role === 'admin' && (
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => onSelectTab('admin')}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-extrabold tracking-wide transition-all ${activeTab === 'admin' ? 'border border-white/60 bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-purple-500/30' : 'text-slate-700 hover:bg-white/60 hover:text-slate-900'}`}
            >
              <Cpu className="w-4 h-4" />
              <span>System & Audit</span>
            </motion.button>
          )}
        </nav>


        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 rounded-2xl border px-3.5 py-2 text-xs font-bold backdrop-blur-md ${currentRole.badge}`} title="Role assigned by the server">
            <CurrentRoleIcon className="w-4 h-4" />
            <span>{currentRole.label}</span>
          </div>
          <div className="hidden items-center gap-2.5 border-l border-slate-300/60 pl-3 sm:flex">
            <div className="w-8 h-8 rounded-2xl bg-gradient-to-tr from-sky-400 to-indigo-500 p-[1px] shadow-sm">
              <div className="flex h-full w-full items-center justify-center rounded-[15px] bg-white/90 text-xs font-extrabold text-sky-700">
                {(user?.username || 'U')[0].toUpperCase()}
              </div>
            </div>
            <span className="hidden text-xs font-bold text-slate-800 md:inline">{user?.username}</span>
          </div>
          <NotificationBell />
          <motion.button
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.92 }}
            onClick={onLogout}
            className="rounded-2xl border border-transparent p-2.5 text-slate-500 transition-all hover:border-rose-300 hover:bg-rose-500/15 hover:text-rose-600"
            title="Sign Out"
          >
            <LogOut className="w-4.5 h-4.5" />
          </motion.button>
        </div>
      </div>
    </header>
  );
}

function NotificationBell() {
  const [open, setOpen] = React.useState(false);
  const [notifications, setNotifications] = React.useState([]);
  const [unreadCount, setUnreadCount] = React.useState(0);

  const loadNotifications = async () => {
    try {
      const { fetchNotifications } = await import('../lib/api');
      const data = await fetchNotifications();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch {
      // Ignore background errors
    }
  };

  React.useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      const { markNotificationsRead } = await import('../lib/api');
      const ids = notifications.filter(n => !n.is_read).map(n => n.id);
      if (ids.length > 0) {
        await markNotificationsRead(ids);
        loadNotifications();
      }
    } catch {}
  };

  return (
    <div className="relative">
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={() => { setOpen(!open); if (!open) loadNotifications(); }}
        className="relative rounded-2xl border border-slate-200 bg-white/80 p-2.5 text-slate-600 transition-all hover:border-sky-300 hover:text-sky-600"
        title="System Alerts & Notifications"
      >
        <span className="sr-only">Notifications</span>
        <svg className="w-4.5 h-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-sm">
            {unreadCount}
          </span>
        )}
      </motion.button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-2xl border border-slate-200 bg-white p-4 shadow-xl z-50">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2.5 mb-2">
            <h4 className="text-xs font-black text-slate-800 uppercase tracking-wider">Alerts & Notifications</h4>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-[11px] font-bold text-sky-600 hover:underline"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {notifications.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">No alerts or notifications</p>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  className={`p-2.5 rounded-xl border text-xs transition-all ${
                    item.is_read ? 'bg-slate-50 border-slate-100 opacity-75' : 'bg-sky-50/50 border-sky-200 font-medium'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className={`text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                      item.severity === 'critical' ? 'bg-rose-100 text-rose-700' :
                      item.severity === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-sky-100 text-sky-700'
                    }`}>
                      {item.severity}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <h5 className="font-bold text-slate-800">{item.title}</h5>
                  <p className="text-slate-600 mt-0.5 text-[11px] leading-relaxed">{item.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
