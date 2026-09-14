import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import UploadArea from './components/UploadArea';
import ConfigPanel from './components/ConfigPanel';
import ProcessingModal from './components/ProcessingModal';
import ResultsGrid from './components/ResultsGrid';
import CaptionEditorModal from './components/CaptionEditorModal';
import ProjectsView from './components/ProjectsView';

import {
  checkHealth,
  uploadVideoFile,
  createProcessingJob,
  getJobStatus,
  updateClipCaptions,
  reRenderClip
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('create'); // 'create' | 'projects'
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking' | 'connected' | 'offline'

  // File Upload state
  const [uploadedVideo, setUploadedVideo] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState(null);

  // Video Configuration state
  const [config, setConfig] = useState({
    requested_duration: 30,
    language: 'HINGLISH',
    caption_style: 'KARAOKE',
    caption_position: 'BOTTOM',
    accuracy_mode: 'BALANCED'
  });

  // Processing & Job state
  const [currentJob, setCurrentJob] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const pollIntervalRef = useRef(null);

  // Caption Editor modal state
  const [editingClip, setEditingClip] = useState(null);

  // Health check on mount & poll every 5s
  useEffect(() => {
    const verifyHealth = async () => {
      try {
        const data = await checkHealth();
        if (data && (data.status === 'ok' || data.status === 'online')) {
          setBackendStatus('connected');
        } else {
          setBackendStatus('offline');
        }
      } catch (err) {
        setBackendStatus('offline');
      }
    };
    verifyHealth();
    const timer = setInterval(verifyHealth, 5000);
    return () => clearInterval(timer);
  }, []);

  // Cleanup polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Handle Video Upload
  const handleFileUploaded = async (file) => {
    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);

    try {
      const data = await uploadVideoFile(file, (percent) => setUploadProgress(percent));
      setUploadedVideo(data);
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  // Reset uploaded video
  const handleReset = () => {
    setUploadedVideo(null);
    setCurrentJob(null);
    setIsProcessing(false);
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
  };

  // Submit Job for Processing
  const handleGenerateShorts = async () => {
    if (!uploadedVideo) return;
    setIsProcessing(true);

    try {
      const { job_id } = await createProcessingJob({
        filename: uploadedVideo.filename,
        requested_duration: config.requested_duration,
        language: config.language,
        caption_style: config.caption_style,
        caption_position: config.caption_position,
        accuracy_mode: config.accuracy_mode || 'BALANCED'
      });

      // Poll job status
      pollIntervalRef.current = setInterval(async () => {
        try {
          const jobData = await getJobStatus(job_id);
          setCurrentJob(jobData);

          if (jobData.status === 'COMPLETED' || jobData.status === 'FAILED') {
            clearInterval(pollIntervalRef.current);
            setIsProcessing(false);
          }
        } catch (err) {
          console.error('Job polling error:', err);
        }
      }, 1500);

    } catch (err) {
      alert('Failed to start processing job: ' + err.message);
      setIsProcessing(false);
    }
  };

  // Open clip in Caption Editor
  const handleEditClip = (clip) => {
    setEditingClip(clip);
  };

  // Save updated captions & re-render clip
  const handleSaveAndRenderClip = async (clipId, updatedCaptions, style, position) => {
    await updateClipCaptions(clipId, updatedCaptions);
    await reRenderClip(clipId, style, position);

    // Refresh current job data to display re-rendered video
    if (currentJob) {
      const refreshedJob = await getJobStatus(currentJob.id);
      setCurrentJob(refreshedJob);
    }
  };

  // Open project from Projects page
  const handleOpenProject = (projectJob) => {
    setCurrentJob(projectJob);
    setActiveTab('create');
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col selection:bg-purple-500 selection:text-white">
      
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendStatus={backendStatus}
      />

      {/* Main Page Views */}
      <main className="flex-1 pb-16">
        {activeTab === 'create' ? (
          <>
            {/* Show Hero when no results generated yet */}
            {!currentJob || currentJob.status !== 'COMPLETED' ? (
              <>
                <Hero />
                <div className="px-4">
                  <UploadArea
                    onFileUploaded={handleFileUploaded}
                    isUploading={isUploading}
                    uploadProgress={uploadProgress}
                    uploadError={uploadError}
                    uploadedVideo={uploadedVideo}
                    onReset={handleReset}
                  />

                  {uploadedVideo && (
                    <ConfigPanel
                      config={config}
                      setConfig={setConfig}
                      onGenerate={handleGenerateShorts}
                      isProcessing={isProcessing}
                    />
                  )}
                </div>
              </>
            ) : (
              /* Show Results Grid when job is completed */
              <div className="pt-8">
                <ResultsGrid
                  job={currentJob}
                  onEditClip={handleEditClip}
                  onReRenderClip={async (clipId) => {
                    await reRenderClip(clipId, config.caption_style, config.caption_position);
                    const refreshed = await getJobStatus(currentJob.id);
                    setCurrentJob(refreshed);
                  }}
                  onReset={handleReset}
                  onUpdateJob={setCurrentJob}
                />
              </div>
            )}
          </>
        ) : (
          /* Projects View */
          <ProjectsView onOpenProject={handleOpenProject} />
        )}
      </main>

      {/* Real-time Background Processing Modal */}
      {isProcessing && <ProcessingModal job={currentJob} />}

      {/* Interactive Caption Editor Modal */}
      {editingClip && (
        <CaptionEditorModal
          clip={editingClip}
          onClose={() => setEditingClip(null)}
          onSaveAndRender={handleSaveAndRenderClip}
        />
      )}

      {/* Footer */}
      <footer className="py-6 border-t border-white/5 text-center text-xs text-zinc-600 glass-panel">
        <p>Shortify AI Video Converter • Production Full-Stack Engine</p>
      </footer>

    </div>
  );
}
