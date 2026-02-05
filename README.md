# AI Production Pipeline Tool

An advanced render farm master server and shot management system for AI video production. This tool orchestrates the workflow between ComfyUI workers, providing a centralized interface for shot management, prompt engineering, and cinematic direction.

## 🚀 Features

- **Shot Management**: centralized database for movie shots, encompassing prompts, camera angles, and frame counts.
- **Worker Orchestration**: Manage and monitor distributed ComfyUI execution nodes.
- **Cinematic Director**: Tools for defining camera movements, lighting, and environmental presets.
- **Character Bible**: Consistent character consistency management with reference images and LoRA integration.
- **Real-time Updates**: WebSocket-based status updates for job progress and worker health.
- **Modern UI**: Dark-mode enabled, responsive frontend built with React and TailwindCSS.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, WebSocket
- **Frontend**: React, Vite, TailwindCSS, Zustand
- **Database/Storage**: File-system based (JSON/Excel) for portability, integrated with Pandas.
- **Communication**: WebSocket for real-time bidirectional communication.

## 📦 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- ComfyUI instances (for workers)

### Backend Setup

1. Navigate to the root directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file (copy from `.env.example`).

### Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

## 🚦 Usage

### Running the Master Server

```bash
# From root directory
uvicorn master.main:app --host 0.0.0.0 --port 8002 --reload
```
The API documentation will be available at `http://localhost:8002/docs`.

### Running the Frontend

```bash
# From frontend directory
npm run dev
```
The UI will be accessible at `http://localhost:5173`.

### Connecting Workers

Workers (ComfyUI nodes) should run the agent script to connect to this master server:

```bash
python worker/agent.py --master http://localhost:8002 --name "Worker-01"
```

## 📂 Project Structure

- `master/`: FastAPI backend core, routers, and services.
- `frontend/`: React-based user interface.
- `worker/`: Agent scripts for ComfyUI nodes.
- `workflows/`: ComfyUI workflow JSON definitions.
- `projects/`: Project data and asset storage.
- `ref/`: Reference images for cinematic presets.

## 📝 Roadmap

See `docs/roadmap_2026-02-04.md` for the detailed development roadmap and upcoming features.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
