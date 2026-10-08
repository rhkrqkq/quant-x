USE quantx;

-- 종목 마스터 (요약 6개)
INSERT IGNORE INTO stock_master (ticker, name_kr, name_en, market, sector, industry, active) VALUES
  ('005930','삼성전자','Samsung Electronics','KOSPI','IT','Semiconductor',TRUE),
  ('000660','SK하이닉스','SK Hynix','KOSPI','IT','Semiconductor',TRUE),
  ('035720','카카오','Kakao','KOSPI','Comm.','Internet',TRUE),
  ('035420','NAVER','Naver','KOSPI','Comm.','Internet',TRUE),
  ('005380','현대차','Hyundai Motor','KOSPI','Industrials','Auto',TRUE),
  ('051910','LG화학','LG Chem','KOSPI','Materials','Chemicals',TRUE);

-- 시세 샘플 (실행일 기준 최근 3일치, 더미값)
-- 날짜를 CURDATE() 기준으로 계산하므로 수업 당일 실행하면 항상 "최근 데이터"가 된다.
INSERT IGNORE INTO market_data_sample
  (ticker, trade_date, open_price, high_price, low_price, close_price, volume, per_ratio, pbr_ratio, roe_ratio)
VALUES
  ('005930', CURDATE() - INTERVAL 3 DAY,  78000,  79500,  77800,  79200, 12300000, 18.5, 1.40, 0.082),
  ('005930', CURDATE() - INTERVAL 2 DAY,  79200,  80500,  79000,  80100, 14200000, 18.7, 1.42, 0.082),
  ('005930', CURDATE() - INTERVAL 1 DAY,  80100,  80800,  79900,  80500,  9800000, 18.8, 1.43, 0.082),
  ('000660', CURDATE() - INTERVAL 3 DAY, 180000, 182000, 179000, 181000,  7800000, 12.3, 1.80, 0.105),
  ('000660', CURDATE() - INTERVAL 2 DAY, 181000, 184000, 180500, 183500,  8200000, 12.5, 1.82, 0.105),
  ('000660', CURDATE() - INTERVAL 1 DAY, 183500, 185500, 182000, 184700,  6900000, 12.6, 1.83, 0.105);
-- 운영 환경에서는 yf_backfill 스크립트로 90일 적재 (위 샘플 데이터 삭제)