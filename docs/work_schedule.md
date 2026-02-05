# AIPipeline_tool 작업 스케쥴

**생성일:** 2026-02-04  
**기반 문서:** [code_review_2026-02-04.md](./code_review_2026-02-04.md)  
**목표:** Code Review에서 식별된 이슈들을 체계적으로 해결하기 위한 작업 일정

---

## 📊 이슈 요약

| 우선순위 | 개수 | 영향도 |
|----------|------|--------|
| 🔴 Critical | 5개 | 런타임 에러, 데이터 손실, 보안 취약점 |
| 🟠 High | 7개 | 디버깅 불가, 잘못된 스케줄링, 설정 하드코딩 |
| 🟡 Medium | 12개+ | 사용자 경험, 코드 품질 |
| 🟢 Low | 7개+ | 문서화, 일관성 |

---

## 🗓️ Phase 1: Immediate Fixes (즉시 수정)

> **예상 소요:** 1일  
> **목표:** 런타임 에러 및 버그 수정

### 작업 목록

| # | 작업 | 파일 | 상태 | 담당 |
|---|------|------|------|------|
| 1.1 | `preset` 미정의 변수 수정 | `master/routers/cinematics.py:17` | ⬜ | - |
| 1.2 | Character 모델에 `use_lora`, `default_clothing` 필드 추가 | `master/models/character.py` | ⬜ | - |
| 1.3 | `subjects` 미정의 변수 수정 (export 함수) | `master/routers/shots.py:92` | ⬜ | - |
| 1.4 | 중복 컬럼 헤더 제거 | `frontend/src/components/ShotTable.jsx:305-308` | ⬜ | - |

### 검증 방법
- [ ] 서버 시작 후 각 엔드포인트 호출 테스트
- [ ] 프론트엔드 빌드 및 UI 확인

---

## 🗓️ Phase 2: Stability (안정성 개선)

> **예상 소요:** 3-5일  
> **목표:** 로깅, 에러 처리, 환경변수 분리

### 작업 목록

| # | 작업 | 관련 파일 | 상태 | 담당 |
|---|------|-----------|------|------|
| 2.1 | Python `logging` 모듈 도입 | 전체 master/, worker/ | ⬜ | - |
| 2.2 | `except Exception: pass` → 구체적 예외 처리 + 에러 로깅 | `worker/agent.py`, `comfy_client.py`, `gpu_reporter.py` | ⬜ | - |
| 2.3 | 환경변수 기반 URL 설정 분리 | `.env` 파일 생성, 각 모듈 수정 | ⬜ | - |
| 2.4 | Worker 작업 완료 폴링 루프 구현 | `worker/agent.py`, `job_executor.py` | ⬜ | - |
| 2.5 | GPU 감지 실패시 가짜 데이터 대신 에러 상태 반환 | `worker/gpu_reporter.py` | ⬜ | - |

### 세부 작업

#### 2.1 로깅 시스템 구축
```
- [ ] logging 설정 유틸리티 생성 (master/utils/logger.py)
- [ ] 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR)
- [ ] 로그 로테이션 설정 (TimedRotatingFileHandler)
- [ ] 모든 print() 문을 logger 호출로 교체
```

#### 2.3 환경변수 분리
```
- [ ] .env.example 템플릿 생성
- [ ] python-dotenv 의존성 추가
- [ ] COMFYUI_URL, MASTER_WS_URL, API_BASE_URL 등 정의
- [ ] frontend/.env 또는 vite.config.js 환경변수 설정
```

#### 2.4 Worker 작업 완료 폴링
```
- [ ] ComfyUI history API 엔드포인트 확인
- [ ] 폴링 루프 구현 (5초 간격)
- [ ] job_completed / job_failed 메시지 타입 추가
- [ ] Master 측 메시지 핸들러 구현
```

### 검증 방법
- [ ] 로그 파일 생성 및 로테이션 확인
- [ ] 의도적 에러 발생 후 로그 기록 확인
- [ ] 환경변수로 다른 포트/URL 설정 후 정상 작동 확인
- [ ] 작업 제출 → 완료 전체 사이클 테스트

---

## 🗓️ Phase 3: Data Integrity (데이터 무결성)

> **예상 소요:** 5-7일  
> **목표:** 데이터베이스 도입, 안전한 데이터 저장

### 작업 목록

| # | 작업 | 관련 파일 | 상태 | 담당 |
|---|------|-----------|------|------|
| 3.1 | SQLite/PostgreSQL DB 레이어 도입 | `master/services/database.py` (신규) | ⬜ | - |
| 3.2 | JSON 파일 atomic write 적용 (전환 기간) | `master/services/data_manager.py` | ⬜ | - |
| 3.3 | 스키마 마이그레이션 전략 수립 | Alembic 설정 | ⬜ | - |
| 3.4 | ID 생성을 UUID 기반으로 변경 | Frontend 컴포넌트, Backend 서비스 | ⬜ | - |

### 세부 작업

#### 3.1 DB 레이어 도입
```
- [ ] SQLAlchemy async 의존성 추가
- [ ] DB 모델 정의 (Job, Worker, Shot, Character, Project)
- [ ] 마이그레이션 스크립트 작성
- [ ] data_manager.py → database.py 전환
- [ ] 기존 JSON 데이터 마이그레이션 스크립트
```

#### 3.2 Atomic Write (임시 전환 기간)
```
- [ ] tempfile 모듈 사용 임시 파일 작성
- [ ] 성공 후 rename으로 원본 교체
- [ ] 실패시 원본 유지 보장
```

#### 3.4 UUID 기반 ID
```
- [ ] Backend: uuid.uuid4() 사용 ID 생성 유틸 생성
- [ ] Frontend: 서버에서 ID 수신하도록 변경
- [ ] 기존 데이터 마이그레이션 고려
```

### 검증 방법
- [ ] 서버 재시작 후 데이터 유지 확인
- [ ] 동시 저장 시뮬레이션 (경쟁 조건 테스트)
- [ ] 마이그레이션 후 기존 데이터 정상 로드 확인

---

## 🗓️ Phase 4: Security (보안 강화)

> **예상 소요:** 3-5일  
> **목표:** 인증/인가, CORS 정책, 입력 검증

### 작업 목록

| # | 작업 | 관련 파일 | 상태 | 담당 |
|---|------|-----------|------|------|
| 4.1 | JWT 또는 API key 인증 미들웨어 | `master/middleware/auth.py` (신규) | ⬜ | - |
| 4.2 | CORS 정책 제한 | `master/main.py` | ⬜ | - |
| 4.3 | 파일 업로드 MIME 타입/크기 검증 강화 | routers 전체 | ⬜ | - |
| 4.4 | 입력값 sanitization 추가 | routers 전체 | ⬜ | - |

### 세부 작업

#### 4.1 인증 미들웨어
```
- [ ] python-jose 또는 PyJWT 의존성 추가
- [ ] JWT 토큰 생성/검증 유틸 구현
- [ ] FastAPI Depends로 인증 체크 미들웨어
- [ ] 로그인 엔드포인트 추가 (/auth/login)
- [ ] Frontend axios 인터셉터에 토큰 헤더 추가
```

#### 4.2 CORS 정책
```
- [ ] allow_origins에 명시적 도메인 리스트
- [ ] allow_methods에 필요한 메서드만 명시
- [ ] 환경별 CORS 설정 분리 (dev/prod)
```

### 검증 방법
- [ ] 인증 없이 API 호출시 401 응답 확인
- [ ] 유효한 토큰으로 API 호출 성공 확인
- [ ] 허용되지 않은 origin에서 CORS 차단 확인

---

## 🗓️ Phase 5: Quality (코드 품질)

> **예상 소요:** 5-7일  
> **목표:** 에러 바운더리, 의존성 정리, 테스트 코드

### 작업 목록

| # | 작업 | 관련 파일 | 상태 | 담당 |
|---|------|-----------|------|------|
| 5.1 | React Error Boundary 추가 | `frontend/src/components/ErrorBoundary.jsx` (신규) | ⬜ | - |
| 5.2 | 미사용 의존성 제거 (Zustand 또는 활용) | `frontend/package.json` | ⬜ | - |
| 5.3 | 핵심 서비스 unit test 작성 | `master/tests/` (신규) | ⬜ | - |
| 5.4 | API 통합 테스트 작성 | `master/tests/` (신규) | ⬜ | - |
| 5.5 | 워크플로우 템플릿 스키마 검증 | `worker/job_executor.py` | ⬜ | - |

### 세부 작업

#### 5.1 Error Boundary
```
- [ ] ErrorBoundary 컴포넌트 생성
- [ ] 에러 발생시 fallback UI 렌더링
- [ ] App.jsx에서 주요 섹션 감싸기
- [ ] 에러 로깅 서비스 연동 (선택)
```

#### 5.3-5.4 테스트 코드
```
- [ ] pytest 의존성 추가
- [ ] conftest.py 설정 (fixtures)
- [ ] job_manager.py unit tests
- [ ] prompt_engine.py unit tests
- [ ] API 엔드포인트 통합 테스트
```

### 검증 방법
- [ ] 컴포넌트 에러 발생시 전체 앱 크래시 방지 확인
- [ ] `npm audit` 결과 확인
- [ ] `pytest` 실행 후 전체 통과 확인

---

## 📅 전체 타임라인 요약

```
Week 1
├── Day 1-2: Phase 1 (즉시 수정)
└── Day 3-7: Phase 2 (안정성) 시작

Week 2
├── Day 1-3: Phase 2 (안정성) 완료
└── Day 4-7: Phase 3 (데이터) 시작

Week 3
├── Day 1-3: Phase 3 (데이터) 완료
└── Day 4-7: Phase 4 (보안)

Week 4
├── Day 1-2: Phase 4 (보안) 완료
└── Day 3-7: Phase 5 (품질)
```

---

## 📝 참고 사항

### 우선순위 조정 기준
- 팀 규모/가용 리소스에 따라 Phase 병렬 진행 가능
- Phase 3 (DB)는 영향도가 크므로 충분한 테스트 필요
- Phase 4 (보안)는 프로덕션 배포 전 필수

### 의존성 관계
```
Phase 1 ─┐
         ├─→ Phase 2 ─→ Phase 3
Phase 4 ─┴─→ Phase 5 (독립 진행 가능)
```

### 리스크 요소
1. DB 마이그레이션 중 데이터 손실 위험 → 백업 필수
2. 인증 도입 시 기존 워크플로우 중단 가능 → 점진적 적용
3. Worker 폴링 로직 변경시 진행중 작업 영향 → 테스트 환경 분리

---

*이 문서는 code_review_2026-02-04.md를 기반으로 자동 생성되었습니다.*
