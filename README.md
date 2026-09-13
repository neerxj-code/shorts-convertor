# ⚡ Shortify - AI Long-to-Short Video Converter

**Shortify** is a production-grade AI web application that automatically transforms long landscape videos and podcasts into viral 9:16 vertical short clips (YouTube Shorts, Instagram Reels, TikToks).

It features **100% local speech-to-text recognition** using OpenAI Whisper, word-level animated karaoke captions, Hinglish code-switching preservation, intelligent center-reframing, and an interactive video subtitle editor.

---

## 🔥 Key Features

- **🎙️ 100% Local Speech AI Processing**:
  - No external cloud API keys required. Runs completely offline via PyTorch and local Whisper models (`base`, `small`, `medium`, `large-v3`).
- **🎯 Selectable Accuracy Modes**:
  - **FAST**: Whisper `base` (~3x speed, low VRAM usage).
  - **BALANCED**: Whisper `small` (Optimal accuracy & speed balance).
  - **ACCURATE**: Whisper `large-v3` (Maximum precision for Hinglish & multi-speaker clarity).
- **🗣️ Native Hinglish & Code-Switching Support**:
  - Preserves spoken Hinglish (Hindi + English) without unwanted auto-translation.
- **🔊 `loudnorm` Audio Pre-Processing**:
  - Automatically normalizes low-volume microphones, speech dynamics, and background noise prior to ASR.
- **🛡️ VAD & Hallucination Suppression**:
  - Filters out silent pause hallucinations and phantom subtitle phrases (`no_speech_prob`, `avg_logprob`, and `compression_ratio` thresholding).
- **🎨 Animated Subtitle Styles**:
  - **Karaoke** (word-by-word centisecond highlight), **Pop**, **Bounce**, **Classic**, **Bold**, and **Minimal**.
- **✏️ Interactive Subtitle Editor**:
  - Real-time video preview seeker, word timing editor, segment addition/deletion, and re-rendering on demand.
- **📱 9:16 Smart Vertical Reframing**:
  - Automatically center-crops landscape videos into portrait mobile format.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide Icons |
| **Backend API** | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| **AI / ASR** | PyTorch, OpenAI Whisper (Local ASR) |
| **Media Processing** | FFmpeg, FFprobe, imageio-ffmpeg |
| **Database** | SQLite3 + SQLAlchemy |

---

## 📁 Repository Structure

```text
shorts-convertor/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI REST endpoints (upload, jobs, captions, render, health)
│   │   ├── core/             # App configuration, settings & DB engine
│   │   ├── models/           # SQLAlchemy DB models & Pydantic schemas
│   │   ├── services/         # FFmpeg, Whisper ASR, Clipping, & Subtitle rendering engine
│   │   ├── utils/            # File management utilities
│   │   └── main.py           # FastAPI server entry point (lifespan managed)
│   ├── .env.example          # Environment variables template
│   └── requirements.txt      # Python dependencies
├── src/
│   ├── components/           # React UI components (Hero, UploadArea, ConfigPanel, ResultsGrid, Editor)
│   ├── services/             # API client services
│   ├── App.jsx               # Main React Application
│   └── index.css             # Tailwind design tokens
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
- `GET /api/jobs/{job_id}` - Fetch job progress, status & generated clip metadata
- `PUT /api/captions/{clip_id}` - Save edited subtitle segments
- `POST /api/render/{clip_id}` - Re-render video clip with updated captions or styles
- `GET /api/projects` - List all processed video projects

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more details.
