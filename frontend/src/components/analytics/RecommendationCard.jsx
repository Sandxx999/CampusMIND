import React from 'react';
import { AlertOctagon, AlertTriangle, CheckCircle, Info, Lightbulb } from 'lucide-react';

const SEVERITY_STYLES = {
  critical: {
    bg: 'bg-rose-500/10 border-rose-500/30 text-rose-300',
    badgeBg: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    icon: AlertOctagon,
  },
  warning: {
    bg: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
    badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    icon: AlertTriangle,
  },
  positive: {
    bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
    badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    icon: CheckCircle,
  },
  info: {
    bg: 'bg-sky-500/10 border-sky-500/30 text-sky-300',
    badgeBg: 'bg-sky-500/20 text-sky-300 border-sky-500/40',
    icon: Info,
  },
};

export default function RecommendationCard({ recommendations }) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur-xl space-y-3">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="h-5 w-5 text-amber-400" />
        <h4 className="font-display font-bold text-slate-100">Explainable Academic Recommendations</h4>
      </div>

      <div className="space-y-3">
        {recommendations.map((rec, idx) => {
          const style = SEVERITY_STYLES[rec.severity] || SEVERITY_STYLES.info;
          const Icon = style.icon;

          return (
            <div key={idx} className={`rounded-xl border p-3.5 backdrop-blur-md transition-all ${style.bg}`}>
              <div className="flex items-start gap-3">
                <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border ${style.badgeBg}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <h5 className="font-display text-xs font-extrabold text-slate-100">{rec.recommendation}</h5>
                    <span className={`rounded-md border px-1.5 py-0.5 text-[9px] font-black uppercase tracking-wider ${style.badgeBg}`}>
                      {rec.severity}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-300">{rec.reason}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
