import React from 'react';
import { Database, Info } from 'lucide-react';

export default function AnalyticsEmptyState({ title = "Insufficient Analytics Data", description = "No academic records found for computation." }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-slate-900/60 p-8 text-center backdrop-blur-xl">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-sky-500/30 bg-sky-500/15 text-sky-400 mb-4">
        <Database className="h-6 w-6" />
      </div>
      <h4 className="font-display text-base font-bold text-slate-100 mb-1">{title}</h4>
      <p className="max-w-md text-xs text-slate-400">{description}</p>
    </div>
  );
}
