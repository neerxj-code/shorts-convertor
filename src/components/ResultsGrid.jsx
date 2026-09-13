import React from 'react';
import { Sparkles, ArrowLeft, Download, CheckCircle2 } from 'lucide-react';
import VideoCard from './VideoCard';

export default function ResultsGrid({ job, onEditClip, onReRenderClip, onReset }) {
  if (!job || !job.clips) return null;

  const completedClips = job.clips.filter((c) => c.status === 'COMPLETED');

  return (
    <div className="max-w-7xl mx-auto px-4 pb-16 space-y-8 animate-in fade-in duration-300">
      
      {/* Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-purple-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-semibold px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 mb-2">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Processing Complete</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-white">Your Shorts Are Ready!</h2>
          <p className="text-sm text-zinc-400 mt-1">
            Generated {completedClips.length} vertical 9:16 clips from <span className="text-purple-300 font-semibold">{job.original_filename}</span>
          </p>
        </div>

        <button
          onClick={onReset}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-white/10 text-sm font-semibold transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Convert Another Video</span>
        </button>
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {job.clips.map((clip) => (
          <VideoCard
            key={clip.id}
            clip={clip}
            onEdit={onEditClip}
            onReRender={onReRenderClip}
          />
        ))}
      </div>

    </div>
  );
}
