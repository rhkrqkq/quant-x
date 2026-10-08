-- ============================================================
-- 본 과정 3장 시점 DDL — users / user_scopes / research_request / research_report
-- 원본: 부록 C §2, §3
-- 적용 대상: MariaDB 11+
-- ============================================================

USE quantx;

-- ----------------------------------------------------------------
-- 2.1 users
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id         VARCHAR(64)  NOT NULL UNIQUE,
  password_hash   VARCHAR(255) NOT NULL,
  name            VARCHAR(100) NOT NULL,
  email           VARCHAR(255),
  role            VARCHAR(32)  NOT NULL,          -- JUNIOR_ANALYST, SENIOR_MANAGER, ADMIN
  active          BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 2.2 user_scopes
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_scopes (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id     BIGINT NOT NULL,
  scope       VARCHAR(64) NOT NULL,               -- RAG_READ, MARKET_DATA_READ, ...
  granted_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  expires_at  DATETIME(6),
  CONSTRAINT fk_user_scopes_user FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE KEY uk_user_scopes (user_id, scope)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 3.1 research_request
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_request (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id         VARCHAR(64) NOT NULL,
  query           TEXT        NOT NULL,
  scope_json      JSON,                            -- ["RAG_READ", "MARKET_DATA_READ"]
  priority        VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  status          VARCHAR(32) NOT NULL DEFAULT 'CREATED',
                                                   -- CREATED, RUNNING, COMPLETED, FAILED, BLOCKED
  job_id          VARCHAR(64),                     -- FastAPI Job UUID
  created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  started_at      DATETIME(6),
  finished_at     DATETIME(6),
  INDEX idx_rr_user (user_id),
  INDEX idx_rr_status (status),
  INDEX idx_rr_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 3.2 research_report
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_report (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  request_id      BIGINT NOT NULL,
  title           VARCHAR(500) NOT NULL,
  summary         TEXT,
  body_json       JSON         NOT NULL,           -- sections, citations, ...
  disclaimer      TEXT,
  approval_status VARCHAR(32)  NOT NULL DEFAULT 'PENDING',
                                                   -- PENDING, APPROVED, REJECTED
  created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_report_request FOREIGN KEY (request_id) REFERENCES research_request(id),
  INDEX idx_report_approval (approval_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
