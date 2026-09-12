import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Sparkles, 
  Award, 
  Calendar, 
  FileText, 
  CreditCard, 
  Briefcase, 
  Trash2, 
  Mic, 
  ChevronRight,
  Layers,
  BookOpen,
  User,
  Bot,
  MessageSquare
} from 'lucide-react';
import MessageBubble from './MessageBubble';
import SourceCitation from './SourceCitation';

const CATEGORY_PROMPTS = [
  {
    id: 'grades',
    title: 'Grade Sheets & CGPA',
    icon: Award,
    color: 'from-amber-400 to-orange-400 text-amber-900 border-amber-300/60',
    desc: 'SGPA/CGPA formulas, official transcripts & grade cards',
    question: 'What is the grading scale and how are SGPA/CGPA calculated? How do I apply for official transcripts?'
  },
  {
    id: 'students',
    title: 'Student Directory & Records',
    icon: User,
    color: 'from-emerald-400 to-teal-400 text-emerald-900 border-emerald-300/60',
    desc: 'Query 100 student profiles, enrolled courses & CGPA details',
    question: 'What are the enrolled courses, branch, and CGPA for student 2024IFHE001?'
  },
  {
    id: 'exams',
    title: 'Exam Schedules & Timetables',
    icon: Calendar,
    color: 'from-sky-400 to-blue-400 text-sky-900 border-sky-300/60',
    desc: 'Spring 2026 dates, slot timings & seating rules',
    question: 'What are the examination dates for Spring 2026 and what are the morning vs afternoon session slot timings?'
  },
  {
    id: 'halltickets',
    title: 'Hall Tickets & Admit Cards',
    icon: FileText,
    color: 'from-blue-400 to-indigo-400 text-indigo-900 border-indigo-300/60',
    desc: 'ERP download dates, eligibility rules & emergency duplicate fee',
    question: 'How do I download my hall ticket from the ERP portal, what is the attendance eligibility requirement, and what happens if I lose it?'
  },
  {
    id: 'documents',
    title: 'Student Documents & Certificates',
    icon: Layers,
    color: 'from-purple-400 to-pink-400 text-purple-900 border-purple-300/60',
    desc: 'Bonafide letters for Bank Loans, Passports, Visas & RFID ID card',
    question: 'How do I request a Bonafide Certificate for an educational bank loan or passport? What is the ID card replacement fee?'
  },
  {
    id: 'fees',
    title: 'Fee Structure & Deadlines',
    icon: CreditCard,
    color: 'from-rose-400 to-red-400 text-rose-900 border-rose-300/60',
    desc: 'B.Tech/MBA tuition fees, late fee fines & merit scholarships',
    question: 'What are the semester tuition fee payment deadlines, late payment daily penalties, and merit scholarship waivers?'
  }
];

const SAMPLE_STUDENTS_PILLS = [
  { id: '2024IFHE001', name: 'Aarav Sharma', branch: 'CSE', cgpa: '9.42' },
  { id: '2024IFHE042', name: 'Riya Deshmukh', branch: 'AI&DS', cgpa: '9.75' },
  { id: '2024IFHE015', name: 'Preeti Mittal', branch: 'ECE', cgpa: '8.90' },
  { id: '2024IFHE088', name: 'Karan Kapoor', branch: 'MBA', cgpa: '9.15' },
];

export default function ChatWindow({ messages, onSendMessage, isLoading, currentSources, onClearChat }) {
  const [inputText, setInputText] = useState('');
  const [activeTabMobile, setActiveTabMobile] = useState('chat');
  const [isMicActive, setIsMicActive] = useState(false);
  const [showSourcesDrawer, setShowSourcesDrawer] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handlePromptClick = (question) => {
    if (isLoading) return;
    onSendMessage(question);
  };

  const toggleMic = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setIsMicActive(!isMicActive);
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        setInputText(transcript);
        setIsMicActive(false);
      };
      recognition.onerror = () => setIsMicActive(false);
      recognition.start();
    } else {
      alert('Voice speech recognition is not supported in your browser.');
    }
  };

  return (
    <div className="w-full max-w-[1700px] mx-auto h-[calc(100vh-75px)] flex flex-col lg:flex-row gap-5 p-4 lg:p-6 overflow-hidden relative">
      
      {/* AMBIENT SOFT PASTEL BLOB SPHERES */}
      <div className="absolute -top-24 -left-24 w-96 h-96 bg-sky-300/30 rounded-full blur-[130px] pointer-events-none animate-pulse-glow" />
      <div className="absolute top-1/3 right-10 w-96 h-96 bg-purple-300/25 rounded-full blur-[140px] pointer-events-none animate-float-slow" />

      {/* MOBILE TAB SWITCHER */}
      <div className="lg:hidden flex glass-mirror-panel p-1 rounded-2xl border border-white/80 shrink-0">
        <button
          onClick={() => setActiveTabMobile('launchpad')}
          className={`flex-1 py-2.5 text-xs font-extrabold rounded-xl transition-all ${
            activeTabMobile === 'launchpad' ? 'bg-sky-500 text-white shadow-md' : 'text-slate-700'
          }`}
        >
          Knowledge Base
        </button>
        <button
          onClick={() => setActiveTabMobile('chat')}
          className={`flex-1 py-2.5 text-xs font-extrabold rounded-xl transition-all ${
            activeTabMobile === 'chat' ? 'bg-sky-500 text-white shadow-md' : 'text-slate-700'
          }`}
        >
          Chatbot Query Panel
        </button>
      </div>

      {/* ==========================================================================
         LEFT COLUMN: KNOWLEDGE LAUNCHPAD & STUDENT DIRECTORY (58% Width)
         ========================================================================== */}
      <div 
        className={`w-full lg:w-[58%] h-full flex flex-col gap-4 overflow-y-auto pr-1 ${
          activeTabMobile === 'launchpad' || window.innerWidth >= 1024 ? 'flex' : 'hidden lg:flex'
        }`}
      >
        {/* HERO TITLE CONTAINER WITH ALL-WHITE MIRROR GLASS */}
        <div className="glass-mirror-panel rounded-3xl p-6 border border-white/90 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-sky-400/20 via-purple-400/10 to-transparent rounded-bl-full pointer-events-none" />
          
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-extrabold uppercase tracking-widest px-3 py-1 rounded-full bg-sky-500/15 text-sky-800 border border-sky-300/60 shadow-sm">
              Campus Intelligence System
            </span>
            <span className="text-[11px] text-slate-600 font-mono font-bold">
              DEMO DATA • 100 Synthetic Student Records
            </span>
          </div>

          <h2 className="font-display text-2xl lg:text-3xl font-black text-slate-900 tracking-tight leading-tight">
            Official IFHE Knowledge Base & RAG Portal
          </h2>
          <p className="text-xs lg:text-sm text-slate-700 font-medium mt-1.5 max-w-xl leading-relaxed">
            Query campus guidelines, timetables, grade sheets, and fee schedules. Student records shown here are synthetic demo data.
          </p>

          {/* QUICK STUDENT RECORD EXPLORER STRIP */}
          <div className="mt-4 pt-4 border-t border-slate-200/80">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-sky-600" />
                <span>Demo Student Record Prompts:</span>
              </span>
              <span className="text-[10px] text-sky-700 font-mono font-bold">DEMO DATA • 100 Records</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {SAMPLE_STUDENTS_PILLS.map((s) => (
                <motion.button
                  key={s.id}
                  whileHover={{ scale: 1.04, y: -2 }}
                  whileTap={{ scale: 0.96 }}
                  onClick={() => handlePromptClick(`What are the enrolled courses, branch, and CGPA for student ${s.id}?`)}
                  className="glass-mirror-card glass-mirror-interactive p-2.5 rounded-2xl text-left border border-white/90 hover:border-sky-400"
                >
                  <div className="text-[11px] font-extrabold text-sky-700 font-mono">{s.id}</div>
                  <div className="text-xs font-bold text-slate-900 truncate">{s.name}</div>
                  <div className="text-[10px] text-slate-600 font-medium flex items-center justify-between mt-0.5">
                    <span>{s.branch}</span>
                    <span className="text-emerald-700 font-bold">CGPA {s.cgpa}</span>
                  </div>
                </motion.button>
              ))}
            </div>
          </div>
        </div>

        {/* 2x3 KNOWLEDGE CATEGORY LAUNCHPAD CARDS */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 flex-1">
          {CATEGORY_PROMPTS.map((cat) => {
            const IconComponent = cat.icon;
            return (
              <motion.button
                key={cat.id}
                whileHover={{ scale: 1.03, y: -4 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => handlePromptClick(cat.question)}
                disabled={isLoading}
                className="w-full text-left glass-mirror-panel glass-mirror-interactive rounded-3xl p-5 border border-white/90 hover:border-sky-400 group relative overflow-hidden shadow-xl flex flex-col justify-between"
              >
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className={`p-3 rounded-2xl bg-gradient-to-br ${cat.color} shrink-0 shadow-sm border border-white/60`}>
                    <IconComponent className="w-5 h-5 text-slate-900" />
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-sky-600 group-hover:translate-x-1 transition-all" />
                </div>

                <div>
                  <h4 className="font-display text-sm lg:text-base font-extrabold text-slate-900 group-hover:text-sky-700 transition-colors mb-1">
                    {cat.title}
                  </h4>
                  <p className="text-xs text-slate-600 font-medium line-clamp-2 leading-relaxed font-sans">
                    {cat.desc}
                  </p>
                </div>
              </motion.button>
            );
          })}
        </div>

      </div>


      {/* ==========================================================================
         RIGHT COLUMN: CHATBOT QUERY BOX AT RIGHT SIDE WITH COOL FLOATING ANIMATIONS (42% Width)
         ========================================================================== */}
      <div 
        className={`w-full lg:w-[42%] h-full flex flex-col glass-mirror-panel rounded-3xl border border-white/90 shadow-2xl overflow-hidden relative ${
          activeTabMobile === 'chat' || window.innerWidth >= 1024 ? 'flex' : 'hidden lg:flex'
        }`}
      >
        {/* ANIMATED GLOW HEADER BAR */}
        <div className="px-5 py-4 bg-white/70 border-b border-white/80 backdrop-blur-2xl flex items-center justify-between shrink-0 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-sky-400 via-indigo-500 to-purple-500 p-[1.5px] shadow-lg shadow-sky-500/20 animate-float-slow">
                <div className="w-full h-full bg-white/90 rounded-[14px] flex items-center justify-center">
                  <Bot className="w-5 h-5 text-sky-600 animate-pulse" />
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-display text-base font-black text-slate-900 tracking-tight flex items-center gap-2">
                <span>CampusMind Query Panel</span>
              </h3>
              <p className="text-[11px] text-sky-700 font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                <span>RAG Intelligence Stream</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {currentSources && currentSources.length > 0 && (
              <button
                onClick={() => setShowSourcesDrawer(!showSourcesDrawer)}
                className="px-3 py-1.5 rounded-xl bg-sky-500/15 text-sky-800 border border-sky-300/60 text-xs font-bold hover:bg-sky-500/25 transition-all flex items-center gap-1.5 shadow-sm"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>{currentSources.length} Sources</span>
              </button>
            )}

            {onClearChat && (
              <button
                onClick={onClearChat}
                className="p-2 rounded-xl text-slate-500 hover:text-rose-600 hover:bg-rose-500/15 transition-all"
                title="Clear Chat Stream"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* CHAT MESSAGES DISPLAY STREAM */}
        <div className="flex-1 overflow-y-auto p-4 md:p-5 space-y-4 relative bg-white/20">
          {messages.length === 0 ? (
            /* EMPTY STREAM WELCOME PROMPT */
            <div className="h-full flex flex-col items-center justify-center text-center p-6 my-auto">
              <motion.div 
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 4, repeat: Infinity, repeatType: 'reverse' }}
                className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-sky-400 via-indigo-500 to-purple-500 p-[1.5px] mb-4 shadow-xl shadow-sky-500/20"
              >
                <div className="w-full h-full bg-white/90 rounded-[22px] flex items-center justify-center">
                  <MessageSquare className="w-8 h-8 text-sky-600" />
                </div>
              </motion.div>

              <h3 className="font-display text-lg font-extrabold text-slate-900 mb-1.5">
                AI Assistant Ready
              </h3>
              <p className="text-xs text-slate-600 font-medium max-w-xs leading-relaxed font-sans mb-4">
                Ask any question about campus policies, exam timetables, or query student data (e.g. <span className="text-sky-700 font-mono font-bold">2024IFHE001</span>).
              </p>

              <div className="flex flex-wrap gap-2 justify-center">
                <button
                  onClick={() => handlePromptClick('When are the Spring 2026 examination dates?')}
                  className="text-[11px] font-bold text-sky-800 bg-sky-500/15 border border-sky-300/60 px-3 py-1.5 rounded-full hover:bg-sky-500/25 transition-all shadow-sm"
                >
                  Spring 2026 Exams?
                </button>
                <button
                  onClick={() => handlePromptClick('Show details for student 2024IFHE042')}
                  className="text-[11px] font-bold text-purple-800 bg-purple-500/15 border border-purple-300/60 px-3 py-1.5 rounded-full hover:bg-purple-500/25 transition-all shadow-sm"
                >
                  Student 2024IFHE042?
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <MessageBubble
                key={idx}
                message={msg}
                onSelectSources={() => setShowSourcesDrawer(true)}
              />
            ))
          )}

          {/* LOADING STATE ANIMATION */}
          {isLoading && (
            <div className="flex items-start my-3">
              <motion.div
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="glass-mirror-card rounded-2xl p-4 border-l-4 border-l-sky-500 text-slate-800 shadow-xl flex items-center gap-3 w-full"
              >
                <div className="w-5 h-5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin shrink-0" />
                <span className="font-display text-xs font-bold tracking-wide text-sky-900">
                  Synthesizing verified RAG response...
                </span>
              </motion.div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* SOURCES MODAL SLIDE-OVER */}
        <AnimatePresence>
          {showSourcesDrawer && (
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="absolute inset-0 z-30 glass-mirror-panel bg-white/95 p-4 flex flex-col"
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
                <h4 className="font-display text-sm font-bold text-slate-900 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-sky-600" />
                  <span>Verified RAG Citation Sources</span>
                </h4>
                <button
                  onClick={() => setShowSourcesDrawer(false)}
                  className="px-3 py-1 rounded-xl bg-slate-200 hover:bg-slate-300 text-xs font-bold text-slate-800"
                >
                  Close
                </button>
              </div>
              <div className="flex-1 overflow-y-auto">
                <SourceCitation sources={currentSources} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* FLOATING QUERY INPUT FORM CONTAINER */}
        <div className="p-4 bg-white/80 border-t border-white/90 backdrop-blur-2xl shrink-0 shadow-lg">
          <form onSubmit={handleSubmit} className="flex items-center gap-2.5">
            {/* VOICE MIC TOGGLE */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={toggleMic}
              className={`p-3 rounded-2xl border transition-all ${
                isMicActive 
                  ? 'bg-rose-500/20 border-rose-400 text-rose-600 animate-pulse' 
                  : 'bg-white/80 border-slate-200 text-slate-600 hover:text-slate-900 hover:border-slate-300 shadow-sm'
              }`}
              title="Voice Input"
            >
              <Mic className="w-4.5 h-4.5" />
            </motion.button>

            {/* INPUT FIELD */}
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask about grade cards, exams, fees or student ID..."
              disabled={isLoading}
              className="flex-1 glass-mirror-input text-slate-900 font-sans text-xs md:text-sm px-4 py-3.5 rounded-2xl placeholder-slate-400 focus:outline-none transition-all font-medium"
            />

            {/* SUBMIT BUTTON */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="font-display text-xs md:text-sm font-extrabold bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white px-5 py-3.5 rounded-2xl transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-sky-500/30 flex items-center gap-2 border border-white/40"
            >
              <span>Ask</span>
              <Send className="w-4 h-4" />
            </motion.button>
          </form>
        </div>

      </div>

    </div>
  );
}
