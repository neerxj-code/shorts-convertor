import React from 'react';
import { RefreshCw, CheckCircle2, Video, Music, Subtitles, Crop, Film } from 'lucide-react';

const STAGES = [
  { id: 'ANALYZING', label: 'Analyze', icon: Video },
  { id: 'EXTRACTING_AUDIO', label: 'Audio', icon: Music },
  { id: 'TRANSCRIBING', label: 'Whisper AI', icon: Subtitles },
  { id: 'GENERATING_CAPTIONS', label: 'Captions', icon: Film },
  { id: 'RENDERING', label: '9:16 Render', icon: Crop },
];

export default function ProcessingModal({ job }) {
  if (!job) return null;

  const currentProgress = job.progress || 0;
  const stageMsg = job.stage_message || 'Processing video...';

  const getStageIndex = (status) => {
    switch (status) {
      case 'ANALYZING': return 0;
      case 'EXTRACTING_AUDIO': return 1;
      case 'TRANSCRIBING': return 2;
      case 'GENERATING_CAPTIONS': return 3;
      case 'RENDERING': return 4;
      case 'COMPLETED': return 5;
      default: return 0;
    }
  };

  const activeStageIdx = getStageIndex(job.status);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="max-w-xl w-full glass-panel p-8 rounded-3xl border border-purple-500/40 shadow-2xl space-y-6 text-center animate-in fade-in zoom-in duration-200">
        
        {/* Header Icon */}
        <div className="relative w-20 h-20 mx-auto">
          <div className="absolute inset-0 rounded-3xl bg-purple-500/20 blur-xl animate-pulse" />
          <div className="relative w-20 h-20 rounded-3xl bg-gradient-to-tr from-purple-600 to-pink-500 flex items-center justify-center text-white shadow-xl shadow-purple-500/30">
            <RefreshCw className="w-10 h-10 animate-spin" />
          </div>
        </div>

        {/* Title */}
        <div>
          <h3 className="text-2xl font-black text-white tracking-tight">Processing Your Shorts</h3>
          <p className="text-xs text-purple-300 font-medium mt-1">Real-time backend job pipeline executing...</p>
        </div>

        {/* Real Stage Indicator Icons */}
        <div className="flex justify-between items-center px-2 py-3 bg-zinc-900/70 rounded-2xl border border-white/10">
          {STAGES.map((st, i) => {
            const IconComp = st.icon;
            const isDone = i < activeStageIdx;
            const isCurrent = i === activeStageIdx;

            return (
              <div key={st.id} className="flex flex-col items-center space-y-1">
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
                    isDone
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      : isCurrent
                      ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30 ring-2 ring-purple-400'
                      : 'bg-zinc-800 text-zinc-600 border border-white/5'
                  }`}
                >
                  {isDone ? <CheckCircle2 className="w-5 h-5" /> : <IconComp className="w-4 h-4" />}
                </div>
                <span className={`text-[10px] font-semibold ${isCurrent ? 'text-purple-300' : isDone ? 'text-emerald-400' : 'text-zinc-500'}`}>
                  {st.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Progress Bar & Status Text */}
        <div className="space-y-3">
          <div className="flex justify-between items-center text-xs text-zinc-300 font-semibold px-1">
            <span className="truncate max-w-[300px] text-zinc-400">{stageMsg}</span>
            <span className="text-purple-400 font-bold text-sm">{currentProgress}%</span>
          </div>

          <div className="w-full bg-zinc-900 h-4 rounded-full overflow-hidden border border-white/15 p-0.5 relative">
            <div
              className="bg-gradient-to-r from-purple-600 via-pink-500 to-cyan-400 h-full rounded-full transition-all duration-500 shadow-md shadow-purple-500/20"
              style={{ width: `${currentProgress}%` }}
            />
          </div>
        </div>

        <p className="text-xs text-zinc-500 italic">
          Please wait while FFmpeg and Whisper process your video into vertical 9:16 clips.
        </p>

      </div>
    </div>
  );
}
