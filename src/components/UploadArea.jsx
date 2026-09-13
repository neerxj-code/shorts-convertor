import React, { useState, useRef } from 'react';
import { Upload, FileVideo, CheckCircle2, AlertCircle, RefreshCw, Clock, HardDrive, Maximize2 } from 'lucide-react';
import { formatTime, formatFileSize } from '../utils/formatters';

export default function UploadArea({ onFileUploaded, isUploading, uploadProgress, uploadError, uploadedVideo, onReset }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = (file) => {
    if (!file.type.includes('video') && !file.name.match(/\.(mp4|mov|avi|mkv|webm)$/i)) {
      alert('Please upload a valid video file (MP4, MOV, AVI, MKV).');
      return;
    }
    onFileUploaded(file);
  };

  if (uploadedVideo) {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-purple-500/30 mb-8 max-w-4xl mx-auto shadow-xl">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="w-14 h-14 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
              <FileVideo className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white max-w-xs sm:max-w-md truncate">
                  {uploadedVideo.original_name}
                </h3>
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Ready</span>
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-xs text-zinc-400 mt-1">
                <span className="flex items-center space-x-1">
                  <HardDrive className="w-3.5 h-3.5 text-purple-400" />
                  <span>{uploadedVideo.size_mb} MB</span>
                </span>
                <span className="flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5 text-pink-400" />
                  <span>{formatTime(uploadedVideo.duration_sec)}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <Maximize2 className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{uploadedVideo.width} × {uploadedVideo.height}</span>
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={onReset}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-white/10 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Change File</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto mb-8">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska,video/webm"
        className="hidden"
      />

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`relative p-8 sm:p-12 rounded-3xl border-2 border-dashed transition-all cursor-pointer text-center glass-panel ${
          isDragOver
            ? 'border-purple-500 bg-purple-500/10 scale-[1.01]'
            : 'border-white/15 hover:border-purple-500/50 hover:bg-purple-500/5'
        }`}
      >
        {isUploading ? (
          <div className="space-y-4 max-w-md mx-auto py-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center animate-spin">
              <RefreshCw className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-semibold text-white">Uploading video...</h4>
            <div className="w-full bg-zinc-800 h-3 rounded-full overflow-hidden border border-white/10">
              <div
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-xs text-zinc-400">{uploadProgress}% complete</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-tr from-purple-600/30 to-pink-500/30 border border-purple-500/40 flex items-center justify-center text-purple-300 shadow-inner">
              <Upload className="w-8 h-8" />
            </div>
            
            <div>
              <h3 className="text-xl font-bold text-white mb-1">Drop your video here</h3>
              <p className="text-sm text-zinc-400">or click to browse files from your computer</p>
            </div>

            <div className="inline-flex items-center space-x-2 text-xs text-zinc-400 bg-zinc-900/60 px-4 py-1.5 rounded-full border border-white/10">
              <span>MP4</span>
              <span>•</span>
              <span>MOV</span>
              <span>•</span>
              <span>AVI</span>
              <span>•</span>
              <span>MKV</span>
              <span>•</span>
              <span>Max 500 MB</span>
            </div>
          </div>
        )}
      </div>

      {uploadError && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{uploadError}</span>
        </div>
      )}
    </div>
  );
}
