import React, { useEffect, useState } from 'react';
import { fetchProjects, deleteJobProject } from '../services/api';
import { getStatusBadge, formatTime } from '../utils/formatters';
import { FolderOpen, Trash2, ExternalLink, Calendar, Film, RefreshCw, AlertCircle } from 'lucide-react';

export default function ProjectsView({ onOpenProject }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadProjectsList = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjects();
      setProjects(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjectsList();
  }, []);

  const handleDelete = async (jobId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this project and all its clips?')) return;
    try {
      await deleteJobProject(jobId);
      setProjects(projects.filter((p) => p.id !== jobId));
    } catch (err) {
      alert('Failed to delete project: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-16 text-center space-y-4">
        <div className="w-12 h-12 mx-auto rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center animate-spin">
          <RefreshCw className="w-6 h-6" />
        </div>
        <p className="text-sm text-zinc-400">Loading saved projects from database...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8 animate-in fade-in duration-200">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl sm:text-3xl font-black text-white flex items-center space-x-3">
            <FolderOpen className="w-8 h-8 text-pink-400" />
            <span>Saved Shorts Projects</span>
          </h2>
          <p className="text-sm text-zinc-400 mt-1">Past video conversion jobs stored in database</p>
        </div>

        <button
          onClick={loadProjectsList}
          className="p-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-white/10 transition-colors"
          title="Refresh List"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {projects.length === 0 ? (
        <div className="glass-panel p-12 rounded-3xl text-center space-y-4 border border-white/10">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-zinc-800 flex items-center justify-center text-zinc-500">
            <Film className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-white">No Projects Found</h3>
          <p className="text-xs text-zinc-400 max-w-sm mx-auto">
            You haven't converted any long videos into shorts yet. Upload a video to get started!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => {
            const badge = getStatusBadge(proj.status);
            const dateStr = new Date(proj.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric'
            });

            return (
              <div
                key={proj.id}
                onClick={() => onOpenProject(proj)}
                className="glass-card p-5 rounded-3xl border border-white/10 space-y-4 cursor-pointer group hover:border-purple-500/50"
              >
                <div className="flex items-start justify-between">
                  <div className="truncate max-w-[200px]">
                    <h4 className="font-bold text-base text-white truncate group-hover:text-purple-300 transition-colors">
                      {proj.original_filename}
                    </h4>
                    <span className="text-[11px] text-zinc-400 flex items-center space-x-1 mt-0.5">
                      <Calendar className="w-3 h-3 text-zinc-500" />
                      <span>{dateStr}</span>
                    </span>
                  </div>

                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold border ${badge.color}`}>
                    {badge.label}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center p-3 rounded-2xl bg-zinc-900/60 border border-white/5 text-xs">
                  <div>
                    <div className="text-[10px] text-zinc-500 font-semibold uppercase">Clips</div>
                    <div className="font-bold text-white mt-0.5">{proj.clips ? proj.clips.length : 0}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-zinc-500 font-semibold uppercase">Duration</div>
                    <div className="font-bold text-white mt-0.5">{proj.requested_duration}s</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-zinc-500 font-semibold uppercase">Style</div>
                    <div className="font-bold text-purple-300 mt-0.5 text-[11px]">{proj.caption_style}</div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    onClick={(e) => handleDelete(proj.id, e)}
                    className="p-2 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-colors"
                    title="Delete Project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <span className="text-xs font-semibold text-purple-400 group-hover:text-purple-300 flex items-center space-x-1">
                    <span>Open Project</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
