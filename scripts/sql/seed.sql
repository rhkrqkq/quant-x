-- ============================================================
-- 본 과정 3장 시점 시드 데이터 — 사용자 2명 + 권한(Scope) 4종
-- 원본: 강의자료 03장 §8.2
-- 비밀번호: 두 계정 모두 "password" (BCrypt 해시 적용됨)
-- ============================================================

USE quantx;

-- ----------------------------------------------------------------
-- 1. 사용자 2명
--    analyst_001 : JUNIOR_ANALYST (주니어 김)
--    senior_001  : SENIOR_MANAGER (시니어 이)
-- ----------------------------------------------------------------
INSERT INTO users (user_id, password_hash, name, email, role, active)
VALUES
  ('analyst_001',
   '$2a$10$ScFGZ9H9R8ZIf9C10khMs.oKGihNwNxtiRN.X.5hkDF/Gr6ZTVJh6',
   '주니어 김', 'jr@example.com', 'JUNIOR_ANALYST', TRUE),
  ('senior_001',
   '$2a$10$ScFGZ9H9R8ZIf9C10khMs.oKGihNwNxtiRN.X.5hkDF/Gr6ZTVJh6',
   '시니어 이', 'sr@example.com', 'SENIOR_MANAGER', TRUE)
ON DUPLICATE KEY UPDATE
  password_hash = VALUES(password_hash),
  name = VALUES(name),
  email = VALUES(email),
  role = VALUES(role),
  active = VALUES(active);

-- ----------------------------------------------------------------
-- 2. Scope 부여
--    공통 (analyst_001, senior_001) : RAG_READ, MARKET_DATA_READ, REPORT_READ
--    senior_001 전용                : REPORT_WRITE
-- ----------------------------------------------------------------
INSERT IGNORE INTO user_scopes (user_id, scope, granted_at)
SELECT id, 'RAG_READ', NOW(6)
FROM users
WHERE user_id IN ('analyst_001', 'senior_001');

INSERT IGNORE INTO user_scopes (user_id, scope, granted_at)
SELECT id, 'MARKET_DATA_READ', NOW(6)
FROM users
WHERE user_id IN ('analyst_001', 'senior_001');

INSERT IGNORE INTO user_scopes (user_id, scope, granted_at)
SELECT id, 'REPORT_READ', NOW(6)
FROM users
WHERE user_id IN ('analyst_001', 'senior_001');

INSERT IGNORE INTO user_scopes (user_id, scope, granted_at)
SELECT id, 'REPORT_WRITE', NOW(6)
FROM users
WHERE user_id = 'senior_001';
