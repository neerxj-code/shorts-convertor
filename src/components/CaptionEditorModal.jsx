import React, { useState, useRef } from 'react';
import { X, Save, RefreshCw, Type, MoveVertical, Check, Clock, Plus, Trash2, Play } from 'lucide-react';
import { getVideoUrl } from '../services/api';
import { formatTimeMs } from '../utils/formatters';

const STYLES = ['KARAOKE', 'POP', 'BOUNCE', 'CLASSIC', 'BOLD', 'MINIMAL'];
const POSITIONS = ['TOP', 'CENTER', 'BOTTOM'];

export default function CaptionEditorModal({ clip, onClose, onSaveAndRender }) {
  if (!clip) return null;

  const [captions, setCaptions] = useState(clip.captions || []);
  const [selectedStyle, setSelectedStyle] = useState('KARAOKE');
  const [selectedPosition, setSelectedPosition] = useState('BOTTOM');
  const [isSaving, setIsSaving] = useState(false);
  const videoRef = useRef(null);

  const videoSrc = clip.output_filename ? getVideoUrl(clip.output_filename) : null;

  const handleTextChange = (index, newText) => {
    const updated = [...captions];
    updated[index] = { ...updated[index], text: newText };
    setCaptions(updated);
  };

  const handleSegmentClick = (startSec) => {
    if (videoRef.current) {
      videoRef.current.currentTime = startSec;
      videoRef.current.play();
    }
  };

  const handleAddSegment = () => {
    const lastCap = captions[captions.length - 1];
    const newStart = lastCap ? lastCap.end : 0;
    const newEnd = newStart + 3;
    setCaptions([
      ...captions,
      { start: newStart, end: newEnd, text: 'New caption segment', words: [] }
    ]);
  };

  const handleDeleteSegment = (index, e) => {
    e.stopPropagation();
    setCaptions(captions.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSaveAndRender(clip.id, captions, selectedStyle, selectedPosition);
      onClose();
    } catch (err) {
      alert('Failed to re-render clip: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="max-w-5xl w-full glass-panel rounded-3xl border border-purple-500/40 shadow-2xl overflow-hidden flex flex-col my-8">
        
        {/* Header */}
        <div className="p-6 border-b border-white/10 flex items-center justify-between bg-zinc-900/80">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center space-x-2">
              <Type className="w-5 h-5 text-purple-400" />
              <span>Interactive Caption & Subtitle Editor</span>
            </h3>
            <p className="text-xs text-zinc-400 mt-0.5">Click any segment to jump to that timestamp in the video preview</p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-12 gap-6 max-h-[70vh] overflow-y-auto">
          
          {/* Left Column: Video Preview & Styling Options */}
          <div className="md:col-span-5 space-y-4">
            <div className="aspect-[9/16] bg-black rounded-2xl overflow-hidden border border-white/10 shadow-lg relative max-h-[380px] mx-auto">
              {videoSrc && (
                <video
                  ref={videoRef}
                  src={videoSrc}
                  controls
                  playsInline
                  className="w-full h-full object-cover"
                />
              )}
            </div>

            {/* Styling Switchers */}
            <div className="space-y-3 bg-zinc-900/60 p-4 rounded-2xl border border-white/5">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-2">Preset Style</label>
                <div className="grid grid-cols-3 gap-1.5">
                  {STYLES.map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setSelectedStyle(st)}
                      className={`py-1.5 rounded-lg text-[11px] font-bold border transition-colors ${
                        selectedStyle === st
                          ? 'bg-purple-600 border-purple-500 text-white'
                          : 'bg-zinc-800 border-white/5 text-zinc-400 hover:text-zinc-200'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-2">Placement</label>
                <div className="flex space-x-2">
                  {POSITIONS.map((pos) => (
                    <button
                      key={pos}
                      type="button"
                      onClick={() => setSelectedPosition(pos)}
                      className={`flex-1 py-1.5 rounded-lg text-[11px] font-bold border transition-colors ${
                        selectedPosition === pos
                          ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                          : 'bg-zinc-800 border-white/5 text-zinc-400 hover:text-zinc-200'
                      }`}
                    >
                      {pos}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Interactive Transcript Segment List */}
          <div className="md:col-span-7 space-y-3 flex flex-col">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-purple-300">
                Transcript Segments ({captions.length})
              </h4>

              <button
                onClick={handleAddSegment}
                className="flex items-center space-x-1 text-xs font-semibold text-purple-400 hover:text-purple-300 px-3 py-1 rounded-lg bg-purple-500/10 border border-purple-500/30 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Segment</span>
              </button>
            </div>

            <div className="space-y-3 flex-1 overflow-y-auto pr-1">
              {captions.length === 0 ? (
                <div className="p-8 text-center text-xs text-zinc-500 bg-zinc-900/40 rounded-2xl">
                  No caption segments found for this clip. Click "Add Segment" to create one.
                </div>
              ) : (
                captions.map((cap, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSegmentClick(cap.start)}
                    className="p-3.5 rounded-2xl bg-zinc-900/70 border border-white/10 hover:border-purple-500/40 space-y-2 cursor-pointer transition-all group"
                  >
                    <div className="flex items-center justify-between text-[11px] text-zinc-400 font-mono">
                      <span className="flex items-center space-x-1.5 text-purple-300 group-hover:text-purple-200">
                        <Play className="w-3 h-3 text-purple-400" />
                        <Clock className="w-3 h-3" />
                        <span>{formatTimeMs(cap.start)} ─ {formatTimeMs(cap.end)}</span>
                      </span>

                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] text-zinc-500">#{idx + 1}</span>
                        <button
                          onClick={(e) => handleDeleteSegment(idx, e)}
                          className="p-1 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                          title="Delete Segment"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <textarea
                      value={cap.text}
                      onChange={(e) => handleTextChange(idx, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      rows={2}
                      className="w-full bg-zinc-950/80 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:border-purple-500 focus:outline-none resize-none font-medium"
                    />
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-white/10 bg-zinc-900/90 flex items-center justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold text-zinc-400 hover:text-white transition-colors"
          >
            Cancel
          </button>

          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-extrabold text-xs shadow-lg shadow-purple-600/30 flex items-center space-x-2 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isSaving ? 'animate-spin' : ''}`} />
            <span>Save & Re-render Video</span>
          </button>
        </div>

      </div>
    </div>
  );
}
