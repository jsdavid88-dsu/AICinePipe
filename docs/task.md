# AI Production Pipeline Tool - 개발 태스크

## Phase 1: 기획 및 설계
- [x] 시스템 아키텍처 설계
- [x] 데이터 모델 설계 (샷리스트, 캐릭터, 시네마틱 옵션)
- [x] 렌더팜 아키텍처 설계 (Master/Worker 구조)
- [x] 영상 모델 및 LoRA 확장 설계 (LTX-2, SVI, TeleStyle)
- [x] UI/UX 설계 (웹 기반 대시보드)

## Phase 2: Master 서버 - 데이터 관리 모듈
- [x] 서버 환경 설정 및 실행 테스트
- [x] Excel/JSON 기반 데이터 스키마 정의
- [x] 샷리스트 테이블 구현
- [x] 캐릭터 바이블 테이블 (LoRA 필드 포함) 구현
- [x] 시네마틱 옵션 테이블 구현
- [x] 프롬프트 조립 엔진 (LoRA 트리거 연동) 구현

## Phase 3: Master 서버 - 이미지 생성 모듈
- [x] 작업(Job) 모델 구현
- [x] 작업 큐 시스템 (JobManager)
- [ ] 프롬프트 템플릿 시스템
- [ ] LoRA 동적 로딩 지원

## Phase 4: 렌더팜 - 기본 구조
- [x] Worker 노드 모델
- [x] Master ↔ Worker WebSocket 통신
- [x] 공유 스토리지 구조 (로컬 폴더 활용)

## Phase 5: 렌더팜 - Worker 에이전트
- [x] Worker Agent 메인 루프
- [x] GPU 상태 리포터 (nvidia-smi/GPUtil 연동)
- [x] ComfyUI API 클라이언트
- [x] 작업 실행기
- [ ] 작업 스케줄러 (고도화)

## Phase 6: 렌더팜 - 작업 스케줄러
- [ ] GPU 모니터링 서비스
- [ ] 작업 분배 알고리즘
- [ ] 워크플로우별 VRAM 요구량 매핑 (LTX-2, SVI 등 추가)
- [ ] 로드 밸런싱

## Phase 7: 스토리보드 편집 모듈
- [ ] 타임라인 UI 구현
- [ ] 프레임/플레이타임 조절 기능
- [ ] 편집 결과 → 데이터베이스 동기화

## Phase 8: 영상 생성 모듈
- [ ] LLM 기반 워크플로우 추천 시스템
- [ ] 멀티 워크플로우 지원 (WAN, LTX-2, SVI, TeleStyle, FFLF)
- [ ] Batch 렌더링 큐 시스템
- [ ] 상태 관리 (대기/진행/컨펌/재생성)

## Phase 9: 퍼블리시 및 통합
- [ ] 최종 출력 시스템
- [ ] 프로젝트별 데이터 저장 구조
- [ ] 편집 ↔ 파이프라인 연동
