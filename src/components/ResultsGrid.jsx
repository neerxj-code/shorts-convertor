import React, { useState } from 'react';
import { Sparkles, ArrowLeft, Download, CheckCircle2, Flame, RefreshCw, Check } from 'lucide-react';
import VideoCard from './VideoCard';
import { selectClips, discoverClips } from '../services/api';

export default function ResultsGrid({ job, onEditClip, onReRenderClip, onReset, onUpdateJob }) {
  if (!job || !job.clips) return null;

  const [selectedIds, setSelectedIds] = useState(() => {
    return job.clips.filter(c => c.is_selected !== false).map(c => c.id);
  });
  const [isSavingSelection, setIsSavingSelection] = useState(false);
  const [isReDiscovering, setIsReDiscovering] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');

  const toggleSelect = (clipId) => {
    setSelectedIds(prev => 
      prev.includes(clipId) ? prev.filter(id => id !== clipId) : [...prev, clipId]
    );
  };

  const handleSaveSelection = async () => {
    setIsSavingSelection(true);
    try {
      const res = await selectClips(job.id, selectedIds);
      if (onUpdateJob) onUpdateJob(res);
      setSaveSuccessMsg(`Saved ${selectedIds.length} selected candidate short(s)!`);
      setTimeout(() => setSaveSuccessMsg(''), 3500);
    } catch (err) {
      console.error('Failed to save selected clips:', err);
    } finally {
      setIsSavingSelection(false);
    }
  };

  const handleRediscover = async (targetDur) => {
    setIsReDiscovering(true);
    try {
      const res = await discoverClips(job.id, targetDur, 6);
      if (onUpdateJob) onUpdateJob(res);
      if (res.clips) {
        setSelectedIds(res.clips.map(c => c.id));
      }
    } catch (err) {
      console.error('Failed to rediscover clips:', err);
    } finally {
      setIsReDiscovering(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 pb-16 space-y-8 animate-in fade-in duration-300">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-purple-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-bold px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 mb-2">
            <Flame className="w-3.5 h-3.5 text-amber-400" />
            <span>AI DISCOVERED MOMENTS</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-white">BEST SHORTS</h2>
          <p className="text-sm text-zinc-400 mt-1">
            Ranked {job.clips.length} high-value moments from <span className="text-purple-300 font-semibold">{job.original_filename}</span>
          </p>
        </div>

        {/* Target Duration Discovery Quick Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-zinc-400 font-semibold mr-1">Re-discover Target:</span>
          {[30, 45, 60, 90].map(dur => (
            <button
              key={dur}
              onClick={() => handleRediscover(dur)}
              disabled={isReDiscovering}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                job.requested_duration === dur
                  ? 'bg-purple-600 text-white border-purple-400 shadow-md shadow-purple-600/30'
                  : 'bg-zinc-800 text-zinc-300 border-white/10 hover:border-purple-400/50'
              }`}
            >
              {dur}s
            </button>
          ))}
        </div>

        <button
          onClick={onReset}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-white/10 text-sm font-semibold transition-colors shrink-0"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>New Video</span>
        </button>
      </div>

      {saveSuccessMsg && (
        <div className="p-4 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-200 text-sm font-bold flex items-center space-x-2 animate-in fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {/* Results Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {job.clips.map((clip) => (
          <VideoCard
            key={clip.id}
            clip={clip}
            onEdit={onEditClip}
            onReRender={onReRenderClip}
            onToggleSelect={toggleSelect}
            isSelected={selectedIds.includes(clip.id)}
          />
        ))}
      </div>

      {/* Selection Action Bar */}
      <div className="sticky bottom-6 glass-panel p-4 rounded-2xl border border-purple-500/40 shadow-2xl flex items-center justify-between max-w-2xl mx-auto backdrop-blur-xl bg-zinc-950/80">
        <div className="text-xs sm:text-sm text-zinc-300 font-semibold">
          <span className="text-purple-400 font-extrabold text-base mr-1">{selectedIds.length}</span> short(s) selected for export
        </div>

        <button
          onClick={handleSaveSelection}
          disabled={isSavingSelection || selectedIds.length === 0}
          className="py-2.5 px-6 rounded-xl font-black text-sm bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white flex items-center space-x-2 shadow-lg shadow-purple-600/30 transition-all disabled:opacity-50"
        >
          {isSavingSelection ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          <span>Generate Selected Shorts</span>
        </button>
      </div>

    </div>
  );
}
