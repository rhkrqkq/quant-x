-- 8장. Core Zone 시뮬레이션과 HITL
-- Mock Core Service 스키마 (SQLite). 부록 C §9와 같은 내용이다.
-- 서비스가 뜰 때 db.py가 이 파일을 그대로 실행한다.

CREATE TABLE IF NOT EXISTS mock_accounts (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id            TEXT NOT NULL UNIQUE,             -- 'acc-001'
  account_number_masked TEXT NOT NULL,                    -- '110-***-456789'
  holder_name_masked    TEXT NOT NULL,                    -- '홍**'
  type                  TEXT NOT NULL,                    -- STOCK, CMA
  balance_krw           INTEGER NOT NULL DEFAULT 0,
  available_krw         INTEGER NOT NULL DEFAULT 0,
  opened_at             TEXT NOT NULL,                    -- ISO-8601
  active                INTEGER NOT NULL DEFAULT 1,
  created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ma_account_id ON mock_accounts(account_id);

CREATE TABLE IF NOT EXISTS mock_orders (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id              TEXT NOT NULL UNIQUE,             -- UUID
  idempotency_key       TEXT NOT NULL UNIQUE,             -- 중복 접수 차단
  account_id            TEXT NOT NULL,
  ticker                TEXT NOT NULL,
  side                  TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
  quantity              INTEGER NOT NULL,
  price                 INTEGER NOT NULL,
  estimated_amount_krw  INTEGER NOT NULL,                 -- quantity * price
  status                TEXT NOT NULL CHECK(status IN
                          ('PENDING','EXECUTED','REJECTED','EXPIRED','FAILED')),
  submitted_by          TEXT NOT NULL,                    -- 결재 요청자 user_id
  research_report_id    INTEGER,                          -- 어느 보고서에서 비롯됐는지 (추적용)
  decided_by            TEXT,                             -- 결재자 user_id
  decided_at            TEXT,
  executed_at           TEXT,
  execution_price_krw   INTEGER,
  actual_amount_krw     INTEGER,
  reject_reason         TEXT,
  created_at            TEXT NOT NULL DEFAULT (datetime('now')),
  decision_required_by  TEXT NOT NULL,                    -- 만료 시각

  FOREIGN KEY (account_id) REFERENCES mock_accounts(account_id)
);

CREATE INDEX IF NOT EXISTS idx_mo_account ON mock_orders(account_id);
CREATE INDEX IF NOT EXISTS idx_mo_status  ON mock_orders(status);
CREATE INDEX IF NOT EXISTS idx_mo_created ON mock_orders(created_at);

-- Mock Core가 자기 앞으로 들어온 호출을 직접 남기는 감사 로그.
-- AI 서버의 Tool 호출 로그와 별개다. Core Zone은 자기 기록을 스스로 갖는다.
CREATE TABLE IF NOT EXISTS mock_core_log (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id        TEXT NOT NULL,                        -- correlation ID
  caller            TEXT NOT NULL,                        -- 'ai-server' | 'spring-boot'
  caller_user_id    TEXT,
  endpoint          TEXT NOT NULL,
  method            TEXT NOT NULL,
  params_hash       TEXT,                                 -- SHA-256 (본문은 남기지 않는다)
  status_code       INTEGER NOT NULL,
  duration_ms       INTEGER NOT NULL,
  error             TEXT,
  created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_mcl_caller   ON mock_core_log(caller);
CREATE INDEX IF NOT EXISTS idx_mcl_endpoint ON mock_core_log(endpoint);
CREATE INDEX IF NOT EXISTS idx_mcl_created  ON mock_core_log(created_at);