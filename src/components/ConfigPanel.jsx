import React from 'react';
import { Clock, Languages, Type, MoveVertical, Sparkles, Flame, Mic, Zap, Check, Cpu } from 'lucide-react';

const DURATIONS = [
  { value: 30, label: '30 sec', desc: 'Fast-paced Reels / TikToks' },
  { value: 45, label: '45 sec', desc: 'Storytelling & Clips' },
  { value: 60, label: '60 sec', desc: 'YouTube Shorts Max' },
  { value: 90, label: '90 sec', desc: 'Extended Shorts' },
];

const LANGUAGES = [
  { value: 'AUTO', label: 'Auto Detect', desc: 'Automatic speech language detection' },
  { value: 'ENGLISH', label: 'English', desc: 'English speech transcription' },
  { value: 'HINDI', label: 'Hindi', desc: 'Hindi speech transcription' },
  { value: 'HINGLISH', label: 'Hinglish', desc: 'Mixed Hindi + English natural speech' },
];

const CAPTION_STYLES = [
  { id: 'KARAOKE', name: 'Karaoke', icon: Mic, color: 'from-amber-500 to-yellow-400', desc: 'Word-by-word highlight as spoken' },
  { id: 'POP', name: 'Pop', icon: Flame, color: 'from-orange-500 to-red-500', desc: 'Dynamic scale & bounce effect' },
  { id: 'BOUNCE', name: 'Bounce', icon: Zap, color: 'from-emerald-500 to-teal-400', desc: 'Subtle vertical entry motion' },
  { id: 'CLASSIC', name: 'Classic', icon: Type, color: 'from-blue-500 to-indigo-500', desc: 'Clean subtitle with dark shadow' },
  { id: 'BOLD', name: 'Bold', icon: Sparkles, color: 'from-purple-500 to-pink-500', desc: 'Large high-impact headline captions' },
  { id: 'MINIMAL', name: 'Minimal', icon: Type, color: 'from-zinc-400 to-zinc-200', desc: 'Clean modern lightweight typography' },
];

const POSITIONS = [
  { value: 'TOP', label: 'Top' },
  { value: 'CENTER', label: 'Center' },
  { value: 'BOTTOM', label: 'Bottom' },
];

const ACCURACY_MODES = [
  { value: 'FAST', label: 'Fast', model: 'Whisper Base', desc: 'Fastest processing • Lowest VRAM' },
  { value: 'BALANCED', label: 'Balanced', model: 'Whisper Small', desc: 'Recommended • High precision & speed' },
  { value: 'ACCURATE', label: 'Accurate', model: 'Whisper Large-v3', desc: 'Maximum quality • Best for Hinglish' },
];

export default function ConfigPanel({ config, setConfig, onGenerate, isProcessing }) {
  return (
    <div className="max-w-4xl mx-auto glass-panel p-6 sm:p-8 rounded-3xl mb-12 shadow-2xl border border-white/10">
      <h2 className="text-xl sm:text-2xl font-extrabold text-white mb-6 flex items-center space-x-2">
        <Sparkles className="w-6 h-6 text-purple-400" />
        <span>Shorts Conversion Preferences</span>
      </h2>

      <div className="space-y-8">

        {/* 1. Target Duration Selector */}
        <div>
          <label className="block text-sm font-semibold text-zinc-300 mb-3 flex items-center space-x-2">
            <Clock className="w-4 h-4 text-purple-400" />
            <span>Target Clip Duration</span>
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {DURATIONS.map((dur) => {
              const isSelected = config.requested_duration === dur.value;
              return (
                <button
                  key={dur.value}
                  type="button"
                  onClick={() => setConfig({ ...config, requested_duration: dur.value })}
                  className={`p-4 rounded-2xl border text-left transition-all relative overflow-hidden ${
                    isSelected
                      ? 'bg-purple-600/30 border-purple-500 shadow-lg shadow-purple-500/10 text-white'
                      : 'bg-zinc-900/60 border-white/10 hover:border-white/20 text-zinc-400'
                  }`}
                >
                  {isSelected && (
                    <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-purple-500 flex items-center justify-center text-white text-xs">
                      <Check className="w-3 h-3" />
                    </div>
                  )}
                  <div className="text-lg font-bold text-white mb-0.5">{dur.label}</div>
                  <div className="text-xs text-zinc-400">{dur.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2. Caption Language Selector */}
        <div>
          <label className="block text-sm font-semibold text-zinc-300 mb-3 flex items-center space-x-2">
            <Languages className="w-4 h-4 text-pink-400" />
            <span>Speech Recognition Language</span>
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {LANGUAGES.map((lang) => {
              const isSelected = config.language === lang.value;
              return (
                <button
                  key={lang.value}
                  type="button"
                  onClick={() => setConfig({ ...config, language: lang.value })}
                  className={`p-3.5 rounded-2xl border text-left transition-all relative ${
                    isSelected
                      ? 'bg-pink-600/30 border-pink-500 shadow-lg shadow-pink-500/10 text-white'
                      : 'bg-zinc-900/60 border-white/10 hover:border-white/20 text-zinc-400'
                  }`}
                >
                  <div className="font-bold text-sm text-white mb-0.5">{lang.label}</div>
                  <div className="text-[11px] text-zinc-400 line-clamp-1">{lang.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2b. Accuracy Mode Selector */}
        <div>
          <label className="block text-sm font-semibold text-zinc-300 mb-3 flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>Speech AI Accuracy Mode</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {ACCURACY_MODES.map((mode) => {
              const isSelected = (config.accuracy_mode || 'BALANCED') === mode.value;
              return (
                <button
                  key={mode.value}
                  type="button"
                  onClick={() => setConfig({ ...config, accuracy_mode: mode.value })}
                  className={`p-4 rounded-2xl border text-left transition-all relative ${
                    isSelected
                      ? 'bg-emerald-600/20 border-emerald-500 shadow-lg shadow-emerald-500/10 text-white ring-1 ring-emerald-500'
                      : 'bg-zinc-900/60 border-white/10 hover:border-white/20 text-zinc-400'
                  }`}
                >
                  {isSelected && (
                    <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center text-white text-xs">
                      <Check className="w-3 h-3" />
                    </div>
                  )}
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-extrabold text-sm text-white">{mode.label}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 font-mono text-emerald-300">
                      {mode.model}
                    </span>
                  </div>
                  <div className="text-xs text-zinc-400">{mode.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. Caption Style Presets */}
        <div>
          <label className="block text-sm font-semibold text-zinc-300 mb-3 flex items-center space-x-2">
            <Type className="w-4 h-4 text-cyan-400" />
            <span>Animated Caption Presets</span>
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {CAPTION_STYLES.map((style) => {
              const isSelected = config.caption_style === style.id;
              const IconComp = style.icon;
              return (
                <button
                  key={style.id}
                  type="button"
                  onClick={() => setConfig({ ...config, caption_style: style.id })}
                  className={`p-4 rounded-2xl border text-left transition-all ${
                    isSelected
                      ? 'bg-gradient-to-br from-zinc-800 to-zinc-900 border-purple-500 shadow-lg shadow-purple-500/15 text-white ring-1 ring-purple-500'
                      : 'bg-zinc-900/60 border-white/10 hover:border-white/20 text-zinc-400'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-2">
                    <div className={`w-7 h-7 rounded-lg bg-gradient-to-tr ${style.color} flex items-center justify-center text-white`}>
                      <IconComp className="w-4 h-4" />
                    </div>
                    <span className="font-bold text-sm text-white">{style.name}</span>
                  </div>
                  <p className="text-xs text-zinc-400">{style.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* 4. Caption Position */}
        <div>
          <label className="block text-sm font-semibold text-zinc-300 mb-3 flex items-center space-x-2">
            <MoveVertical className="w-4 h-4 text-amber-400" />
            <span>Caption Placement</span>
          </label>
          <div className="flex space-x-3 max-w-md">
            {POSITIONS.map((pos) => {
              const isSelected = config.caption_position === pos.value;
              return (
                <button
                  key={pos.value}
                  type="button"
                  onClick={() => setConfig({ ...config, caption_position: pos.value })}
                  className={`flex-1 py-2.5 rounded-xl border text-xs font-bold transition-all ${
                    isSelected
                      ? 'bg-amber-500/20 border-amber-500 text-amber-300 shadow-sm'
                      : 'bg-zinc-900/60 border-white/10 hover:border-white/20 text-zinc-400'
                  }`}
                >
                  {pos.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-white/10">
          <button
            onClick={onGenerate}
            disabled={isProcessing}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-purple-600 via-pink-600 to-cyan-500 hover:from-purple-500 hover:via-pink-500 hover:to-cyan-400 text-white font-extrabold text-lg tracking-wide shadow-xl shadow-purple-600/30 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-3"
          >
            <Sparkles className="w-6 h-6 animate-spin-slow" />
            <span>GENERATE SHORTS</span>
          </button>
        </div>

      </div>
    </div>
  );
}
