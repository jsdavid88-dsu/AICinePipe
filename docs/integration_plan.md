# AIPipeline 기능 확장 계획서
> 프로덕션급 AI 영상 파이프라인으로 확장

---

## Phase 0: 버그 수정 + DB 기반 (Week 1) ✅ COMPLETED

| # | 작업 | 파일 | 상태 |
|---|------|------|------|
| 0-1 | `cinematics.py` 런타임 에러 | `master/routers/cinematics.py` | ✅ 정상 확인 |
| 0-2 | Character trigger_words 파싱 | `master/services/prompt_engine.py` | ✅ 수정 |
| 0-3 | ShotTable 중복 컬럼 | `frontend/src/components/ShotTable.jsx` | ✅ 정상 확인 |
| 0-4 | shots.py export 버그 | `master/routers/shots.py` | ✅ 수정 |
| 0-5 | 환경변수 분리 (.env) | `master/utils/config.py` | ✅ |
| 0-6 | 로깅 구조화 (loguru) | 전체 `print()` → loguru | ✅ |
| 0-7 | **JSON → SQLite 전환** | `master/db/database.py` 신규 | ✅ |
| 0-8 | Job 영속성 (메모리→DB) | `master/services/job_manager.py` | ✅ |
| 0-9 | Worker 완료 보고 구현 | `worker/agent.py` | ✅ |

---

## Phase 1: 렌더팜 강화 (Week 2-3)

### 구현 항목

| # | 작업 | 구현 위치 |
|---|------|----------|
| 1-1 | 워크플로우 JSON 파싱 (노드→실행계획) | `master/services/workflow_parser.py` 신규 |
| 1-2 | 파라미터 동적 치환 (`{prompt}`, `{seed}` 등) | `master/services/parameter_patcher.py` 신규 |
| 1-3 | 백엔드 매니저 (멀티 ComfyUI 노드 등록) | `master/services/backend_manager.py` 신규 |
| 1-4 | ComfyUI 클라이언트 (큐, 진행률, 취소) | `worker/comfy_client.py` 개선 |
| 1-5 | 스케줄러 (능력+부하 기반 노드 선택) | `master/services/scheduler.py` 신규 |
| 1-6 | 헬스 모니터 (주기적 폴링) | `master/services/health_monitor.py` 신규 |
| 1-7 | GPU 메트릭 수집 (VRAM/온도/큐) | `worker/gpu_reporter.py` 개선 |
| 1-8 | 단계별 진행률 (KSampler step 추적) | `master/routers/websocket.py` 개선 |
| 1-9 | 큐 관리 API (우선순위, 취소) | `master/routers/jobs.py` 개선 |
| 1-10 | 프론트 워커 대시보드 개선 | `frontend/src/components/WorkerDashboard.jsx` 개선 |

### Orchestrator 아키텍처

```
사용자 → Job 제출 (워크플로우 JSON + 파라미터)
  ↓
GraphExecutor: 토폴로지 정렬 → 스트림 분리 (독립 서브그래프)
  ↓
ParameterPatcher: {variable} → 실제값 치환
  ↓
Scheduler: 능력 매칭 + 부하 밸런싱 → 최적 백엔드 선택
  ↓
ComfyUIClient: 프롬프트 큐 제출
  ↓
WebSocket: 실시간 진행률 모니터
  ↓
노드 완료 콜백 → 중간 출력물 전송
  ↓
전체 완료 → Job COMPLETED → 출력물 저장
  ↓
(실패시) 페일오버 → 다른 백엔드로 재제출
```

---

## Phase 2: CPE 룰 엔진 (Week 4-5)

### 구현 항목

| # | 작업 | 구현 위치 |
|---|------|----------|
| 2-1 | 공통 Enum 정의 (ShotSize, Mood, Composition...) | `master/models/cinema_enums.py` 신규 |
| 2-2 | 카메라 DB (ARRI, RED, Sony, Panavision, 150+모델) | `master/models/camera_db.py` 신규 |
| 2-3 | 렌즈 DB (마운트 호환성, 초점거리) | `master/models/lens_db.py` 신규 |
| 2-4 | 필름스톡 DB (50+ 옵션, 시대별) | `master/models/filmstock_db.py` 신규 |
| 2-5 | 조명 DB (광원, 시대 제약) | `master/models/lighting_db.py` 신규 |
| 2-6 | 검증 룰 엔진 (56+ 룰) | `master/services/rule_engine.py` 신규 |
| 2-7 | 50+ 영화 프리셋 | `master/data/presets/live_action.json` |
| 2-8 | 43+ 애니메이션 프리셋 | `master/data/presets/animation.json` |
| 2-9 | 모델별 프롬프트 포맷팅 (FLUX, Wan, SD, MJ) | `master/services/prompt_engine.py` 개선 |
| 2-10 | 애니메이션 스키마 (도메인, 렌더링, 모션) | `master/models/animation_schema.py` 신규 |
| 2-11 | CPE API 엔드포인트 (/validate, /generate-prompt) | `master/routers/cpe.py` 신규 |
| 2-12 | 프론트 CPE 설정 UI | `frontend/src/components/CPESettings.jsx` 신규 |

### 룰 엔진 패턴

```python
# Rule 정의 패턴
class Rule:
    severity: RuleSeverity  # HARD, SOFT, INFO
    message: str
    check: Callable[[Config], bool]  # True = 위반

# 룰 카테고리:
# - 필름스톡 룰: 디지털→필름스톡 금지, 65mm→65mm카메라 필수
# - 렌즈 룰: Panavision 카메라→Panavision 렌즈만, 센서→초점거리 매칭
# - 무브먼트 룰: 무거운 카메라→짐벌/핸드헬드 금지
# - 조명 룰: 1970년 이전→LED/HMI 금지
# - 조합 룰: 느와르 프리셋+밝은 무드 = HARD 위반
```

---

## Phase 3: LLM 통합 (Week 5-6)

| # | 작업 | 구현 위치 |
|---|------|----------|
| 3-1 | LLM 프로바이더 추상화 | `master/services/llm_service.py` 신규 |
| 3-2 | OpenAI / Anthropic / Google / Ollama 지원 | 위 파일에 통합 |
| 3-3 | 시나리오 자동 분석 (캐릭터/샷/배경 추출) | `master/services/scenario_analyzer.py` 신규 |
| 3-4 | 프롬프트 향상 (LLM으로 프롬프트 리파인) | `master/services/prompt_enhancer.py` 신규 |
| 3-5 | API 키 관리 (암호화 저장) | `master/services/credential_store.py` 신규 |
| 3-6 | 로컬 LLM (Ollama) 지원 | 위 서비스에 통합 |

---

## Phase 4: 샷 관리 고도화 (Week 6-8)

| # | 작업 | 구현 위치 |
|---|------|----------|
| 4-1 | Airtable급 인라인 편집 | `frontend/src/components/ShotTable.jsx` 개선 |
| 4-2 | 드래그 정렬, 멀티셀 선택 | ShotTable에 통합 |
| 4-3 | 필터/정렬/그룹핑 | `frontend/src/lib/filtering.js` 신규 |
| 4-4 | 엑셀 Export/Import 수정 | `frontend/src/components/ExcelImportModal.jsx` 수정 |
| 4-5 | 상태 워크플로우 (칸반) | `frontend/src/components/ShotKanban.jsx` 신규 |
| 4-6 | 썸네일 컬럼 | ShotTable에 통합 |
| 4-7 | Undo/Redo | `frontend/src/store/undoStore.js` 신규 |

### 태스크 상태 패턴

```
상태 워크플로우:
pending → wip → review → approved / retake → final

역할별 필터링:
- Manager/Supervisor: 모든 상태 접근
- Artist: artist_allowed 상태만
- Client: client_allowed 상태만

칸반 보드:
- 열 = 상태 (pending, wip, review, approved...)
- 카드 = 샷
- 드래그&드롭 = 상태 변경
```

---

## Phase 5: 폴더 구조 자동화 (Week 8-9)

| # | 작업 | 구현 위치 |
|---|------|----------|
| 5-1 | 네이밍 컨벤션 엔진 강화 | `master/utils/naming_convention.py` 개선 |
| 5-2 | 컨펌 → 폴더 트리 생성 | `master/services/filesystem_service.py` 개선 |
| 5-3 | 버전 관리 디렉토리 | 위 파일에 통합 |
| 5-4 | 메타데이터 JSON 자동 배치 | 위 파일에 통합 |

---

## Phase 6: 이미지 생성 강화 (Week 9-12)

| # | 작업 | 구현 위치 |
|---|------|----------|
| 6-1 | t2i 배치 생성 | `master/services/batch_generator.py` 신규 |
| 6-2 | i2i 리파인 루프 | `workflows/image_to_image/` 신규 |
| 6-3 | 인페인팅/아웃페인팅 | `workflows/inpaint/` 신규 |
| 6-4 | 컨트롤넷 지원 | `workflows/controlnet/` 신규 |
| 6-5 | 이미지 버전 관리 | `master/services/version_manager.py` 신규 |
| 6-6 | Before/After 비교 뷰어 | `frontend/src/components/ImageCompare.jsx` 신규 |
| 6-7 | 승인/반려 워크플로우 | 상태 워크플로우에 통합 |

---

## Phase 7: 스토리보드 캔버스 (Week 12-14)

| # | 작업 | 구현 위치 |
|---|------|----------|
| 7-1 | 무한 캔버스 UI (`@xyflow/react`) | `frontend/src/components/StoryboardCanvas.jsx` 신규 |
| 7-2 | 자유 배치 패널 | 위 파일에 통합 |
| 7-3 | 패널별 워크플로우/파라미터 | 위 파일에 통합 |
| 7-4 | 이미지 히스토리/네비게이션 | `frontend/src/components/ImageHistory.jsx` 신규 |
| 7-5 | 별점 레이팅 | 패널 컴포넌트에 통합 |
| 7-6 | 마크다운 노트 | 패널 컴포넌트에 통합 |
| 7-7 | 인쇄용 PDF | `frontend/src/lib/pdfExport.js` 신규 |

---

## Phase 8: 비디오 생성 (Week 14-16)

| # | 작업 | 구현 위치 |
|---|------|----------|
| 8-1 | i2v 워크플로우 (WAN 2.2) | `workflows/image_to_video/wan22.json` |
| 8-2 | CogVideoX 지원 | `workflows/image_to_video/cogvideox.json` |
| 8-3 | HunyuanVideo 지원 | `workflows/image_to_video/hunyuan.json` |
| 8-4 | 비디오 인라인 재생 | `frontend/src/components/VideoPlayer.jsx` 신규 |
| 8-5 | 비디오 버전 관리 | version_manager에 통합 |

---

## Phase 9: 타임라인/편집 (Week 16-18)

| # | 작업 | 구현 위치 |
|---|------|----------|
| 9-1 | 프록시 영상 생성 | `master/services/proxy_generator.py` 신규 |
| 9-2 | 드래그 리사이즈/리오더 | `frontend/src/components/Timeline.jsx` 개선 |
| 9-3 | 플레이백 엔진 | 위 파일에 통합 |
| 9-4 | 마커/코멘트 | 타임라인에 통합 |
| 9-5 | EDL/XML Export | `master/routers/projects.py` 개선 |

---

## Phase 10: 리뷰 시스템 (Week 18-19)

| # | 작업 | 구현 위치 |
|---|------|----------|
| 10-1 | 플레이리스트 리뷰 | `frontend/src/components/ReviewPlaylist.jsx` 신규 |
| 10-2 | 코멘트/피드백 (마크다운+멘션) | `frontend/src/components/CommentThread.jsx` 신규 |
| 10-3 | 버전 히스토리 비교 | `frontend/src/components/VersionCompare.jsx` 신규 |
| 10-4 | 승인/반려 워크플로우 | 상태 시스템에 통합 |

### 리뷰 패턴

```
리뷰 세션:
1. 플레이리스트 생성 (샷 선택)
2. 순차 재생 + 코멘트
3. 각 샷에 상태 부여 (approved/retake)
4. 코멘트에 타임코드 참조 가능

실시간 협업 (WebSocket):
- preview-room:join → 세션 참가
- preview-room:room-updated → 재생 동기화
- preview-room:panzoom-changed → 뷰 동기화
```

---

## Phase 11: 대시보드 (Week 19-20)

| # | 작업 | 구현 위치 |
|---|------|----------|
| 11-1 | 프로덕션 진행률 차트 | `frontend/src/components/Dashboard.jsx` 신규 |
| 11-2 | 샷별/상태별 통계 | 위 파일에 통합 |
| 11-3 | 렌더팜 현황 | WorkerDashboard 확장 |
| 11-4 | 리포트 (일일/주간) | `master/services/report_generator.py` 신규 |

---

## Phase 12-13: DCC 연동 + 후처리 (Week 20-26)

자체 설계. Blender 브릿지, 프레임 보간, 업스케일, EDL 출력.

---

## Phase 14: 인프라 (전 구간 병행)

| # | 작업 | 비고 |
|---|------|------|
| 14-1 | SQLite (Phase 0에서 완료) | ✅ |
| 14-2 | PostgreSQL 전환 (필요시) | Month 4+ |
| 14-3 | JWT 인증 | Month 2+ |
| 14-4 | 역할별 권한 | Month 3+ |
| 14-5 | 백업 시스템 | Month 4+ |
| 14-6 | Docker 컨테이너화 | Month 5+ |

---

## 파일 구조 (최종 목표)

```
AIPipeline_tool/
├── master/
│   ├── main.py
│   ├── models/
│   │   ├── shot.py                 # 기존 (개선)
│   │   ├── job.py                  # 기존 (개선)
│   │   ├── worker.py               # 기존 (개선)
│   │   ├── character.py            # 기존 (수정)
│   │   ├── cinematic.py            # 기존
│   │   ├── cinema_enums.py         # 신규 (Phase 2)
│   │   ├── camera_db.py            # 신규 (Phase 2)
│   │   ├── lens_db.py              # 신규 (Phase 2)
│   │   ├── filmstock_db.py         # 신규 (Phase 2)
│   │   ├── lighting_db.py          # 신규 (Phase 2)
│   │   └── animation_schema.py     # 신규 (Phase 2)
│   ├── routers/
│   │   ├── shots.py                # 기존 (수정)
│   │   ├── jobs.py                 # 기존 (개선)
│   │   ├── workers.py              # 기존
│   │   ├── projects.py             # 기존 (개선)
│   │   ├── characters.py           # 기존
│   │   ├── cinematics.py           # 기존
│   │   ├── websocket.py            # 기존 (개선)
│   │   ├── cpe.py                  # 신규 (Phase 2)
│   │   ├── llm.py                  # 신규 (Phase 3)
│   │   └── review.py               # 신규 (Phase 10)
│   ├── services/
│   │   ├── data_manager.py         # 기존 → SQLite (Phase 0)
│   │   ├── filesystem_service.py   # 기존 (개선)
│   │   ├── job_manager.py          # 기존 (DB 전환)
│   │   ├── worker_manager.py       # 기존
│   │   ├── prompt_engine.py        # 기존 (대폭 개선 Phase 2)
│   │   ├── workflow_analyzer.py    # 기존
│   │   ├── preset_service.py       # 기존
│   │   ├── workflow_parser.py      # 신규 (Phase 1)
│   │   ├── parameter_patcher.py    # 신규 (Phase 1)
│   │   ├── backend_manager.py      # 신규 (Phase 1)
│   │   ├── scheduler.py            # 신규 (Phase 1)
│   │   ├── health_monitor.py       # 신규 (Phase 1)
│   │   ├── rule_engine.py          # 신규 (Phase 2)
│   │   ├── llm_service.py          # 신규 (Phase 3)
│   │   ├── scenario_analyzer.py    # 신규 (Phase 3)
│   │   ├── prompt_enhancer.py      # 신규 (Phase 3)
│   │   ├── credential_store.py     # 신규 (Phase 3)
│   │   ├── batch_generator.py      # 신규 (Phase 6)
│   │   ├── version_manager.py      # 신규 (Phase 6)
│   │   └── report_generator.py     # 신규 (Phase 11)
│   ├── data/
│   │   └── presets/
│   │       ├── live_action.json    # 신규 (Phase 2) 50+ 영화 프리셋
│   │       └── animation.json      # 신규 (Phase 2) 43+ 애니 프리셋
│   └── db/
│       ├── database.py             # 신규 (Phase 0) SQLite 연결
│       └── migrations/             # 스키마 마이그레이션
│
├── worker/                          # 기존 (개선)
│
├── frontend/src/
│   ├── components/
│   │   ├── ShotTable.jsx           # 기존 (대폭 개선 Phase 4)
│   │   ├── ShotKanban.jsx          # 신규 (Phase 4)
│   │   ├── CPESettings.jsx         # 신규 (Phase 2)
│   │   ├── StoryboardCanvas.jsx    # 신규 (Phase 7)
│   │   ├── ImageHistory.jsx        # 신규 (Phase 7)
│   │   ├── ImageCompare.jsx        # 신규 (Phase 6)
│   │   ├── VideoPlayer.jsx         # 신규 (Phase 8)
│   │   ├── ReviewPlaylist.jsx      # 신규 (Phase 10)
│   │   ├── CommentThread.jsx       # 신규 (Phase 10)
│   │   ├── VersionCompare.jsx      # 신규 (Phase 10)
│   │   ├── Dashboard.jsx           # 신규 (Phase 11)
│   │   └── WorkerDashboard.jsx     # 기존 (개선)
│   ├── lib/
│   │   ├── api.js                  # 기존 (확장)
│   │   ├── filtering.js            # 신규 (Phase 4)
│   │   ├── sorting.js              # 신규 (Phase 4)
│   │   └── pdfExport.js            # 신규 (Phase 7)
│   └── store/
│       └── undoStore.js            # 신규 (Phase 4)
│
├── workflows/
│   ├── text_to_image/flux_basic.json  # 기존
│   ├── image_to_image/             # 신규 (Phase 6)
│   ├── image_to_video/             # 신규 (Phase 8)
│   ├── inpaint/                    # 신규 (Phase 6)
│   └── controlnet/                 # 신규 (Phase 6)
│
└── docs/
    └── integration_plan.md         # 이 문서
```
