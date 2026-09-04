import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  Copy, 
  Check, 
  Volume2, 
  BookOpen, 
  ShieldCheck
} from 'lucide-react';
import FeedbackButtons from './FeedbackButtons';

export default function MessageBubble({ message, onSelectSources }) {
  const isUser = message.sender === 'user';
  const [copied, setCopied] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSpeak = () => {
    if ('speechSynthesis' in window) {
      if (speaking) {
        window.speechSynthesis.cancel();
        setSpeaking(false);
        return;
      }
      const utterance = new SpeechSynthesisUtterance(message.text.replace(/[#*`]/g, ''));
      utterance.onend = () => setSpeaking(false);
      setSpeaking(true);
      window.speechSynthesis.speak(utterance);
    }
  };

  const renderFormattedMarkdown = (text) => {
    if (!text) return null;
    const lines = text.split('\n');

    return lines.map((line, idx) => {
      const trimmed = line.trim();

      if (trimmed.startsWith('### ')) {
        return (
          <h3 key={idx} className="font-display text-base font-extrabold text-sky-800 mt-3 mb-1.5 flex items-center gap-2">
            {trimmed.replace('### ', '')}
          </h3>
        );
      }
      if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
        return (
          <p key={idx} className="font-bold text-slate-900 mt-2 mb-1 text-xs md:text-sm">
            {trimmed.replace(/\*\*/g, '')}
          </p>
        );
      }
      if (trimmed.startsWith('• ') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const cleanContent = trimmed.substring(2);
        const parts = cleanContent.split(/(\*\*.*?\*\*)/g);
        return (
          <li key={idx} className="ml-4 list-disc text-slate-800 my-1 leading-relaxed text-xs md:text-sm font-medium">
            {parts.map((p, i) => 
              p.startsWith('**') && p.endsWith('**') ? (
                <strong key={i} className="text-sky-900 font-extrabold">{p.replace(/\*\*/g, '')}</strong>
              ) : (
                p
              )
            )}
          </li>
        );
      }
      if (trimmed.startsWith('---')) {
        return <hr key={idx} className="my-3 border-slate-200/80" />;
      }
      if (trimmed.startsWith('*Information verified')) {
        return (
          <p key={idx} className="text-[11px] text-slate-600 italic mt-3 pt-2.5 border-t border-slate-200/80 flex items-center gap-1.5 font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{trimmed.replace(/\*/g, '')}</span>
          </p>
        );
      }

      if (!trimmed) return <div key={idx} className="h-1.5" />;

      const parts = line.split(/(\*\*.*?\*\*)/g);
      return (
        <p key={idx} className="text-xs md:text-sm text-slate-800 leading-relaxed my-1 font-medium">
          {parts.map((p, i) => 
            p.startsWith('**') && p.endsWith('**') ? (
              <strong key={i} className="text-slate-900 font-extrabold">{p.replace(/\*\*/g, '')}</strong>
            ) : (
              p
            )
          )}
        </p>
      );
    });
  };

  if (isUser) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 12, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="flex flex-col items-end w-full my-3"
      >
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-[11px] font-bold text-slate-600">You</span>
          <div className="w-5 h-5 rounded-full bg-sky-500/20 border border-sky-400/50 flex items-center justify-center text-sky-700 text-[10px] font-extrabold shadow-sm">
            U
          </div>
        </div>

        <div className="max-w-[85%] mirror-bubble-user font-sans text-xs md:text-sm px-4.5 py-3.5 rounded-3xl rounded-tr-sm leading-relaxed">
          {message.text}
        </div>

        <span className="text-[10px] text-slate-500 mt-1 font-mono">{message.timestamp || 'Just now'}</span>
      </motion.div>
    );
  }

  const confidenceScore = Math.round((message.confidence || 0.85) * 100);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 12, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.35 }}
      className="flex flex-col items-start w-full my-4"
    >
      {/* HEADER BAR FOR ASSISTANT MESSAGE */}
      <div className="flex items-center justify-between w-full mb-1.5">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-xl bg-gradient-to-tr from-sky-400 to-indigo-500 p-[1px] shadow-sm">
            <div className="w-full h-full bg-white/90 rounded-[11px] flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
            </div>
          </div>
          <span className="font-display text-xs font-black text-slate-900">CampusMind AI</span>
          <span className="text-[10px] text-slate-500 font-mono">• {message.timestamp || 'Just now'}</span>
        </div>

        {/* Confidence Meter Badge */}
        {message.confidence !== undefined && (
          <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
            confidenceScore >= 75 ? 'bg-emerald-500/15 border-emerald-400/50 text-emerald-800' :
            confidenceScore >= 50 ? 'bg-sky-500/15 border-sky-400/50 text-sky-800' :
            'bg-amber-500/15 border-amber-400/50 text-amber-800'
          }`}>
            {confidenceScore}% RAG Match
          </span>
        )}
      </div>

      {/* MESSAGE BODY CONTAINER WITH ALL-WHITE MIRROR GLASS */}
      <div className={`w-full mirror-bubble-ai rounded-3xl p-5 border-l-4 ${
        message.isError 
          ? 'border-l-rose-500 bg-rose-50 border-rose-300 text-rose-900' 
          : 'border-l-sky-500 border-white/90'
      } shadow-xl relative group`}>
        
        {renderFormattedMarkdown(message.text)}

        {/* CITED SOURCES STRIP */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-4 pt-3.5 border-t border-slate-200/80 flex items-center justify-between flex-wrap gap-2">
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => onSelectSources && onSelectSources(message.sources)}
              className="inline-flex items-center gap-2 text-xs font-extrabold text-sky-800 bg-sky-500/15 hover:bg-sky-500/25 px-3.5 py-1.5 rounded-2xl border border-sky-300/60 transition-all shadow-sm"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>{message.sources.length} Verified Citation Source{message.sources.length > 1 ? 's' : ''}</span>
            </motion.button>

            {/* ACTION TOOLBAR: Copy & Speak */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleCopy}
                className="p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                title="Copy Answer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              </button>

              <button
                onClick={handleSpeak}
                className={`p-2 rounded-xl transition-colors ${speaking ? 'text-sky-700 bg-sky-500/20' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'}`}
                title="Listen to Answer"
              >
                <Volume2 className="w-3.5 h-3.5" />
              </button>

              {message.queryId && (
                <FeedbackButtons queryId={message.queryId} />
              )}
            </div>
          </div>
        )}

        {!message.sources?.length && message.queryId && (
          <div className="mt-3 pt-2.5 border-t border-slate-200/80 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleCopy}
                className="p-1.5 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                title="Copy Answer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            <FeedbackButtons queryId={message.queryId} />
          </div>
        )}
      </div>
    </motion.div>
  );
}
