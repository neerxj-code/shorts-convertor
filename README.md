# ⚡ Shortify - AI Long-to-Short Video Generator

**Shortify** is a production-grade AI video generator that automatically transforms long landscape videos and podcasts (20–90+ mins) into viral, high-converting 9:16 vertical short clips (YouTube Shorts, Instagram Reels, TikToks).

It features **100% local speech-to-text recognition** using OpenAI Whisper, **AI-powered moment discovery & scoring**, OpenCV face-tracking 9:16 reframing, word-level animated karaoke captions, native Hinglish code-switching preservation, and an interactive video subtitle editor.

---

## 🔥 Key Features

- **🧠 AI Short Candidate Discovery & Scoring**:
  - Automatically analyzes master video transcripts to find high-value moments.
  - Multi-factor internal scoring (0–100): **Hook Strength**, **Practical Value**, **Emotional Intensity**, **Context Completeness**, **Ending Quality**, and **Silence Penalties**.
  - Auto-categorizes clips: `Educational`, `Story`, `Insight`, `Advice`, `Opinion`.
  - Non-maximum suppression deduplication ensures high diversity without overlapping clips.
- **🎙️ 100% Local Speech AI Processing**:
  - Runs completely offline via PyTorch and local Whisper models (`base`, `small`, `medium`, `large-v3`). No external API keys required.
- **🎯 Smart Target Durations (30s, 45s, 60s, 90s)**:
  - Finds coherent cut windows near requested duration target without cutting speaker mid-sentence.
- **📷 Smart 9:16 Reframing & Active Speaker Face Tracking**:
  - Dynamically centers vertical 9:16 viewport around active speaker faces using OpenCV detection with graceful fallback to center-crop.
- **🗣️ Native Hinglish & Code-Switching Support**:
  - Preserves natural spoken Hinglish (Hindi + English) without unwanted auto-translation.
- **🛡️ VAD & Hallucination Suppression**:
  - Filters out silent pause hallucinations and phantom subtitle phrases (`no_speech_prob`, `avg_logprob`, and `compression_ratio` thresholding).
- **🎨 Animated Karaoke & Subtitle Styles**:
  - **Karaoke** (word-by-word centisecond highlight), **Pop**, **Bounce**, **Classic**, **Bold**, and **Minimal**.
- **✏️ Interactive Subtitle & Candidate Editor**:
  - Real-time video preview seeker, candidate selector, word timing editor, and on-demand re-rendering.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide Icons |
| **Backend API** | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| **AI / ASR** | PyTorch, OpenAI Whisper (Local ASR) |
| **Short Discovery Engine** | Modular `ClipAnalysisProvider` (Rule-based & Heuristic NLP) |
| **Computer Vision** | OpenCV (Haar Cascade Face Tracking & Speaker Frame Positioning) |
| **Media Processing** | FFmpeg, FFprobe, imageio-ffmpeg |
| **Database** | SQLite3 + SQLAlchemy (Auto-migrating Schema) |

---

## 📁 Repository Structure

```text
shorts-convertor/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI REST endpoints (upload, jobs, discover, captions, render, health)
│   │   ├── core/             # App configuration, settings & DB engine with auto-migrations
│   │   ├── models/           # SQLAlchemy DB models & Pydantic schemas
│   │   ├── services/         # Whisper ASR, Clip Discovery, Face-Tracking Cropping, ASS Subtitles, FFmpeg Engine
│   │   ├── utils/            # File management & safe naming utilities
│   │   ├── workers/          # Background worker job processor
│   │   └── main.py           # FastAPI server entry point
│   ├── .env.example          # Environment variables template
│   └── requirements.txt      # Python dependencies
├── src/
│   ├── components/           # React UI components (Hero, UploadArea, ConfigPanel, ResultsGrid, VideoCard, Editor)
│   ├── services/             # API client services
│   ├── App.jsx               # Main React Application
│   └── index.css             # Design tokens & glassmorphism styling
├── package.json
└── vite.config.js
```

---

## 🚀 Quick Start & Installation

### Prerequisites

- **Node.js**: v18.0.0 or higher
- **Python**: v3.10 or higher
- **FFmpeg**: System FFmpeg installed or imageio-ffmpeg auto-bundled

---

### 1. Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your `.env` file from the example template:
   ```bash
   cp .env.example .env
   ```

5. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *The API server will run at `http://127.0.0.1:8000`. Interactive OpenAPI docs available at `http://127.0.0.1:8000/docs`.*

---

### 2. Frontend Setup (React + Vite)

1. In the project root directory, install npm packages:
   ```bash
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```

3. Open your browser at `http://localhost:5173`.

---

## ⚙️ Environment Variables (`.env`)

Configure the following variables in `backend/.env`:

```env
APP_ENV=development
MAX_UPLOAD_SIZE_MB=500
WHISPER_MODEL=small
ACCURACY_MODE=BALANCED
FFMPEG_PATH=
FFPROBE_PATH=
DATABASE_URL=sqlite:///./shortify.db
FILE_RETENTION_HOURS=24
```

---

## 📡 Key REST API Endpoints

- `GET /api/health` - Health check, GPU status & loaded FFmpeg paths
- `POST /api/upload` - Upload long video file (supports `.mp4`, `.mov`, `.mkv`, `.avi`)
- `POST /api/jobs` - Create video conversion job with duration, style & accuracy parameters
- `GET /api/jobs/{job_id}` - Fetch job progress, status & candidate clip metadata
- `POST /api/jobs/{job_id}/discover-clips` - Re-analyze transcript to discover short candidates for a target duration
- `POST /api/jobs/{job_id}/select-clips` - Update selected short candidates for batch export
- `PUT /api/captions/{clip_id}` - Save edited subtitle segments
- `POST /api/render/{clip_id}` - Re-render video clip with updated captions or styles
- `GET /api/projects` - List all processed video projects

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more details.
