import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ShieldCheck, UserCheck, GraduationCap, Lock, User, ArrowRight } from 'lucide-react';
import { loginUser } from '../lib/api';

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('student1');
  const [password, setPassword] = useState('password123');
  const [selectedDemo, setSelectedDemo] = useState('student');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await loginUser(username, password);
      onLoginSuccess(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials or backend server status.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoUser = (demoUsername, demoRole) => {
    setUsername(demoUsername);
    setPassword('password123');
    setSelectedDemo(demoRole);
  };

  return (
    <div className="min-h-screen bg-[#ECEFF6] flex items-center justify-center p-4 relative overflow-hidden">
      
      {/* SOFT PASTEL FLOATING ORBS */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-300/35 rounded-full blur-[130px] pointer-events-none animate-pulse-glow" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-300/30 rounded-full blur-[130px] pointer-events-none animate-float-slow" />

      {/* LOGIN CARD CONTAINER WITH ALL-WHITE MIRROR GLASS */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md glass-mirror-panel rounded-3xl p-8 border border-white/90 shadow-2xl relative z-10 overflow-hidden"
      >
        
        {/* LOGO & TITLE HEADER */}
        <div className="text-center mb-6">
          <motion.div 
            whileHover={{ scale: 1.1, rotate: 5 }}
            className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-sky-400 via-indigo-500 to-purple-500 p-[1.5px] mx-auto mb-3 shadow-lg shadow-sky-500/20"
          >
            <div className="w-full h-full bg-white/90 rounded-[22px] flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-sky-600 animate-pulse" />
            </div>
          </motion.div>
          
          <h2 className="font-display text-2xl lg:text-3xl font-black text-slate-900 tracking-tight">
            CampusMind AI
          </h2>
          <p className="text-xs text-sky-700 font-bold mt-1">
            Development demo — server-assigned roles and synthetic data
          </p>
        </div>

        {/* ERROR ALERT */}
        {error && (
          <div className="mb-4 p-3.5 bg-rose-500/15 border border-rose-300/60 rounded-2xl text-xs text-rose-800 font-bold font-sans">
            {error}
          </div>
        )}

        {/* DEMO USER QUICK PRESET PILLS */}
        <div className="mb-6">
          <label className="block text-[11px] font-extrabold text-slate-600 uppercase tracking-wider mb-2.5">
            Select Demo Identity
          </label>
          <div className="grid grid-cols-3 gap-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => handleQuickDemoUser('student1', 'student')}
              className={`p-2.5 rounded-2xl border text-center transition-all ${
                selectedDemo === 'student'
                  ? 'bg-sky-500/20 border-sky-400/70 text-sky-900 font-extrabold shadow-sm'
                  : 'bg-white/60 border-white/90 text-slate-700 hover:bg-white'
              }`}
            >
              <GraduationCap className="w-5 h-5 mx-auto mb-1 text-sky-600" />
              <div className="text-[11px] font-bold">Student</div>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => handleQuickDemoUser('faculty1', 'faculty')}
              className={`p-2.5 rounded-2xl border text-center transition-all ${
                selectedDemo === 'faculty'
                  ? 'bg-purple-500/20 border-purple-400/70 text-purple-900 font-extrabold shadow-sm'
                  : 'bg-white/60 border-white/90 text-slate-700 hover:bg-white'
              }`}
            >
              <UserCheck className="w-5 h-5 mx-auto mb-1 text-purple-600" />
              <div className="text-[11px] font-bold">Faculty</div>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => handleQuickDemoUser('admin1', 'admin')}
              className={`p-2.5 rounded-2xl border text-center transition-all ${
                selectedDemo === 'admin'
                  ? 'bg-amber-500/20 border-amber-400/70 text-amber-900 font-extrabold shadow-sm'
                  : 'bg-white/60 border-white/90 text-slate-700 hover:bg-white'
              }`}
            >
              <ShieldCheck className="w-5 h-5 mx-auto mb-1 text-amber-600" />
              <div className="text-[11px] font-bold">Admin</div>
            </motion.button>
          </div>
        </div>

        {/* LOGIN FORM */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-800 mb-1.5 flex items-center gap-1.5">
              <User className="w-4 h-4 text-sky-600" />
              <span>Username</span>
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 glass-mirror-input rounded-2xl text-sm font-semibold text-slate-900 placeholder-slate-400 focus:outline-none transition font-sans"
              placeholder="e.g. student1"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-800 mb-1.5 flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-sky-600" />
              <span>Password</span>
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 glass-mirror-input rounded-2xl text-sm font-semibold text-slate-900 placeholder-slate-400 focus:outline-none transition font-sans"
              placeholder="••••••••"
            />
          </div>

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-display font-extrabold rounded-2xl text-sm transition-all disabled:opacity-50 shadow-md shadow-sky-500/30 flex items-center justify-center gap-2 mt-3 border border-white/40"
          >
            {loading ? (
              <span>Authenticating JWT Token...</span>
            ) : (
              <>
                <span>Access Campus System</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </motion.button>
        </form>

        {/* FOOTER DEMO INFO */}
        <div className="mt-6 pt-4 border-t border-slate-200/80 text-center font-mono text-[11px] text-slate-500 font-semibold">
          Development demo only — roles are assigned by the server
        </div>

      </motion.div>
    </div>
  );
}
