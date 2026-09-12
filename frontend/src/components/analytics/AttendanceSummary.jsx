import React from 'react';
import { Calendar, CheckCircle2, Clock, XCircle } from 'lucide-react';

export default function AttendanceSummary({ attendanceSummary }) {
  if (!attendanceSummary) return null;

  const { overall_attendance_pct, total_conducted, total_attended, total_missed, course_breakdown } = attendanceSummary;

  return (
    <div className="space-y-4">
      {/* Attendance Stats Header */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-500/20 text-sky-400">
              <Calendar className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-xs font-semibold text-slate-300">Overall Attendance</span>
              <span className="font-display text-xl font-black text-sky-400">{overall_attendance_pct}%</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/10 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-xs font-semibold text-slate-300">Total Conducted</span>
              <span className="font-display text-xl font-black text-indigo-300">{total_conducted}</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
              <CheckCircle2 className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-xs font-semibold text-slate-300">Classes Attended</span>
              <span className="font-display text-xl font-black text-emerald-400">{total_attended}</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-500/20 text-rose-400">
              <XCircle className="h-5 w-5" />
            </div>
            <div>
              <span className="block text-xs font-semibold text-slate-300">Classes Missed</span>
              <span className="font-display text-xl font-black text-rose-400">{total_missed}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Course Breakdown Table */}
      {course_breakdown && course_breakdown.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 backdrop-blur-xl">
          <h4 className="font-display text-sm font-bold text-slate-200 mb-3">Course-wise Attendance Breakdown</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-white/10 bg-white/5 font-semibold text-slate-200">
                <tr>
                  <th className="px-3 py-2">Course Title</th>
                  <th className="px-3 py-2 text-center">Conducted</th>
                  <th className="px-3 py-2 text-center">Attended</th>
                  <th className="px-3 py-2 text-center">Percentage</th>
                  <th className="px-3 py-2 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {course_breakdown.map((item, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition-all">
                    <td className="px-3 py-2 font-medium text-slate-100">{item.course_title}</td>
                    <td className="px-3 py-2 text-center">{item.conducted}</td>
                    <td className="px-3 py-2 text-center text-emerald-400 font-bold">{item.attended}</td>
                    <td className="px-3 py-2 text-center font-bold">
                      <span className={item.attendance_pct >= 75 ? 'text-emerald-400' : 'text-rose-400'}>
                        {item.attendance_pct}%
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-black uppercase tracking-wider ${
                        item.risk_level === 'SAFE' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                        item.risk_level === 'WATCH' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                        'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      }`}>
                        {item.risk_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
