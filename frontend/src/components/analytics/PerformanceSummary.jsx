import React from 'react';
import { Award, BookOpen, Layers, Star, TrendingUp } from 'lucide-react';

export default function PerformanceSummary({ performanceSummary }) {
  if (!performanceSummary) return null;

  const {
    cgpa,
    sgpa,
    backlogs,
    assessment_average,
    total_assessments,
    performance_by_course,
    performance_by_type,
    strongest_subjects,
    weakest_subjects,
  } = performanceSummary;

  return (
    <div className="space-y-4">
      {/* Key Academic Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/10 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400">
              <Award className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-xs font-semibold text-slate-300">Cumulative CGPA</span>
              <span className="font-display text-xl font-black text-indigo-300">{cgpa.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-500/20 text-sky-400">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-xs font-semibold text-slate-300">Current Semester SGPA</span>
              <span className="font-display text-xl font-black text-sky-400">{sgpa.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-purple-500/20 bg-purple-500/10 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/20 text-purple-400">
              <Star className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-xs font-semibold text-slate-300">Assessment Average</span>
              <span className="font-display text-xl font-black text-purple-300">
                {assessment_average !== null ? `${assessment_average}%` : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-xs font-semibold text-slate-300">Active Backlogs</span>
              <span className={`font-display text-xl font-black ${backlogs > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {backlogs}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Strongest & Weakest Subjects */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {strongest_subjects && strongest_subjects.length > 0 && (
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 backdrop-blur-xl">
            <h4 className="font-display text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2">Strongest Subjects</h4>
            <div className="space-y-2">
              {strongest_subjects.map((sub, idx) => (
                <div key={idx} className="flex justify-between items-center bg-white/5 rounded-xl px-3 py-2 text-xs">
                  <span className="font-medium text-slate-200">{sub.course_title}</span>
                  <span className="font-black text-emerald-400">{sub.score_pct}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {weakest_subjects && weakest_subjects.length > 0 && (
          <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4 backdrop-blur-xl">
            <h4 className="font-display text-xs font-bold uppercase tracking-wider text-rose-400 mb-2">Focus Areas (Lower Performance)</h4>
            <div className="space-y-2">
              {weakest_subjects.map((sub, idx) => (
                <div key={idx} className="flex justify-between items-center bg-white/5 rounded-xl px-3 py-2 text-xs">
                  <span className="font-medium text-slate-200">{sub.course_title}</span>
                  <span className="font-black text-rose-400">{sub.score_pct}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
