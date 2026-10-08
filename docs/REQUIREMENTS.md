# Quant-X MVP 요구사항
## 1. 비즈니스 요구사항
- **누가**: 증권사 리서치센터 주니어 애널리스트, 시니어 매니저
- **무엇을**: 한국 상장사에 대한 자동화된 리서치 보고서 초안
- **왜**: 반복 리서치 업무 시간 단축, 누락 정보 최소화
## 2. 사용자 역할 및 권한

| 역할 | 권한 | 비고 |
|---|---|---|
| Junior Analyst | RAG_READ, MARKET_DATA_READ, ACCOUNT_READ, REPORT_READ | 보고서 저장·결재 불가 |
| Senior Manager | Junior Analyst 권한 전체 + REPORT_WRITE, ADMIN | 모든 권한 + HITL 결재 |

## 3. 화면 목록
- FR-UI-01 로그인 화면
- FR-UI-02 리서치 요청 화면
- FR-UI-03 Agent 실행 상태 화면 (Timeline)
- FR-UI-04 결과 보고서 + 근거 문서 화면
- FR-UI-05 주문 결재 대기 / 승인 / 반려 화면 (Senior만)
- FR-UI-06 감사 로그 조회 화면
- FR-UI-07 관리자 Kill Switch / LLM Provider 전환 화면
## 4. 기능 요구사항 (발췌)
- FR-001 사용자는 자연어로 리서치 요청을 입력할 수 있다.
- FR-002 시스템은 입력에 PII가 포함되면 차단한다.
- FR-003 4개 Agent가 협업하여 보고서를 생성한다.
- FR-004 보고서는 RAG 근거 문서를 인용한다.
- FR-005 모든 Tool 호출은 감사 로그에 기록된다.
- FR-006 Senior Manager는 Kill Switch를 활성화할 수 있다.
- FR-007 보고서 저장은 Senior Manager 권한이 필요하다.
- FR-008 LLM Provider는 환경변수로 OpenAI/Ollama/vLLM 전환 가능.
- FR-009 AI Agent는 주문 실행 권한을 가질 수 없으며, 주문은 Senior Manager의 명시적 결재(HITL)를 거친다.
- FR-010 Mock Core Service는 별도 프로세스로 실행되며, Tool Gateway는 Read만, Spring Boot는 시스템 권한으로 Write 가능하다.
## 5. 비기능 요구사항
- 응답 시간 ≤ 30초 (95th percentile)
- 가용성 ≥ 99% (Kill Switch 발동 제외)
- 감사 로그 보관 ≥ 1년
- 모든 입출력 로깅 (개인정보는 해시로)
## 6. 제약사항
- 폐쇄망 모드 운영 가능해야 함 (외부 API 호출 금지 옵션)
- 개인신용정보 LLM 전송 절대 금지
- 외부 LLM 호출 시 학습 미사용(Opt-out) 계약 전제
## 7. 외부 의존성
- OpenAI API (개발) / Ollama (폐쇄망)
- Chroma (Vector DB)
- yfinance (시장 데이터, 개발용 - 운영은 사내 데이터마트)
## 8. 위험 요소
- R-001 LLM 환각 → Output Filter + 인간 승인
- R-002 RAG 문서 오염 → Untrusted Context 분리, 신뢰도 점수
- R-003 권한 우회 → Tool Gateway + Scope Token
- R-004 외부 API 장애 → Mock 모드 폴백
- R-005 비용 폭증 → 호출 한도 + 모니터링
- R-006 AI 단독 거래 → HITL 강제, Agent에 Write Scope 부재