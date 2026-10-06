#!/usr/bin/env bash
# Quant-X 본 과정용 워크스페이스 초기화 스크립트
set -euo pipefail

# 1. 백엔드 디렉토리 (Spring Boot)
mkdir -p backend

# 2. AI 서버 디렉토리 (FastAPI)
mkdir -p ai-server

# 3. Mock Core Service 디렉토리 (8장)
mkdir -p mock-core-service

# 4. 프론트엔드 디렉토리 (React)
mkdir -p frontend

# 5. 공통 docs
mkdir -p docs
cat > docs/ARCHITECTURE.md <<'EOF'
# Quant-X 아키텍처
- React (DMZ) → Spring Boot (Service Layer) → FastAPI (AI Layer) → Mock Core Service (Core Zone)
- 자세한 다이어그램은 1장 §4.1 참조
EOF

# 6. 공통 .gitignore
cat > .gitignore <<'EOF'
# Python
ai-server/.venv/
ai-server/__pycache__/
mock-core-service/.venv/
mock-core-service/data/*.db
**/*.pyc

# Node
frontend/node_modules/
frontend/dist/

# Java
backend/build/
backend/.gradle/

# 환경변수 (절대 커밋 금지)
.env
.env.*
!.env.example

# 데이터/로그
data/
logs/
*.db
EOF

# 7. 환경변수 템플릿
cat > .env.example <<'EOF'
# === LLM ===
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=

# === 폐쇄망 (10장) ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
ALLOW_EXTERNAL_LLM=true

# === Vector DB (4장) ===
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_PROVIDER=openai

# === Spring Boot ↔ FastAPI (3장) ===
AI_SERVER_BASE_URL=http://localhost:8000
AI_SERVER_API_KEY=changeme-internal-key
JWT_SECRET=changeme-jwt-secret

# === Mock Core Service (8장) ===
MOCK_CORE_BASE_URL=http://localhost:9000
MOCK_CORE_API_KEY=changeme-core-key
MOCK_CORE_LATENCY_MS_MIN=50
MOCK_CORE_LATENCY_MS_MAX=200
MOCK_CORE_FAIL_RATE=0.05
ORDER_SINGLE_LIMIT_KRW=100000000
ORDER_DAILY_LIMIT_KRW=500000000

# === 보안 ===
KILL_SWITCH_ENABLED=false
PII_MASK_LEVEL=strict
EOF

echo "Quant-X 워크스페이스가 생성되었습니다."