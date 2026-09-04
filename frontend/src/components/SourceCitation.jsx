import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, 
  ExternalLink, 
  Sparkles, 
  BookOpen, 
  Award, 
  Calendar, 
  CreditCard, 
  Briefcase, 
  Building,
  ShieldCheck,
  X
} from 'lucide-react';

export default function SourceCitation({ sources, isShuffling }) {
  const [selectedDoc, setSelectedDoc] = useState(null);

  const getDocMeta = (docName) => {
    const name = (docName || '').toLowerCase();
    if (name.includes('student_directory') || name.includes('student_records')) {
      return { icon: Award, color: 'text-emerald-800 bg-emerald-500/15 border-emerald-300/60', category: 'Student Records' };
    }
    if (name.includes('grade') || name.includes('transcript')) {
      return { icon: Award, color: 'text-amber-800 bg-amber-500/15 border-amber-300/60', category: 'Grade Sheets' };
    }
    if (name.includes('exam') || name.includes('hall_ticket') || name.includes('schedule')) {
      return { icon: Calendar, color: 'text-sky-800 bg-sky-500/15 border-sky-300/60', category: 'Exam Timetables' };
    }
    if (name.includes('fee') || name.includes('deadline')) {
      return { icon: CreditCard, color: 'text-emerald-800 bg-emerald-500/15 border-emerald-300/60', category: 'Fee Structures' };
    }
    if (name.includes('document') || name.includes('certificate')) {
      return { icon: FileText, color: 'text-blue-800 bg-blue-500/15 border-blue-300/60', category: 'Official Documents' };
    }
    if (name.includes('placement') || name.includes('internship')) {
      return { icon: Briefcase, color: 'text-purple-800 bg-purple-500/15 border-purple-300/60', category: 'Placements' };
    }
    if (name.includes('hostel') || name.includes('mess')) {
      return { icon: Building, color: 'text-rose-800 bg-rose-500/15 border-rose-300/60', category: 'Hostel Regulations' };
    }
    return { icon: ShieldCheck, color: 'text-slate-800 bg-slate-500/15 border-slate-300/60', category: 'Campus Guidelines' };
  };

  if (!sources || sources.length === 0) {
    return (
      <div className="h-full flex flex-col justify-center items-center text-center p-6 glass-mirror-card rounded-3xl border border-white/90">
        <div className="w-12 h-12 rounded-2xl bg-sky-500/15 border border-sky-300/60 flex items-center justify-center mb-3 text-sky-700 shadow-sm">
          <BookOpen className="w-6 h-6 animate-pulse" />
        </div>
        <h4 className="font-display text-sm font-bold text-slate-900 mb-1">RAG Context Rail Idle</h4>
        <p className="text-xs text-slate-600 font-medium leading-relaxed max-w-xs font-sans">
          Source cards with vector similarity scores will automatically be retrieved from ChromaDB when a query is executed.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col gap-4">
      {/* DRAWER HEADER */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-xl bg-sky-500/15 border border-sky-300/50 text-sky-700">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-display text-sm font-black text-slate-900 tracking-tight">
              Retrieved Context Sources
            </h3>
            <p className="text-[11px] text-sky-700 font-semibold">ChromaDB Vector Matching Index</p>
          </div>
        </div>
        <span className="text-xs font-extrabold px-3 py-1 rounded-full bg-sky-500/15 border border-sky-300/60 text-sky-800 shadow-sm">
          {sources.length} Chunks
        </span>
      </div>

      {/* CARDS LIST */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {sources.map((src, idx) => {
          const meta = getDocMeta(src.document_name);
          const IconComp = meta.icon;
          const matchPercent = Math.round((src.score || 0) * 100);

          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.05 }}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setSelectedDoc(src)}
              className="glass-mirror-card glass-mirror-interactive rounded-2xl p-4 cursor-pointer group border border-white/90 hover:border-sky-400 relative overflow-hidden"
            >
              {/* Top Row: Category Tag & Match Percentage Gauge */}
              <div className="flex items-center justify-between mb-2.5">
                <span className={`text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-md border ${meta.color}`}>
                  {meta.category}
                </span>

                <div className="flex items-center gap-1.5">
                  <div className="w-14 h-1.5 rounded-full bg-slate-200 overflow-hidden border border-slate-300">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${
                        matchPercent >= 75 ? 'bg-gradient-to-r from-emerald-500 to-sky-500' :
                        matchPercent >= 50 ? 'bg-gradient-to-r from-sky-500 to-blue-600' : 'bg-amber-500'
                      }`}
                      style={{ width: `${matchPercent}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-bold text-sky-800 font-mono">
                    {matchPercent}%
                  </span>
                </div>
              </div>

              {/* Title */}
              <div className="flex items-center gap-2 mb-2">
                <IconComp className="w-4 h-4 text-sky-700 shrink-0" />
                <h4 className="font-display text-xs font-bold text-slate-900 group-hover:text-sky-800 transition-colors truncate">
                  {src.document_name}
                </h4>
              </div>

              {/* Snippet Excerpt */}
              <p className="text-xs text-slate-700 line-clamp-3 leading-relaxed font-sans italic bg-white/80 p-2.5 rounded-xl border border-slate-200/80 font-medium">
                "{src.snippet}"
              </p>

              <div className="mt-2 text-[10px] text-sky-700 font-bold opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-end gap-1">
                <span>Inspect Full Chunk</span>
                <ExternalLink className="w-3 h-3" />
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* SNIPPET INSPECTOR MODAL */}
      <AnimatePresence>
        {selectedDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-md">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-mirror-panel rounded-3xl border border-white/90 p-6 max-w-lg w-full shadow-2xl relative bg-white/95"
            >
              <button
                onClick={() => setSelectedDoc(null)}
                className="absolute top-4 right-4 p-2 rounded-2xl hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-2 mb-3">
                <FileText className="w-5 h-5 text-sky-700" />
                <h3 className="font-display text-base font-extrabold text-slate-900">
                  {selectedDoc.document_name}
                </h3>
              </div>

              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs font-bold px-3 py-1 rounded-full bg-sky-500/15 border border-sky-300/60 text-sky-800 font-mono">
                  Score: {selectedDoc.score} ({Math.round(selectedDoc.score * 100)}% Match)
                </span>
                <span className="text-xs text-slate-600 font-medium">Verified Campus Record</span>
              </div>

              <div className="bg-white/80 p-4 rounded-2xl border border-slate-200 max-h-80 overflow-y-auto text-xs text-slate-800 leading-relaxed font-mono whitespace-pre-wrap font-medium">
                {selectedDoc.snippet}
              </div>

              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => setSelectedDoc(null)}
                  className="px-5 py-2.5 bg-sky-500/15 hover:bg-sky-500/25 text-sky-800 text-xs font-bold rounded-2xl transition-colors border border-sky-300/60"
                >
                  Close Document
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
