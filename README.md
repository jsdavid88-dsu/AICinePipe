# AI Production Pipeline Tool

An advanced render farm master server and shot management system for AI video production. This tool orchestrates the workflow between ComfyUI workers, providing a centralized interface for shot management, prompt engineering, and cinematic direction.

## 🚀 Quick Start (3 Steps)

### Prerequisites
- **Python 3.10+** — [python.org](https://python.org) (check "Add to PATH")
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **ComfyUI** — running locally or on network (for AI rendering)

### Step 1: Clone & Setup

```bash
git clone <repo-url>
cd AIPipeline_tool
```

**Windows:**
```cmd
setup.bat
```

**Mac/Linux:**
```bash
chmod +x setup.sh && ./setup.sh
```

This will automatically:
- ✅ Create Python virtual environment
- ✅ Install all Python dependencies
- ✅ Install frontend npm packages
- ✅ Create `.env` config from template

### Step 2: Configure (optional)

Edit `.env` to set your environment:
```ini
COMFYUI_URL=http://127.0.0.1:8188       # Your ComfyUI instance
# OPENAI_API_KEY=sk-...                   # For AI script analysis
```

### Step 3: Run

**Windows:**
```cmd
start_all.bat
```

**Any OS:**
```bash
python launcher.py
```

🎉 Open **http://localhost:5173** in your browser!

---

## 🎬 Features

- **Shot Management** — Centralized database for shots, prompts, camera angles, frame counts
- **Worker Orchestration** — Manage distributed ComfyUI execution nodes
- **Cinematic Director** — Camera movements, lighting, and environmental presets
- **Character Bible** — Consistent characters with LoRA integration
- **LLM Script Analysis** — Auto-generate shot lists from screenplay text (OpenAI / Anthropic / Gemini / Ollama)
- **FFmpeg Composition** — Combine rendered shots into final video with transitions
- **Timeline Editor** — Storyboard timeline with drag & drop
- **Export** — EDL/XML for Premiere/DaVinci, project archives
- **Real-time Updates** — WebSocket-based status and progress
- **Modern UI** — Dark-mode, responsive React frontend

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, WebSocket |
| Frontend | React, Vite, TailwindCSS |
| Database | SQLite (WAL mode) |
| AI Engine | ComfyUI (FLUX, WAN, LTX-2) |
| Video | FFmpeg |
| LLM | OpenAI / Anthropic / Gemini / Ollama |

## 📂 Project Structure

```
AIPipeline_tool/
├── master/              # FastAPI backend
│   ├── main.py          # Server entry point
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── models/          # Data models
│   ├── db/              # Database layer
│   └── utils/           # Config, logging, helpers
├── worker/              # ComfyUI worker agent
│   ├── agent.py         # Worker entry point
│   ├── comfy_client.py  # ComfyUI API client
│   └── job_executor.py  # Job execution logic
├── frontend/            # React UI
│   └── src/
├── workflows/           # ComfyUI workflow JSONs
├── projects/            # Project data & assets
├── setup.bat            # Windows one-click setup
├── setup.sh             # Mac/Linux one-click setup
├── start_all.bat        # Windows launcher
├── launcher.py          # Cross-platform launcher
├── requirements.txt     # Python dependencies
└── .env.example         # Configuration template
```

## 🔧 Running Services Individually

```bash
# Backend only
python -m master.main

# Worker only (connects to master)
python worker/agent.py --master http://localhost:8002 --name "Worker-01"

# Frontend only
cd frontend && npm run dev
```

**API Documentation:** http://localhost:8002/docs

## 📝 Roadmap

See [ROADMAP.md](ROADMAP.md) for the detailed development plan.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
