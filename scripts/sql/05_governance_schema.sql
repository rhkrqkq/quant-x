-- 9장. 금융 보안 가드레일과 거버넌스
-- 감사 로그 · 가드레일 이벤트 · Kill Switch · Tool 호출 기록
-- 적용: docker exec -i quantx-mariadb mariadb -uroot -proot quantx < 부록/sql/05_governance_schema.sql
--
-- 네 테이블을 관통하는 축은 request_uid 하나다.
-- Spring Boot가 요청마다 UUID를 만들고, FastAPI가 그대로 들고 다니다가
-- Core Zone 호출에도 실어 보낸다. 8장의 mock_core_log.request_id가 같은 값을 받는다.
-- "이 조회는 누가 왜 했는가"에 답하려면 로그가 하나로 이어져야 한다.

USE quantx;

-- ----------------------------------------------------------------
-- 1. 감사 로그 (Append-Only)
--    사람의 행위는 Spring Boot가, Agent의 행위는 FastAPI가 넣는다.
--    두 서버가 같은 테이블에 쓰지만 type으로 구분된다.
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
  id               BIGINT PRIMARY KEY AUTO_INCREMENT,
  type             VARCHAR(64)  NOT NULL,          -- USER_LOGIN, RESEARCH_REQUEST_CREATED,
                                                   -- ORDER_SUBMITTED, ORDER_APPROVED, ORDER_REJECTED,
                                                   -- KILL_SWITCH_TOGGLED, AGENT_EXECUTION,
                                                   -- AGENT_TOOL_CALL, GUARDRAIL_BLOCKED
  request_uid      VARCHAR(64),                    -- 요청 상관관계 ID
  user_id          VARCHAR(64),
  agent_id         VARCHAR(64),
  request_id       BIGINT,                         -- research_request.id (있을 때만)
  payload_json     JSON         NOT NULL,          -- 원본이 아니라 요약. PII는 넣지 않는다
  payload_hash     VARCHAR(64),                    -- SHA-256 hex (위변조 검증용)
  prev_hash        VARCHAR(64),                    -- 이전 레코드 hash. 본 과정에서는 채우지 않는다
  created_at       DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_al_type (type),
  INDEX idx_al_user (user_id),
  INDEX idx_al_uid (request_uid),
  INDEX idx_al_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- append-only는 아래 §5의 전용 계정 권한으로 보장한다. 트리거는 쓰지 않는다.

-- ----------------------------------------------------------------
-- 2. 가드레일 이벤트
--    원본 텍스트는 남기지 않는다. 주민번호를 걸러 낸 기록에 주민번호가 들어 있으면
--    로그 자체가 유출 경로가 된다 (8장 mock_core_log.params_hash와 같은 판단).
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS guardrail_event (
  id               BIGINT PRIMARY KEY AUTO_INCREMENT,
  type             VARCHAR(32)  NOT NULL,          -- INPUT, OUTPUT
  severity         VARCHAR(16)  NOT NULL,          -- SAFE, WARNING, BLOCKED
  request_uid      VARCHAR(64),
  user_id          VARCHAR(64),
  agent_id         VARCHAR(64),
  request_id       BIGINT,
  detected_issues  JSON         NOT NULL,          -- ["PII_DETECTED:RRN", "INJECTION:IGNORE_PREV"]
  payload_hash     VARCHAR(64)  NOT NULL,          -- 원본 텍스트 SHA-256. 원본은 저장하지 않는다
  filtered_text    TEXT,                           -- 마스킹을 마친 결과라 남겨도 된다
  blocked          BOOLEAN      NOT NULL,
  created_at       DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_ge_severity (severity),
  INDEX idx_ge_user (user_id),
  INDEX idx_ge_uid (request_uid),
  INDEX idx_ge_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------
-- 3. Kill Switch 상태
--    현재 상태를 UPDATE하지 않고 토글할 때마다 한 줄씩 쌓는다.
--    "지금 켜져 있나"보다 "언제 누가 왜 껐다 켰나"가 감사에서 중요하다.
--    최신 행 하나가 현재 상태다.
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kill_switch_status (
  id               BIGINT PRIMARY KEY AUTO_INCREMENT,
  active           BOOLEAN      NOT NULL,
  reason           VARCHAR(500),
  toggled_by       VARCHAR(64)  NOT NULL,
  toggled_at       DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_ks_toggled (toggled_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 초기 상태 한 줄. 이 행이 없으면 FastAPI가 "기록이 없으니 꺼진 것"으로 읽는다.
INSERT INTO kill_switch_status (active, reason, toggled_by)
SELECT 0, '초기 상태', 'system'
 WHERE NOT EXISTS (SELECT 1 FROM kill_switch_status);

-- ----------------------------------------------------------------
-- 4. Tool 호출 기록
--    7장까지 Tool Gateway가 메모리에 들고 있던 것(ToolGateway._call_log)을 여기로 옮긴다.
--
--    부록 C §4.3은 execution_id를 NOT NULL + agent_execution 외래 키로 잡았지만 뺐다.
--    Tool Gateway는 자기를 부른 실행이 무엇인지 모르고, /ai/tools/{name}/invoke로 직접
--    부르는 경로는 실행 자체가 없다. 7장 agent_execution·8장 order_approval_queue와 같은 판단이다.
--    대신 request_uid로 잇는다.
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_tool_call_log (
  id               BIGINT PRIMARY KEY AUTO_INCREMENT,
  request_uid      VARCHAR(64),
  execution_id     BIGINT,                         -- agent_execution.id. 직접 호출이면 NULL
  agent_id         VARCHAR(64)  NOT NULL,
  user_id          VARCHAR(64)  NOT NULL,
  tool_name        VARCHAR(128) NOT NULL,
  scope_json       JSON         NOT NULL,          -- 호출 시점에 검사한 scope
  scope_pass       BOOLEAN      NOT NULL,
  params_hash      VARCHAR(64),                    -- 인자도 본문 대신 해시로 남긴다
  result_summary   TEXT,
  duration_ms      INT,
  error_message    TEXT,
  created_at       DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_atc_agent (agent_id),
  INDEX idx_atc_tool (tool_name),
  INDEX idx_atc_user (user_id),
  INDEX idx_atc_uid (request_uid),
  INDEX idx_atc_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------
-- 5. 감사 기록 전용 계정
--    세 테이블에 INSERT와 SELECT만 준다. UPDATE·DELETE는 아예 부여하지 않는다.
--    "권한을 뺏는" 게 아니라 "처음부터 주지 않는" 것이라 REVOKE도 필요 없다.
--
--    왜 트리거가 아니라 계정인가.
--    ① 트리거는 root로 붙으면 DROP TRIGGER 한 줄에 사라진다. 통제 강도가 더 약하다.
--    ② MariaDB는 트리거를 datadir의 .TRG 파일로 저장하는데, 윈도우 호스트 폴더를
--       bind mount한 컨테이너에서는 파일 권한 설정이 막혀 생성 자체가 실패한다.
--       통제가 실행 환경에 좌우되면 통제가 아니다.
--    ③ 운영에서 실제로 쓰는 방식이 이쪽이다 (부록 A §6 감사 로그 보관).
--
--    [주의] root로 접속하면 여전히 UPDATE가 된다. 감사 기록을 쓰는 경로가 이 계정만
--           쓰도록 애플리케이션을 나눠야 의미가 생긴다 — 그래서 Spring Boot와 FastAPI
--           양쪽에 감사 전용 커넥션을 따로 뒀다. 8장에서 조회 키와 시스템 키를 나눈 것과
--           같은 사상이다. 운영에서는 애플리케이션 계정에서도 이 세 테이블의
--           UPDATE·DELETE를 회수한다.
-- ----------------------------------------------------------------
CREATE USER IF NOT EXISTS 'quantx_audit'@'%' IDENTIFIED BY 'audit-only-pass';

GRANT INSERT, SELECT ON quantx.audit_log           TO 'quantx_audit'@'%';
GRANT INSERT, SELECT ON quantx.guardrail_event     TO 'quantx_audit'@'%';
GRANT INSERT, SELECT ON quantx.agent_tool_call_log TO 'quantx_audit'@'%';

FLUSH PRIVILEGES;