import React from 'react';
import { AlertTriangle, CheckCircle2, Info, ShieldAlert, ShieldCheck } from 'lucide-react';

const RISK_THEMES = {
  SAFE: {
    bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
    badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    icon: ShieldCheck,
    title: 'Safe Attendance Status',
  },
  WATCH: {
    bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
    badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    icon: Info,
    title: 'Watch Status - Near Threshold',
  },
  AT_RISK: {
    bg: 'bg-orange-500/10 border-orange-500/30 text-orange-400',
    badgeBg: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
    icon: AlertTriangle,
    title: 'At-Risk Attendance Level',
  },
  CRITICAL: {
    bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
    badgeBg: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    icon: ShieldAlert,
    title: 'Critical Risk - Below Threshold',
  },
  UNKNOWN: {
    bg: 'bg-slate-500/10 border-slate-500/30 text-slate-400',
    badgeBg: 'bg-slate-500/20 text-slate-300 border-slate-500/40',
    icon: Info,
    title: 'Insufficient Data State',
  },
};

export default function RiskIndicator({ riskAnalysis }) {
  if (!riskAnalysis) return null;

  const level = riskAnalysis.risk_level || 'UNKNOWN';
  const theme = RISK_THEMES[level] || RISK_THEMES.UNKNOWN;
  const IconComponent = theme.icon;

  return (
    <div className={`rounded-2xl border p-5 backdrop-blur-xl transition-all ${theme.bg}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${theme.badgeBg}`}>
            <IconComponent className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-display font-bold text-slate-100">{theme.title}</h3>
              <span className={`rounded-full border px-2.5 py-0.5 text-xs font-black uppercase tracking-wider ${theme.badgeBg}`}>
                {level}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-300">{riskAnalysis.explanation}</p>
          </div>
        </div>

        {level !== 'SAFE' && level !== 'UNKNOWN' && riskAnalysis.classes_needed_to_recover > 0 && (
          <div className="rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-right backdrop-blur-md">
            <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">Recovery Requirement</span>
            <span className="font-display text-sm font-extrabold text-white">
              +{riskAnalysis.classes_needed_to_recover} consecutive classes
            </span>
          </div>
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 border-t border-white/10 pt-4">
        <div>
          <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">Current Pct</span>
          <span className="font-display text-base font-extrabold text-white">{riskAnalysis.attendance_percentage}%</span>
        </div>
        <div>
          <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">Required Pct</span>
          <span className="font-display text-base font-extrabold text-slate-300">{riskAnalysis.required_percentage}%</span>
        </div>
        <div>
          <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">Classes Attended</span>
          <span className="font-display text-base font-extrabold text-emerald-400">
            {riskAnalysis.classes_attended} / {riskAnalysis.classes_conducted}
          </span>
        </div>
        <div>
          <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">Deficit Pct</span>
          <span className={`font-display text-base font-extrabold ${riskAnalysis.deficit_percentage > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {riskAnalysis.deficit_percentage}%
          </span>
        </div>
      </div>
    </div>
  );
}
