# 폐쇄망 운영 정책

## 환경변수

| 변수                 | 외부망 모드 | 폐쇄망 모드          |
| -------------------- | ----------- | -------------------- |
| `ALLOW_EXTERNAL_LLM` | `true`      | `false`              |
| `LLM_PROVIDER`       | `openai`    | `ollama` 또는 `vllm` |
| `EMBEDDING_PROVIDER` | `openai`    | `bge-m3` (로컬)      |

## 폐쇄망 모드 동작

1. FastAPI 시작 시 `ALLOW_EXTERNAL_LLM=false`이면:
   - OpenAI 클라이언트 인스턴스화 거부
   - 환경변수 `OPENAI_API_KEY`가 있어도 무시
2. LLM Provider Registry에서 `external=true` 항목 비활성화
3. 모든 외부 도메인 호출 시도 시 즉시 차단 + CRITICAL 알람

## 검증 방법

```bash
# 폐쇄망 모드로 실행
ALLOW_EXTERNAL_LLM=false LLM_PROVIDER=ollama \
  uvicorn ai-server.app.main:app

# 외부 API 호출 시도 (실패해야 함)
curl -X POST http://localhost:8000/ai/research \
  -H "X-Internal-API-Key: changeme-internal-key" \
  -d '{"query":"테스트"}'

# 기대: 503 또는 기본 ollama 사용

## **10장 연계**

본 정책은 10장 §7 LLM Adapter 구현으로 연결된다.
```
