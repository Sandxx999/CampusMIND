import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sparkles, 
  ShieldCheck, 
  UserCheck, 
  GraduationCap, 
  BookOpen, 
  BarChart3, 
  LogOut, 
  Cpu, 
  Layers,
  ChevronDown
} from 'lucide-react';

export default function Header({ user, onLogout, activeTab, onSelectTab, onRoleChange }) {
  const [showRoleDropdown, setShowRoleDropdown] = useState(false);

  const roles = [
    { id: 'student', name: 'Student View', icon: GraduationCap, badge: 'bg-sky-500/15 text-sky-700 border-sky-300/60 shadow-sm', desc: 'General Notices, Student Records, Timetables, Grades' },
    { id: 'faculty', name: 'Faculty View', icon: UserCheck, badge: 'bg-purple-500/15 text-purple-700 border-purple-300/60 shadow-sm', desc: 'Faculty Circulars, Seed Grants, Grading Policy' },
    { id: 'admin', name: 'Admin Scope', icon: ShieldCheck, badge: 'bg-amber-500/15 text-amber-700 border-amber-300/60 shadow-sm', desc: 'Full System Control, RAG Metrics & Query Logs' },
  ];

  const currentRoleObj = roles.find(r => r.id === user?.role) || roles[0];
  const CurrentRoleIcon = currentRoleObj.icon;

  const handleSelectRole = (newRole) => {
    setShowRoleDropdown(false);
    if (onRoleChange) {
      onRoleChange(newRole);
    }
  };

  return (
    <header className="glass-mirror-navbar sticky top-0 z-50 px-4 md:px-8 py-3.5 transition-all duration-300">
      <div className="max-w-[1700px] mx-auto flex items-center justify-between gap-4">
        
        {/* BRAND & LOGO EMBLEM */}
        <div className="flex items-center gap-3.5">
          <motion.div 
            whileHover={{ scale: 1.08, rotate: 4 }}
            whileTap={{ scale: 0.95 }}
            className="relative group cursor-pointer"
          >
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-sky-400 via-indigo-500 to-purple-500 p-[1.5px] shadow-lg shadow-sky-500/20">
              <div className="w-full h-full bg-white/90 rounded-[14px] flex items-center justify-center backdrop-blur-md">
                <Sparkles className="w-5.5 h-5.5 text-sky-600 animate-pulse" />
              </div>
            </div>
            {/* Live RAG Status Dot */}
            <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 border-2 border-white rounded-full shadow-sm" title="RAG Vector Engine Active" />
          </motion.div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-display text-xl md:text-2xl font-black tracking-tight text-slate-900">
                CampusMind <span className="text-sky-600 font-extrabold text-xs tracking-wider uppercase px-2.5 py-0.5 rounded-full bg-sky-500/15 border border-sky-300/50 ml-1.5 shadow-sm">AI</span>
              </h1>
            </div>
            <p className="text-xs text-slate-600 flex items-center gap-1.5 font-semibold tracking-wide">
              <Cpu className="w-3.5 h-3.5 text-sky-600" />
              <span>IFHE Enterprise RAG Assistant</span>
            </p>
          </div>
        </div>

        {/* ROLE SCOPE SWITCHER & TAB NAV */}
        <div className="hidden lg:flex items-center gap-2 bg-white/40 p-1.5 rounded-2xl border border-white/80 shadow-inner backdrop-blur-xl">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onSelectTab && onSelectTab('chat')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-extrabold tracking-wide transition-all ${
              activeTab === 'chat'
                ? 'bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 text-white shadow-md shadow-sky-500/30 border border-white/60'
                : 'text-slate-700 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Assistant Chat</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onSelectTab && onSelectTab('admin')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-extrabold tracking-wide transition-all ${
              activeTab === 'admin'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-purple-500/30 border border-white/60'
                : 'text-slate-700 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Analytics & Knowledge Base</span>
          </motion.button>
        </div>

        {/* USER PROFILE & ROLE SCOPE DROPDOWN */}
        <div className="flex items-center gap-3">
          {/* Dynamic Role Scope Selector Dropdown */}
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => setShowRoleDropdown(!showRoleDropdown)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-2xl border text-xs font-bold transition-all ${currentRoleObj.badge} backdrop-blur-md`}
              title="Click to switch active role scope for RAG document permissions"
            >
              <CurrentRoleIcon className="w-4 h-4" />
              <span className="capitalize">{user?.role || 'Student'} Scope</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-70" />
            </motion.button>

            {/* Dropdown Menu */}
            <AnimatePresence>
              {showRoleDropdown && (
                <motion.div 
                  initial={{ opacity: 0, y: -8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                  className="absolute right-0 mt-2.5 w-72 glass-mirror-panel rounded-3xl border border-white/90 p-2.5 shadow-2xl z-50"
                >
                  <div className="px-3 py-2 mb-1.5 text-[11px] font-extrabold text-slate-500 uppercase tracking-wider border-b border-slate-200/60 flex items-center justify-between">
                    <span>Switch Active Scope</span>
                    <Layers className="w-3.5 h-3.5 text-sky-600" />
                  </div>
                  <div className="space-y-1.5">
                    {roles.map((r) => {
                      const IconComp = r.icon;
                      const isSelected = (user?.role === r.id);
                      return (
                        <button
                          key={r.id}
                          onClick={() => handleSelectRole(r.id)}
                          className={`w-full text-left p-2.5 rounded-2xl transition-all flex items-start gap-3 ${
                            isSelected
                              ? 'bg-sky-500/15 border border-sky-400/50 text-sky-900 font-bold shadow-sm'
                              : 'hover:bg-white/80 text-slate-700'
                          }`}
                        >
                          <IconComp className={`w-4 h-4 mt-0.5 ${isSelected ? 'text-sky-600' : 'text-slate-500'}`} />
                          <div>
                            <div className="text-xs font-bold">{r.name}</div>
                            <div className="text-[11px] text-slate-500 leading-snug mt-0.5">{r.desc}</div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* User Avatar Chip */}
          <div className="hidden sm:flex items-center gap-2.5 pl-3 border-l border-slate-300/60">
            <div className="w-8 h-8 rounded-2xl bg-gradient-to-tr from-sky-400 to-indigo-500 p-[1px] shadow-sm">
              <div className="w-full h-full bg-white/90 rounded-[15px] flex items-center justify-center font-extrabold text-xs text-sky-700">
                {(user?.username || 'U')[0].toUpperCase()}
              </div>
            </div>
            <span className="text-xs font-bold text-slate-800 hidden md:inline">
              {user?.username}
            </span>
          </div>

          {/* Sign Out Button */}
          <motion.button
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.92 }}
            onClick={onLogout}
            className="p-2.5 rounded-2xl text-slate-500 hover:text-rose-600 hover:bg-rose-500/15 transition-all border border-transparent hover:border-rose-300"
            title="Sign Out"
          >
            <LogOut className="w-4.5 h-4.5" />
          </motion.button>
        </div>

      </div>
    </header>
  );
}
