export function formatTime(seconds) {
  if (isNaN(seconds) || seconds === null || seconds === undefined) return "00:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export function formatTimeMs(seconds) {
  if (isNaN(seconds) || seconds === null || seconds === undefined) return "00:00.0";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const tenths = Math.floor((seconds % 1) * 10);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${tenths}`;
}

export function formatFileSize(bytes) {
  if (!bytes) return "0 MB";
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(1)} MB`;
}

export function getStatusBadge(status) {
  switch (status) {
    case "COMPLETED":
      return { label: "Completed", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" };
    case "UPLOADING":
      return { label: "Uploading", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" };
    case "ANALYZING":
    case "EXTRACTING_AUDIO":
    case "TRANSCRIBING":
    case "GENERATING_CAPTIONS":
    case "RENDERING":
      return { label: "Processing", color: "bg-amber-500/20 text-amber-400 border-amber-500/30 animate-pulse" };
    case "FAILED":
      return { label: "Failed", color: "bg-rose-500/20 text-rose-400 border-rose-500/30" };
    default:
      return { label: status, color: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30" };
  }
}
