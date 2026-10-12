-- 8장. Core Zone 시뮬레이션과 HITL
-- Spring Boot 쪽 결재 큐 + Core Zone 조회 권한
-- 적용: docker exec -i quantx-mariadb mariadb -uroot -proot quantx < 부록/sql/04_hitl_schema.sql
--
-- Mock Core Service의 세 테이블(mock_accounts / mock_orders / mock_core_log)은
-- 여기 없다. 그쪽은 SQLite이고 서비스가 뜰 때 스스로 만든다.
-- Core Zone과 Middle Zone은 DB 파일부터 나뉜다는 뜻이다.

USE quantx;

-- ----------------------------------------------------------------
-- 1. 결재 큐
--    research_report_id에 외래 키를 걸지 않는다. 보고서를 거치지 않고 낸 주문도 있고,
--    실행 이력(agent_execution)과 마찬가지로 추적용 참조로만 쓴다.
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_approval_queue (
  id                   BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id             VARCHAR(64)  NOT NULL UNIQUE,        -- Core Zone의 order_id
  research_report_id   BIGINT,
  account_id           VARCHAR(32)  NOT NULL,
  ticker               VARCHAR(16)  NOT NULL,
  side                 VARCHAR(8)   NOT NULL,
  quantity             INT          NOT NULL,
  price                INT          NOT NULL,
  estimated_amount_krw BIGINT       NOT NULL,
  submitted_by         VARCHAR(64)  NOT NULL,
  status               VARCHAR(16)  NOT NULL,               -- Core Zone과 동기화된 상태
  decided_by           VARCHAR(64),
  decided_at           DATETIME(6),
  comment              TEXT,
  created_at           DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at           DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  INDEX idx_oaq_status (status),
  INDEX idx_oaq_submitted_by (submitted_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------
-- 2. Core Zone 조회 권한
--    ACCOUNT_READ는 계좌를 볼 수 있는 권한이다. 주문을 넣는 권한(ORDER_WRITE)은
--    누구에게도 주지 않는다. 주문은 결재를 거쳐 시스템 권한으로만 나간다.
-- ----------------------------------------------------------------
INSERT IGNORE INTO user_scopes (user_id, scope, granted_at)
SELECT id, 'ACCOUNT_READ', NOW(6)
FROM users
WHERE user_id = 'senior_001';