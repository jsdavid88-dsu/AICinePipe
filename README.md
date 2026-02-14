# AICinePipe — AI Production Pipeline Tool

> 🚧 **Work In Progress (WIP)** — 개발 진행 중

AI 영상 제작을 위한 렌더팜 마스터 서버 및 샷 관리 시스템.
ComfyUI 워커를 오케스트레이션하여 샷 관리, 프롬프트 엔지니어링, 영상 합성을 통합 제공합니다.

An advanced render farm master server and shot management system for AI video production.
Orchestrates ComfyUI workers with centralized shot management, prompt engineering, and cinematic direction.

**Developed by** 동서대학교 가상융합기술연구소 & (주)레드캣갱  
**Developed by** Dongseo University Virtual Convergence Technology Research Institute & Red Cat Gang Co., Ltd.

---

## 🚀 Quick Start / 빠른 시작

### Prerequisites / 사전 요구사항
- **Python 3.10+** — [python.org](https://python.org) (설치 시 "Add to PATH" 체크)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **ComfyUI** — 로컬 또는 네트워크에서 실행 중 (AI 렌더링용)

### Step 1: Clone & Setup / 클론 & 설치

```bash
git clone https://github.com/jsdavid88-dsu/AICinePipe.git
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

자동으로 다음을 수행합니다 / This will automatically:
- ✅ Python 가상환경 생성 / Create virtual environment
- ✅ Python 패키지 설치 / Install Python dependencies
- ✅ 프론트엔드 npm 패키지 설치 / Install frontend packages
- ✅ `.env` 설정 파일 생성 / Create config from template

### Step 2: Configure / 설정 (선택사항)

`.env` 파일을 편집하세요 / Edit `.env`:
```ini
COMFYUI_URL=http://127.0.0.1:8188       # ComfyUI 인스턴스 주소
# OPENAI_API_KEY=sk-...                   # AI 스크립트 분석용 (선택)
```

### Step 3: Run / 실행

**Windows:**
```cmd
start_all.bat
```

**Any OS / 모든 OS:**
```bash
python launcher.py
```

🎉 브라우저에서 **http://localhost:5173** 접속!

---

## 🎬 Features / 기능

| Feature / 기능 | Description / 설명 |
|---|---|
| **Shot Management / 샷 관리** | 샷, 프롬프트, 카메라 앵글, 프레임 수 통합 관리 |
| **Worker Orchestration / 워커 오케스트레이션** | 분산 ComfyUI 노드 관리 및 잡 큐잉 |
| **Cinematic Director / 시네마틱 디렉터** | 카메라 움직임, 조명, 환경 프리셋 |
| **Character Bible / 캐릭터 바이블** | 캐릭터 일관성 관리 + LoRA 연동 |
| **LLM Script Analysis / LLM 스크립트 분석** | 대본에서 샷 리스트 자동 생성 (OpenAI / Anthropic / Gemini / Ollama) |
| **FFmpeg Composition / 영상 합성** | 렌더된 샷을 트랜지션과 함께 합성 |
| **Timeline Editor / 타임라인 편집기** | 드래그 & 드롭 스토리보드 타임라인 |
| **Model Manager / 모델 관리** | AI 모델 목록 조회, 설치 상태 확인 (🚧 WIP) |
| **Export / 내보내기** | EDL/XML (Premiere/DaVinci), 프로젝트 아카이브 |
| **Real-time Updates / 실시간 업데이트** | WebSocket 기반 진행 상태 모니터링 |

## 🛠️ Tech Stack / 기술 스택

| Layer / 레이어 | Technology / 기술 |
|---|---|
| Backend | Python, FastAPI, WebSocket |
| Frontend | React, Vite, TailwindCSS, Zustand |
| Database | SQLite (WAL mode) |
| AI Engine | ComfyUI (FLUX, WAN 2.1/2.2, LTX-2) |
| Video | FFmpeg |
| LLM | OpenAI / Anthropic / Gemini / Ollama |

## 📂 Project Structure / 프로젝트 구조

```
AICinePipe/
├── core/                # 공유 코어 / Shared core modules
│   ├── comfy_client.py  # 통합 ComfyUI 클라이언트 / Unified ComfyUI client
│   ├── workflow_utils.py# 워크플로우 인젝션 / Workflow injection utils
│   └── models_db.json   # AI 모델 DB / Model database (30+ models)
├── master/              # 백엔드 서버 / FastAPI backend
│   ├── main.py
│   ├── routers/         # API 엔드포인트 / API endpoints
│   ├── services/        # 비즈니스 로직 / Business logic
│   ├── models/          # 데이터 모델 / Data models
│   └── utils/           # 설정/로깅 / Config, logging
├── worker/              # ComfyUI 워커 에이전트 / Worker agent
├── frontend/            # React UI
├── workflows/           # ComfyUI 워크플로우 JSON
├── projects/            # 프로젝트 데이터 / Project data & assets
├── setup.bat / setup.sh # 원클릭 설치 / One-click setup
├── launcher.py          # 통합 런처 / Unified launcher
└── .env.example         # 설정 템플릿 / Config template
```

## 🔧 Running Services / 개별 서비스 실행

```bash
# 백엔드만 / Backend only
python -m master.main

# 워커만 / Worker only (Master 서버에 연결)
python worker/agent.py --master http://localhost:8002 --name "Worker-01"

# 프론트엔드만 / Frontend only
cd frontend && npm run dev
```

**API 문서 / API Documentation:** http://localhost:8002/docs

## 🚧 Current Status / 현재 상태

> **WIP** — 핵심 기능 구현 완료, 통합 테스트 및 UI 고도화 진행 중

| Phase | Status / 상태 |
|---|---|
| Core Backend & Frontend | ✅ Complete |
| Shot Management & Character Bible | ✅ Complete |
| Cinematic Presets | ✅ Complete |
| Distributed Render Farm | ✅ Complete |
| LLM Multi-Provider | ✅ Complete |
| FFmpeg Video Composition | ✅ Complete |
| Core Unification (core/) | ✅ Complete |
| Model Management API | 🚧 WIP |
| DCC Bridge (Maya/Nuke) | 📋 Planned |
| Full Installer (ComfyUI bundled) | 📋 Planned |

## 📝 Roadmap / 로드맵

상세 개발 계획은 [ROADMAP.md](ROADMAP.md)를 참고하세요.  
See [ROADMAP.md](ROADMAP.md) for the detailed development plan.

## 🤝 Contributing / 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
