# Quant-X Agent 권한 매트릭스

## 1. Agent별 역할 정의

| Agent ID               | Role           | 책임                                |
| ---------------------- | -------------- | ----------------------------------- |
| `research-agent`       | RESEARCH       | 사내·외부 문서 검색, 팩트 수집      |
| `market-analyst-agent` | MARKET_ANALYST | 시세·재무 데이터 분석, 차트 생성    |
| `risk-reviewer-agent`  | RISK_REVIEWER  | 규제·컴플라이언스 검토, 리스크 평가 |
| `report-writer-agent`  | REPORT_WRITER  | 최종 보고서 작성, 출력 필터 통과    |
| `manager-agent`        | MANAGER        | 위 4개 Worker 오케스트레이션        |

## 2. Scope 매트릭스

| Scope \\ Agent      | research | market | risk | writer | manager |
| ------------------- | :------: | :----: | :--: | :----: | :-----: |
| `RAG_READ`          |    ✓     |        |  ✓   |   ✓    |         |
| `WEB_SEARCH`        |    ✓     |        |      |        |         |
| `MARKET_DATA_READ`  |          |   ✓    |  ✓   |        |         |
| `STOCK_MASTER_READ` |          |   ✓    |      |        |         |
| `REPORT_READ`       |    ✓     |   ✓    |  ✓   |   ✓    |    ✓    |
| `REPORT_WRITE`      |          |        |      |   ✓    |         |
| `ACCOUNT_READ`      |    ✗     |   ✗    |  ✗   |   ✗    |    ✗    |
| `ORDER_WRITE`       |    ✗     |   ✗    |  ✗   |   ✗    |    ✗    |

## 3. Tool 매트릭스

| Tool \\ Agent            | research | market | risk |         writer         | manager |
| ------------------------ | :------: | :----: | :--: | :--------------------: | :-----: |
| `search_internal` (RAG)  |    ✓     |        |  ✓   |           ✓            |         |
| `search_web`             |    ✓     |        |      |                        |         |
| `get_market_summary`     |          |   ✓    |      |                        |         |
| `get_stock_price`        |          |   ✓    |      |                        |         |
| `get_financial_metrics`  |          |   ✓    |      |                        |         |
| `check_compliance_rules` |          |        |  ✓   |                        |         |
| `save_report`            |          |        |      | ✓ (Senior 사용자 한정) |         |
| `dispatch_to_worker`     |          |        |      |                        |    ✓    |

## 4. 사용자(Senior/Junior) × Agent 권한

| 권한                     | Junior Analyst | Senior Manager |
| ------------------------ | :------------: | :------------: |
| 모든 Agent 호출          |       ✓        |       ✓        |
| 보고서 저장              |       ✗        |       ✓        |
| 보고서 승인/반려         |       ✗        |       ✓        |
| Kill Switch 토글         |       ✗        |       ✓        |
| 감사 로그 조회           |   본인 것만    |      전체      |
| LLM Provider 전환 (10장) |       ✗        |       ✓        |

## 5. Tool 호출 통제 분류

| 통제 수준         | Tool 예시                        | 검증 절차                                  |
| ----------------- | -------------------------------- | ------------------------------------------ |
| Auto              | search_internal, get_stock_price | Scope 검사만                               |
| Semi-Auto         | save_report                      | Scope + Senior 권한 검사                   |
| Human-in-the-Loop | (Mock) execute_order             | + 명시적 인간 승인 (본 과정에선 화면 데모) |
