
-- CRITICAL PRIORITY INDEXES (Execute first, during maintenance window)
BEGIN;

-- Phase 1: Critical Performance Tables
ALTER TABLE "FE_DMV_ALL" ADD CONSTRAINT pk_fe_dmv_all PRIMARY KEY (slug, timestamp);
ALTER TABLE "1K_coins_ohlcv" ADD CONSTRAINT pk_1k_coins_ohlcv PRIMARY KEY (slug, timestamp);

CREATE INDEX CONCURRENTLY idx_fe_dmv_all_timestamp ON "FE_DMV_ALL" (timestamp DESC);
CREATE INDEX CONCURRENTLY idx_fe_dmv_all_slug ON "FE_DMV_ALL" (slug);
CREATE INDEX CONCURRENTLY idx_1k_ohlcv_timestamp ON "1K_coins_ohlcv" (timestamp DESC);
CREATE INDEX CONCURRENTLY idx_1k_ohlcv_volume ON "1K_coins_ohlcv" (volume DESC);
CREATE INDEX CONCURRENTLY idx_1k_ohlcv_slug ON "1K_coins_ohlcv" (slug);

COMMIT;

-- Phase 2: Signal Tables (Execute after Phase 1 success)
BEGIN;

ALTER TABLE "FE_MOMENTUM_SIGNALS" ADD CONSTRAINT pk_fe_momentum_signals PRIMARY KEY (slug, timestamp);
ALTER TABLE "FE_OSCILLATORS_SIGNALS" ADD CONSTRAINT pk_fe_oscillators_signals PRIMARY KEY (slug, timestamp);
ALTER TABLE "FE_RATIOS_SIGNALS" ADD CONSTRAINT pk_fe_ratios_signals PRIMARY KEY (slug, timestamp);

CREATE INDEX CONCURRENTLY idx_fe_momentum_signals_timestamp ON "FE_MOMENTUM_SIGNALS" (timestamp DESC);
CREATE INDEX CONCURRENTLY idx_fe_oscillators_signals_timestamp ON "FE_OSCILLATORS_SIGNALS" (timestamp DESC);
CREATE INDEX CONCURRENTLY idx_fe_ratios_signals_timestamp ON "FE_RATIOS_SIGNALS" (timestamp DESC);

COMMIT;

-- Update table statistics after index creation
ANALYZE;
