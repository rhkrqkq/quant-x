# Quant-X — 금융 멀티 에이전트 리서치 시스템

> 금융 풀스택 과정 실습 프로젝트
> 챕터 진행하면서 점진적으로 구축한다.

## 시스템 구성

- **Frontend**: React 18 + TypeScript
- **Backend**: Spring Boot 3.x + Spring Security + JPA + MariaDB
- **AI Server**: FastAPI + LangChain + LangGraph + Chroma
- **Mock Core Service**: FastAPI + SQLite (Core Zone 시뮬레이션)
- **LLM**: OpenAI GPT-4o-mini (개발) / Qwen 2.5 (폐쇄망)

## 실행

DB만 컨테이너로 띄우고, 나머지 서버는 각자 터미널에서 직접 실행한다.
의존 방향의 역순 — 불리는 쪽을 먼저 올린다. (전체 순서는 11장 검증 ①)

1. MariaDB      : docker start quantx-mariadb            (3장)
2. Mock Core    : mock-core-service/ → uvicorn app.main:app --port 9000   (8장)
3. AI 서버     : ai-server/        → uvicorn app.main:app --port 8000   (3장)
4. 백엔드      : backend/          → ./gradlew bootRun                 (3장)
5. 프런트      : frontend/         → npm run dev                       (11장)

## 주의

- 본 시스템은 교육용으로 실제 투자 결정에 사용 금지.
- 모든 사용자 활동은 감사 로그에 기록.
- 민감 정보(주민번호, 계좌번호 등)는 입력 시 자동 마스킹.