import React from 'react';
import { Film, FolderOpen, Sparkles, Server, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, backendStatus }) {
  const renderStatusBadge = () => {
    if (backendStatus === 'connected' || backendStatus === 'online') {
      return (
        <div className="flex items-center space-x-1.5 text-emerald-400 font-medium">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Backend Connected</span>
        </div>
      );
    } else if (backendStatus === 'checking') {
      return (
        <div className="flex items-center space-x-1.5 text-amber-400 font-medium">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          <span>Checking...</span>
        </div>
      );
    } else {
      return (
        <div className="flex items-center space-x-1.5 text-rose-400 font-medium">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>Backend Offline</span>
        </div>
      );
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 glass-panel">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Logo */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('create')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Film className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-xl font-extrabold tracking-wider text-white">SHORTIFY</span>
            <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
              AI ENGINE
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('create')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'create'
                ? 'bg-purple-600/30 text-purple-200 border border-purple-500/40 shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span>Create Shorts</span>
          </button>

          <button
            onClick={() => setActiveTab('projects')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'projects'
                ? 'bg-purple-600/30 text-purple-200 border border-purple-500/40 shadow-sm'
                : 'text-zinc-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <FolderOpen className="w-4 h-4 text-pink-400" />
            <span>Projects</span>
          </button>
        </nav>

        {/* System Backend Health Status */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-zinc-900/80 border border-white/10 text-xs">
          <Server className="w-3.5 h-3.5 text-zinc-400" />
          {renderStatusBadge()}
        </div>

      </div>
    </header>
  );
}
