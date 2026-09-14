import React, { useRef, useState } from 'react';
import { Play, Pause, Download, Edit3, RefreshCw, Volume2, VolumeX, Maximize, Clock, Share2, Check } from 'lucide-react';
import { getVideoUrl, getThumbnailUrl } from '../services/api';
import { formatTime } from '../utils/formatters';

export default function VideoCard({ clip, onEdit, onReRender, onToggleSelect, isSelected = true }) {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isReRendering, setIsReRendering] = useState(false);
  const [copied, setCopied] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const videoSrc = clip.output_filename ? getVideoUrl(clip.output_filename) : null;
  const thumbSrc = clip.thumbnail_filename ? getThumbnailUrl(clip.thumbnail_filename) : null;

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const toggleFullscreen = () => {
    if (!videoRef.current) return;
    if (videoRef.current.requestFullscreen) {
      videoRef.current.requestFullscreen();
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleDownload = () => {
    if (!videoSrc) return;
    const a = document.createElement('a');
    a.href = videoSrc;
    a.download = clip.output_filename || `short_clip_${clip.clip_index}.mp4`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleCopyLink = () => {
    if (!videoSrc) return;
    navigator.clipboard.writeText(window.location.origin + videoSrc);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReRenderClick = async () => {
    if (!onReRender) return;
    setIsReRendering(true);
    try {
      await onReRender(clip.id);
    } finally {
      setIsReRendering(false);
    }
  };

  const progressPercent = clip.duration > 0 ? (currentTime / clip.duration) * 100 : 0;
  const breakdown = clip.score_breakdown || {};

  return (
    <div className={`glass-card rounded-3xl overflow-hidden flex flex-col border transition-all duration-300 shadow-xl group ${
      isSelected ? 'border-purple-500/60 ring-2 ring-purple-500/20' : 'border-white/10 opacity-75 hover:opacity-100'
    }`}>
      
      {/* Video Container (9:16 Aspect Ratio) */}
      <div className="relative aspect-[9/16] bg-black overflow-hidden flex items-center justify-center">
        {videoSrc ? (
          <video
            ref={videoRef}
            src={videoSrc}
            poster={thumbSrc}
            loop
            playsInline
            onTimeUpdate={handleTimeUpdate}
            onEnded={() => setIsPlaying(false)}
            onPause={() => setIsPlaying(false)}
            onPlay={() => setIsPlaying(true)}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center bg-gradient-to-b from-purple-950/40 via-zinc-900 to-black text-zinc-400 space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 font-extrabold text-lg shadow-inner">
              ⚡ {clip.score || 85}
            </div>
            <div className="text-xs font-semibold text-zinc-300 line-clamp-3 italic px-2">
              "{clip.hook || clip.transcript || 'Candidate short preview'}"
            </div>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
              {clip.category || 'Candidate'}
            </span>
          </div>
        )}

        {/* Video Overlay Play Button */}
        {videoSrc && (
          <button
            onClick={togglePlay}
            className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
          >
            <div className="w-14 h-14 rounded-full bg-purple-600/90 text-white flex items-center justify-center shadow-lg shadow-purple-600/50 hover:scale-110 transition-transform">
              {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-1" />}
            </div>
          </button>
        )}

        {/* Top Badges */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none z-10">
          <span className="px-2.5 py-1 rounded-full bg-black/70 backdrop-blur-md text-[11px] font-bold text-white border border-white/10 flex items-center space-x-1">
            <Clock className="w-3 h-3 text-purple-400" />
            <span>{formatTime(clip.duration)} • {clip.category || 'Insight'}</span>
          </span>

          <span className="px-2.5 py-1 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-black font-black text-xs shadow-lg border border-amber-400/40">
            ⚡ {clip.score || 80}/100
          </span>
        </div>

        {/* Bottom Progress Bar & Player Controls */}
        {videoSrc && (
          <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/80 to-transparent space-y-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="w-full bg-white/20 h-1 rounded-full overflow-hidden">
              <div
                className="bg-purple-500 h-full transition-all duration-150"
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            <div className="flex items-center justify-between">
              <button
                onClick={toggleMute}
                className="p-1.5 rounded-full bg-black/60 text-white hover:bg-black/90 transition-colors"
              >
                {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
              </button>

              <div className="flex items-center space-x-1">
                <button
                  onClick={handleCopyLink}
                  className="p-1.5 rounded-full bg-black/60 text-white hover:bg-black/90 transition-colors"
                  title="Copy Direct Link"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Share2 className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={toggleFullscreen}
                  className="p-1.5 rounded-full bg-black/60 text-white hover:bg-black/90 transition-colors"
                  title="Fullscreen"
                >
                  <Maximize className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Card Info & Action Footer */}
      <div className="p-4 space-y-3 bg-zinc-900/80 flex-1 flex flex-col justify-between">
        
        {/* Hook & Reason AI Discovery Summary */}
        <div className="space-y-2">
          {clip.hook && (
            <div className="text-xs font-extrabold text-purple-300 line-clamp-2 leading-snug">
              💡 "{clip.hook}"
            </div>
          )}
          {clip.reason && (
            <div className="text-[11px] text-zinc-400 line-clamp-2 italic leading-tight">
              {clip.reason}
            </div>
          )}

          {/* Mini Score Breakdown Pills */}
          {breakdown.hook_score !== undefined && (
            <div className="flex flex-wrap gap-1 pt-1">
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">Hook {breakdown.hook_score}/20</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">Value {breakdown.value_score}/20</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-pink-500/10 text-pink-300 border border-pink-500/20">Emotion {breakdown.emotion_score}/20</span>
            </div>
          )}

          <div className="text-xs text-zinc-300 line-clamp-2 italic bg-zinc-800/50 p-2 rounded-xl border border-white/5 mt-1">
            "{clip.transcript || (clip.captions && clip.captions[0] ? clip.captions[0].text : 'No transcript snippet')}"
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2 pt-2">
          {onToggleSelect && (
            <button
              onClick={() => onToggleSelect(clip.id)}
              className={`w-full py-2.5 px-3 rounded-xl text-xs font-extrabold flex items-center justify-center space-x-2 transition-all shadow-md ${
                isSelected
                  ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-purple-600/30'
                  : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-white/10'
              }`}
            >
              <Check className={`w-4 h-4 ${isSelected ? 'opacity-100' : 'opacity-30'}`} />
              <span>{isSelected ? 'Selected Short ✓' : 'Select Short'}</span>
            </button>
          )}

          <div className="grid grid-cols-2 gap-2">
            {onEdit && (
              <button
                onClick={() => onEdit(clip)}
                className="py-2 px-2 rounded-xl text-xs font-semibold bg-zinc-800 hover:bg-zinc-700 text-purple-300 border border-purple-500/30 flex items-center justify-center space-x-1 transition-colors"
                title="Edit Captions"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Edit</span>
              </button>
            )}

            {videoSrc ? (
              <button
                onClick={handleDownload}
                className="py-2 px-2 rounded-xl text-xs font-bold bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white flex items-center justify-center space-x-1 shadow-md shadow-purple-600/20 transition-all"
                title="Download MP4 Short"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Save</span>
              </button>
            ) : onReRender ? (
              <button
                onClick={handleReRenderClick}
                disabled={isReRendering}
                className="py-2 px-2 rounded-xl text-xs font-semibold bg-zinc-800 hover:bg-zinc-700 text-cyan-300 border border-cyan-500/30 flex items-center justify-center space-x-1 transition-colors disabled:opacity-50"
                title="Render Final Video"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isReRendering ? 'animate-spin' : ''}`} />
                <span>Render</span>
              </button>
            ) : null}
          </div>
        </div>

      </div>

    </div>
  );
}
