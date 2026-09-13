import React from 'react';
import { Zap, Subtitles, Crop, Languages } from 'lucide-react';

export default function Hero() {
  return (
    <div className="relative py-8 text-center max-w-4xl mx-auto px-4">
      {/* Background Ambient Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-48 bg-purple-600/15 blur-3xl rounded-full pointer-events-none" />

      {/* Badge */}
      <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs font-semibold uppercase tracking-wider mb-4">
        <Zap className="w-3.5 h-3.5 text-purple-400" />
        <span>AI Video Engine v1.0</span>
      </div>

      {/* Main Headline */}
      <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white mb-4 leading-tight">
        Turn Long Videos Into <br className="hidden sm:inline" />
        <span className="text-gradient">Scroll-Stopping Shorts</span>
      </h1>

      {/* Subheading */}
      <p className="text-base sm:text-lg text-zinc-400 max-w-2xl mx-auto mb-6">
        Upload your video. Let AI extract key moments, transcribe Hinglish/English speech, generate animated karaoke captions, and format to 9:16 vertical.
      </p>

      {/* Feature Highlights */}
      <div className="flex flex-wrap justify-center items-center gap-3 text-xs text-zinc-300">
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg glass-card">
          <Subtitles className="w-3.5 h-3.5 text-cyan-400" />
          <span>Animated Karaoke Captions</span>
        </div>
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg glass-card">
          <Languages className="w-3.5 h-3.5 text-pink-400" />
          <span>Hinglish & Hindi Speech-to-Text</span>
        </div>
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg glass-card">
          <Crop className="w-3.5 h-3.5 text-amber-400" />
          <span>9:16 Smart Center Reframing</span>
        </div>
      </div>
    </div>
  );
}
