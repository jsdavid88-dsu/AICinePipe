# AIPipeline_tool Code Review

**Date:** 2026-02-04
**Scope:** Full codebase review (master, worker, frontend, workflows)
**Status:** Prototype / PoC stage

---

## 1. Project Overview

ComfyUI 기반 AI 영상 제작 파이프라인 시스템.
Master-Worker 분산 아키텍처로 웹 UI에서 샷/캐릭터/시네마틱 프리셋을 관리하고 GPU 워커에 렌더링 작업을 분배한다.

```
master/       FastAPI 서버 (port 8002)
worker/       WebSocket 워커 에이전트
frontend/     React + Vite 웹 UI
workflows/    ComfyUI 워크플로우 템플릿 (JSON)
projects/     프로젝트 데이터 저장소 (JSON)
```

### Tech Stack

| Layer | Stack |
|-------|-------|
| Backend | FastAPI 0.109, Uvicorn, Pydantic 2.6, WebSockets 12.0 |
| Frontend | React 18.2, Vite 5.1, TailwindCSS 3.4, Zustand 4.5, Axios |
| Worker | asyncio, websockets, GPUtil, psutil |
| AI/ML | ComfyUI (FLUX, LTX-2, WAN-Animate, SVI 등), OpenAI API |
| Data | JSON file-based (no DB) |

---

## 2. Architecture Assessment

### Strengths

- **관심사 분리가 명확함**: models / services / routers / components 구조
- **Pydantic 모델** 기반 데이터 검증이 잘 설계됨
- **Shot 모델**이 VFX 파이프라인에 맞게 상세 (Subject, TechnicalSpecs, Environment)
- **프롬프트 엔진**이 캐릭터 + 환경 + 기술 스펙을 체계적으로 조합
- **프론트엔드 UI**가 일관된 다크 테마, glassmorphism 스타일로 통일
- **WebSocket** 기반 실시간 워커 통신 구현
- **VFX 표준 디렉토리 구조** (working/export/shots/assets) 반영
- **시네마틱 프리셋 시스템**이 풍부 (35+ 프리셋)

### Architecture Diagram

```
[Frontend (React)]
       |
       | REST API (HTTP)
       v
[Master Server (FastAPI:8002)]
       |
       |--- REST API ---> [ComfyUI Local (:8188)]
       |
       | WebSocket
       v
[Worker Agent] ---> [ComfyUI Remote (:8188)]
       |
       v
[GPU (FLUX, LTX-2, WAN-Animate...)]
```

---

## 3. Critical Issues

### 3.1 No Database Layer — In-Memory Only

- **Location:** `master/services/job_manager.py`
- **Impact:** 서버 재시작시 모든 작업 데이터 소실
- **Detail:** `self.jobs: Dict[str, Job]` 인메모리 딕셔너리만 사용. 소스 코드에 `# TODO: Persist jobs to DB` 주석 존재.
- **Recommendation:** 최소 SQLite, 이상적으로는 PostgreSQL + SQLAlchemy async 도입

### 3.2 Worker Never Reports Job Completion

- **Location:** `worker/agent.py:49-51`
- **Impact:** Master가 작업 완료 여부를 알 수 없음
- **Detail:** 워커가 ComfyUI에 작업을 큐잉한 후 `job_started`만 보내고 완료 폴링을 하지 않음. 소스 코드 주석: `# A real implementation would loop checking status via executor.`
- **Recommendation:** ComfyUI history API 폴링 루프 구현, `job_completed` / `job_failed` 메시지 추가

### 3.3 No Authentication / Authorization

- **Location:** `master/main.py:36`, `frontend/src/lib/api.js`
- **Impact:** 모든 API 엔드포인트가 무인증 오픈 상태
- **Detail:** CORS `allow_methods=["*"]`, 프론트엔드 axios에 auth 헤더/인터셉터 없음
- **Recommendation:** JWT 또는 API key 기반 인증 미들웨어 추가

### 3.4 Runtime Bug — Undefined Variable

- **Location:** `master/routers/cinematics.py:17`
- **Impact:** 해당 엔드포인트 호출시 런타임 에러
- **Detail:** `preset` 변수가 정의되지 않은 상태에서 참조됨
- **Recommendation:** 즉시 수정 필요

### 3.5 Character Model Field Mismatch

- **Location:** `master/models/character.py` vs `master/services/prompt_engine.py:42,87`
- **Impact:** 프롬프트 엔진에서 AttributeError 발생 가능
- **Detail:** `prompt_engine.py`에서 `use_lora`, `default_clothing` 필드를 사용하지만 Character 모델에 해당 필드가 정의되어 있지 않음
- **Recommendation:** Character 모델에 누락 필드 추가

---

## 4. High Priority Issues

### 4.1 No Structured Logging

- **Location:** 전체 코드베이스
- **Impact:** 프로덕션 디버깅 불가, 로그 로테이션 없음
- **Detail:** 모든 로깅이 `print()` 문으로 처리됨. `master/main.py`에서 `server.log` 파일에 기록하지만 로테이션 없음
- **Recommendation:** Python `logging` 모듈 도입, 로그 레벨/로테이션/포맷 설정

### 4.2 Silent Error Swallowing

- **Location:** `worker/agent.py:79`, `worker/comfy_client.py:24`, `worker/gpu_reporter.py:26`
- **Impact:** 장애 원인 파악 불가
- **Detail:**
  ```python
  except Exception:
      pass  # 하트비트 에러 무시
  except:
      return False  # 모든 예외 삼킴
  ```
- **Recommendation:** 최소한 에러 로깅 추가, 구체적 예외 타입 사용

### 4.3 Hardcoded URLs

- **Location:** `worker/agent.py:25`, `frontend/src/lib/api.js:4`, `frontend/src/components/CharacterCard.jsx:8`
- **Impact:** 배포 환경 변경시 코드 수정 필요
- **Detail:**
  - Worker: `http://127.0.0.1:8188` (ComfyUI), `ws://localhost:8002` (Master)
  - Frontend: `http://127.0.0.1:8002` (API), `http://localhost:8000` (CharacterCard — 다른 포트)
- **Recommendation:** `.env` 파일 + 환경변수로 분리

### 4.4 Fake GPU Data Fallback

- **Location:** `worker/gpu_reporter.py:26-37`
- **Impact:** Master가 실제/가짜 GPU를 구분할 수 없어 잘못된 스케줄링
- **Detail:** GPUtil 실패시 가짜 RTX 4090 데이터를 생성하여 반환
- **Recommendation:** GPU 감지 실패시 명시적 에러 상태 반환, `is_simulated` 플래그 추가

### 4.5 Resource Matching Not Implemented

- **Location:** `master/services/job_manager.py`
- **Impact:** VRAM 부족한 워커에 작업 할당 가능
- **Detail:** `JobPriority` enum과 VRAM 요구사항이 모델에 정의되어 있지만 실제 매칭 로직 미구현. 단순 FIFO로 첫 번째 idle 워커에 할당
- **Recommendation:** VRAM 비교 로직 구현, 우선순위 큐 도입

### 4.6 Prompt Injection to All Text Nodes

- **Location:** `worker/job_executor.py:56-62`
- **Impact:** 긍정/부정 프롬프트 구분 불가
- **Detail:** 모든 `CLIPTextEncode` 노드에 동일한 텍스트를 주입. 소스 코드 주석: `# 긍정 프롬프트 (Node Title이나 ID로 구분해야 완벽하지만...)`
- **Recommendation:** 노드 ID 기반 명시적 매핑 또는 워크플로우 메타데이터에 역할 태그 추가

### 4.7 ID Collision Risk

- **Location:** `frontend/src/components/ShotTable.jsx:96`, `CharacterModal.jsx:59`
- **Impact:** 동시 접속 클라이언트에서 ID 충돌 가능
- **Detail:**
  ```javascript
  const id = `SHT-${Date.now().toString().slice(-5)}`
  const id = `CHR-${Date.now().toString().slice(-6)}`
  ```
- **Recommendation:** UUID 사용 또는 서버 사이드 ID 생성

---

## 5. Medium Priority Issues

### 5.1 Data Persistence

| Issue | Location | Detail |
|-------|----------|--------|
| JSON 파일 기반 — atomic write 없음 | `data_manager.py` | 크래시시 데이터 손상 위험 |
| 스키마 마이그레이션 전략 없음 | `data_manager.py` | 모델 변경시 기존 데이터 호환 불가 |
| 백업 메커니즘 없음 | `data_manager.py` | 데이터 복구 불가 |

### 5.2 Frontend

| Issue | Location | Detail |
|-------|----------|--------|
| React Error Boundary 없음 | 전체 | API 에러로 전체 UI 크래시 가능 |
| Zustand 설치됐지만 미사용 | `package.json` | 불필요한 의존성 |
| TypeScript 타입 패키지 설치됐지만 JSX 사용 | `package.json` | 타입 안전성 미적용 |
| PropTypes 검증 없음 | 컴포넌트 전체 | 런타임 prop 에러 감지 불가 |
| `window.alert()` / `window.confirm()` 사용 | `App.jsx:21`, `CharacterBible.jsx:44` | 커스텀 토스트/다이얼로그로 교체 필요 |
| ShotTable 중복 컬럼 헤더 | `ShotTable.jsx:305-308` | Subjects, Env 컬럼 중복 정의 |

### 5.3 Worker

| Issue | Location | Detail |
|-------|----------|--------|
| WebSocket 재연결시 상태 복구 없음 | `agent.py` | 연결 끊김 후 진행중 작업 상태 불명 |
| 하트비트 타임아웃 없음 | `agent.py:32` | `await websocket.recv()` 무한 대기 |
| 워크플로우 템플릿 스키마 검증 없음 | `job_executor.py:14-20` | 잘못된 JSON이 큐 시점에서야 실패 |

### 5.4 API

| Issue | Location | Detail |
|-------|----------|--------|
| `shots.py:92` 미정의 `subjects` 참조 | `routers/shots.py` | Export 기능 에러 |
| 비일관적 HTTP 상태 코드 | routers 전체 | 에러 응답 표준화 필요 |
| 파일 업로드 MIME 타입 검증 불완전 | routers 일부 | 임의 파일 업로드 가능 |

---

## 6. Low Priority / Observations

- 한국어/영어 주석 혼재 — 일관성 필요
- Docstring 없음 — 함수/클래스 문서화 부족
- 테스트 코드 전무 — unit/integration test 없음
- WorkerDashboard 5초 폴링 — 대규모 팜에서 비효율적 (WebSocket 이벤트 방식 권장)
- Shot 모델에 `character_ids` (legacy)와 `subjects` (new) 이중 참조 — 동기화 문제
- `Activity` 버튼 핸들러 미구현 (`App.jsx:188`)
- `CinematicOptions` "Create New" 버튼 onClick 없음

---

## 7. Security Assessment

| Category | Status | Notes |
|----------|--------|-------|
| Authentication | Not Implemented | API 완전 오픈 |
| Authorization | Not Implemented | 역할 기반 접근 제어 없음 |
| CORS | Overly Permissive | `allow_methods=["*"]` |
| Input Validation | Partial | Pydantic 모델은 있으나 프론트엔드 미검증 |
| File Upload | Weak | MIME 타입 검증 불완전 |
| XSS | Low Risk | React 기본 이스케이핑에 의존 |
| CSRF | Not Implemented | POST 요청 보호 없음 |

---

## 8. Production Readiness

| Aspect | Status | Detail |
|--------|--------|--------|
| Database | Not Ready | 인메모리, 재시작시 소실 |
| Error Handling | Weak | broad catch, print 기반 |
| Logging | Basic | 파일 기반, 로테이션 없음 |
| Resource Management | Incomplete | VRAM 매칭 미구현 |
| Security | Weak | 인증 없음, CORS 개방 |
| Job Lifecycle | Incomplete | 완료 감지 미구현 |
| Testing | None | 테스트 코드 없음 |
| Scalability | Limited | 싱글톤, 인메모리 구조 |
| Monitoring | Basic | GPU 리포팅만, APM 없음 |
| Documentation | Fair | 아키텍처 문서 있음, API 문서 없음 |

---

## 9. Recommended Action Plan

### Phase 1 — Immediate Fixes (버그 수정)

1. `master/routers/cinematics.py:17` 미정의 변수 수정
2. `master/models/character.py`에 `use_lora`, `default_clothing` 필드 추가
3. `master/routers/shots.py:92` export 함수 수정
4. `frontend/src/components/ShotTable.jsx:305-308` 중복 컬럼 제거

### Phase 2 — Stability (안정성)

5. `print()` → Python `logging` 모듈 전환 (전체)
6. `except Exception: pass` → 구체적 예외 처리 + 에러 로깅
7. 환경변수 기반 URL 설정 분리 (`.env`)
8. Worker 작업 완료 폴링 루프 구현
9. GPU 감지 실패시 가짜 데이터 대신 에러 상태 반환

### Phase 3 — Data Integrity (데이터)

10. SQLite 또는 PostgreSQL DB 레이어 도입
11. JSON 파일 atomic write 적용 (임시 전환 기간)
12. 스키마 마이그레이션 전략 수립 (Alembic 등)
13. ID 생성을 UUID 기반으로 변경

### Phase 4 — Security (보안)

14. JWT 또는 API key 인증 미들웨어
15. CORS 정책 제한 (허용 origin 명시)
16. 파일 업로드 MIME 타입 / 크기 검증 강화
17. 입력값 sanitization 추가

### Phase 5 — Quality (품질)

18. React Error Boundary 추가
19. 미사용 의존성 제거 (Zustand 또는 활용)
20. 핵심 서비스 unit test 작성
21. API 통합 테스트 작성
22. 워크플로우 템플릿 스키마 검증

---

## 10. File Reference

### Master Server

| File | Lines | Purpose |
|------|-------|---------|
| `master/main.py` | 66 | FastAPI 앱 진입점 |
| `master/dependencies.py` | — | 싱글톤 의존성 주입 |
| `master/models/job.py` | 48 | 작업 모델 |
| `master/models/worker.py` | 38 | 워커 노드 모델 |
| `master/models/shot.py` | 92 | 샷 모델 (V2) |
| `master/models/character.py` | 17 | 캐릭터 모델 |
| `master/models/cinematic.py` | 31 | 시네마틱 프리셋 모델 |
| `master/services/job_manager.py` | 62 | 작업 큐 관리 |
| `master/services/worker_manager.py` | 99 | 워커 레지스트리 |
| `master/services/data_manager.py` | 166 | JSON 영속화 |
| `master/services/local_executor.py` | 69 | ComfyUI 직접 실행 |
| `master/services/prompt_engine.py` | 114 | 프롬프트 생성 엔진 |
| `master/services/workflow_analyzer.py` | 46 | 워크플로우 추천 |
| `master/services/filesystem_service.py` | 101 | VFX 디렉토리 구조 |
| `master/routers/jobs.py` | 108 | 작업 API |
| `master/routers/workers.py` | 36 | 워커 API |
| `master/routers/shots.py` | 236 | 샷 API |
| `master/routers/projects.py` | 165 | 프로젝트 API |
| `master/routers/characters.py` | 89 | 캐릭터 API |
| `master/routers/cinematics.py` | 26 | 시네마틱 API (버그 있음) |
| `master/routers/websocket.py` | 37 | WebSocket 엔드포인트 |

### Worker

| File | Lines | Purpose |
|------|-------|---------|
| `worker/agent.py` | 91 | 메인 워커 프로세스 |
| `worker/comfy_client.py` | ~30 | ComfyUI HTTP 클라이언트 |
| `worker/gpu_reporter.py` | ~40 | GPU/시스템 모니터링 |
| `worker/job_executor.py` | ~80 | 워크플로우 실행 |

### Frontend

| File | Lines | Purpose |
|------|-------|---------|
| `frontend/src/App.jsx` | 464 | 메인 앱 컴포넌트 |
| `frontend/src/lib/api.js` | ~80 | API 클라이언트 |
| `frontend/src/components/ShotTable.jsx` | 624 | 샷 관리 테이블 |
| `frontend/src/components/ProjectSelection.jsx` | 228 | 프로젝트 선택 화면 |
| `frontend/src/components/CharacterBible.jsx` | 125 | 캐릭터 목록 |
| `frontend/src/components/CharacterModal.jsx` | 215 | 캐릭터 편집 모달 |
| `frontend/src/components/CinematicOptions.jsx` | 139 | 시네마틱 프리셋 |
| `frontend/src/components/WorkerDashboard.jsx` | 161 | GPU 워커 대시보드 |
| `frontend/src/components/Timeline.jsx` | 153 | 타임라인 편집 |
| `frontend/src/components/SubjectSelector.jsx` | 155 | 캐릭터 캐스팅 모달 |
| `frontend/src/components/ExcelImportModal.jsx` | 152 | 엑셀 임포트 |

---

*Review conducted with automated codebase analysis. Manual testing not performed.*
