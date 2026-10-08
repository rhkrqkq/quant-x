# Quant-X 데이터 분류표

| ID     | 데이터 유형            | 분류 | 출처             | 형태          | 보안등급 |        본 과정 사용        |    Zone    | Agent 접근                |
| ------ | ---------------------- | :--: | ---------------- | ------------- | :------: | :------------------------: | :--------: | ------------------------- |
| DC-001 | 고객 신상정보          |  ①   | Core Banking     | 정형          |   최고   |             ✗              |    Core    | 불가                      |
| DC-002 | 계좌 잔고/거래         |  ①   | 증권 원장        | 정형          |   최고   | **Mock Core Service**(8장) |    Core    | Indirect Tool only (Read) |
| DC-003 | 실시간 시세            |  ②   | KRX/Coscom       | 정형 (피드)   |    중    |        △ (yfinance)        |   Middle   | Read                      |
| DC-004 | 일봉 OHLCV             |  ②   | yfinance/사내 DM | 정형          |    중    |             ✓              |   Middle   | Read                      |
| DC-005 | 종목 마스터            |  ②   | 사내 DM          | 정형          |   일반   |             ✓              |   Middle   | Read                      |
| DC-006 | 재무지표 (PER/PBR/ROE) |  ②   | yfinance/DART    | 정형          |   일반   |             ✓              |   Middle   | Read                      |
| DC-007 | 사내 리서치 리포트     |  ③   | 사내 R&D         | 비정형        |    중    |             ✓              |   Middle   | RAG_READ                  |
| DC-008 | 외부 애널리스트 리포트 |  ③   | 증권사 외부      | 비정형        |    중    |        △ (HF 합성)         |   Middle   | RAG_READ                  |
| DC-009 | 기업공시 (DART)        |  ③   | DART 공개        | 비정형        |   일반   |             ✓              |   Middle   | RAG_READ                  |
| DC-010 | 뉴스                   |  ③   | 외부 RSS         | 비정형        |   일반   |          △ (Mock)          | DMZ→Middle | RAG_READ                  |
| DC-011 | 금융감독 규정          |  ④   | 법령/감독규정    | 계층적 텍스트 |    중    |             ✓              |   Middle   | RAG_READ                  |
| DC-012 | 컴플라이언스 문서      |  ④   | 사내 준법        | 계층적 텍스트 |    중    |             ✓              |   Middle   | RAG_READ                  |
| DC-013 | 보안 가이드라인        |  ④   | 금융보안원       | 비정형        |   일반   |             ✓              |   Middle   | RAG_READ                  |

## 사용 정책

- ✓: 실제 데이터 사용
- ✗: 절대 사용하지 않음 (Mock도 만들지 않음)
- Mock: 가공된 가상 데이터로 시뮬레이션만 (운영 코드 흐름은 동일)
- △: 외부 공개 또는 합성 데이터로 대체

## Quant-X 절대 금지선

- DC-001 (고객 신상정보)는 **어떤 형태로도** 본 과정 시스템에 들어와선 안 된다.
- DC-002는 **Mock Core Service**(별도 프로세스, 8장)에서 시뮬레이션하며, 실제 계좌번호 패턴(예: 110-123-456789)을 입력하면 즉시 마스킹된다. AI Agent는 Read 권한만 갖고, Write(주문)는 인간 승인(HITL) 후 Spring Boot 시스템 권한으로만 가능하다.
- 모든 외부 LLM 호출은 ALLOW_EXTERNAL_LLM 플래그 검사 후에만 가능.
