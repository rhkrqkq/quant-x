USE quantx;

CREATE TABLE IF NOT EXISTS stock_master (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  ticker      VARCHAR(16)  NOT NULL UNIQUE,
  name_kr     VARCHAR(100) NOT NULL,
  name_en     VARCHAR(100),
  market      VARCHAR(16),
  sector      VARCHAR(64),
  industry    VARCHAR(64),
  active      BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_sm_market (market),
  INDEX idx_sm_sector (sector)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS market_data_sample (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  ticker       VARCHAR(16)  NOT NULL,
  trade_date   DATE         NOT NULL,
  open_price   DECIMAL(15,2),
  high_price   DECIMAL(15,2),
  low_price    DECIMAL(15,2),
  close_price  DECIMAL(15,2),
  volume       BIGINT,
  per_ratio    DECIMAL(8,2),
  pbr_ratio    DECIMAL(8,2),
  roe_ratio    DECIMAL(8,4),
  UNIQUE KEY uk_mds (ticker, trade_date),
  INDEX idx_mds_ticker (ticker),
  INDEX idx_mds_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;