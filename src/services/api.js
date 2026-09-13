const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

export async function checkHealth() {
  const url = `${API_BASE_URL}/health`;
  try {
    const res = await fetch(url);
    if (!res.ok) {
      console.error(`[checkHealth] Error ${res.status}: ${res.statusText} at ${url}`);
      throw new Error(`Backend response status: ${res.status}`);
    }
    const data = await res.json();
    return data;
  } catch (err) {
    console.error(`[checkHealth] Failed to connect to ${url}:`, err);
    throw err;
  }
}

export async function uploadVideoFile(file, onProgress) {
  const uploadUrl = `${API_BASE_URL}/upload`;
  const formData = new FormData();
  formData.append("file", file);

  console.log(`[uploadVideoFile] Uploading '${file.name}' (${(file.size / (1024 * 1024)).toFixed(2)} MB) to ${uploadUrl}...`);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", uploadUrl);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        const percent = Math.round((e.loaded / e.total) * 100);
        onProgress(percent);
      }
    };

    xhr.onload = () => {
      console.log(`[uploadVideoFile] Server response HTTP ${xhr.status}:`, xhr.responseText);
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch (err) {
          console.error(`[uploadVideoFile] Failed to parse JSON response:`, xhr.responseText);
          reject(new Error("Invalid server JSON response"));
        }
      } else {
        try {
          const errData = JSON.parse(xhr.responseText);
          reject(new Error(errData.detail || `Upload failed with status ${xhr.status}`));
        } catch {
          reject(new Error(`Upload failed (HTTP ${xhr.status}): ${xhr.responseText || 'Server error'}`));
        }
      }
    };

    xhr.onerror = (e) => {
      console.error(`[uploadVideoFile] Network/connection error attempting POST ${uploadUrl}:`, e);
      reject(new Error(`Cannot connect to backend server at ${uploadUrl}. Please verify the FastAPI backend is running.`));
    };

    xhr.send(formData);
  });
}

export async function createProcessingJob(jobData) {
  const url = `${API_BASE_URL}/jobs`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(jobData),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    console.error(`[createProcessingJob] Error ${res.status} at ${url}:`, errData);
    throw new Error(errData.detail || `Failed to create processing job (HTTP ${res.status})`);
  }
  return res.json();
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Failed to fetch job status (HTTP ${res.status})`);
  return res.json();
}

export async function updateClipCaptions(clipId, captions) {
  const res = await fetch(`${API_BASE_URL}/captions/${clipId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ captions }),
  });
  if (!res.ok) throw new Error(`Failed to update captions (HTTP ${res.status})`);
  return res.json();
}

export async function reRenderClip(clipId, style, position) {
  const res = await fetch(`${API_BASE_URL}/render/${clipId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ caption_style: style, caption_position: position }),
  });
  if (!res.ok) throw new Error(`Failed to re-render clip (HTTP ${res.status})`);
  return res.json();
}

export async function fetchProjects() {
  const res = await fetch(`${API_BASE_URL}/projects`);
  if (!res.ok) throw new Error(`Failed to fetch projects (HTTP ${res.status})`);
  return res.json();
}

export async function deleteJobProject(jobId) {
  const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete project (HTTP ${res.status})`);
  return res.json();
}

export function getVideoUrl(filename) {
  return `${API_BASE_URL}/videos/${filename}`;
}

export function getThumbnailUrl(filename) {
  return `${API_BASE_URL}/thumbnails/${filename}`;
}
