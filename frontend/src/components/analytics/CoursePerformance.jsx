import React from 'react';
import { BookOpen } from 'lucide-react';

export default function CoursePerformance({ performanceByCourse }) {
  if (!performanceByCourse || performanceByCourse.length === 0) return null;

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur-xl space-y-3">
      <div className="flex items-center gap-2 mb-3">
        <BookOpen className="h-5 w-5 text-indigo-400" />
        <h4 className="font-display font-bold text-slate-100">Course Assessment Performance Breakdown</h4>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {performanceByCourse.map((c, idx) => (
          <div key={idx} className="rounded-xl border border-white/10 bg-white/5 p-3.5 backdrop-blur-md">
            <div className="flex justify-between items-start mb-2">
              <h5 className="font-display text-xs font-bold text-slate-200">{c.course_title}</h5>
              <span className={`font-display text-xs font-black ${c.score_pct >= 70 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {c.score_pct}%
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full ${c.score_pct >= 75 ? 'bg-emerald-400' : c.score_pct >= 60 ? 'bg-amber-400' : 'bg-rose-400'}`}
                style={{ width: `${Math.min(100, Math.max(0, c.score_pct))}%` }}
              />
            </div>
            <div className="mt-2 text-[10px] text-slate-400 text-right">
              {c.assessment_count} assessment(s) recorded
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
