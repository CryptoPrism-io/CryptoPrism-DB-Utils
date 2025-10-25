-- Create timestamp index on FE_FEAR_GREED_CMC table to fix performance regression
-- This will enable index-based sorting instead of sequential scan + sort

CREATE INDEX CONCURRENTLY idx_fe_fear_greed_cmc_timestamp_desc
ON "FE_FEAR_GREED_CMC" (timestamp DESC);

-- Add primary key constraint using timestamp (assuming timestamps are unique)
-- If timestamps are not unique, this will fail and we'll need a composite key
ALTER TABLE "FE_FEAR_GREED_CMC"
ADD CONSTRAINT pk_fe_fear_greed_cmc_timestamp
PRIMARY KEY (timestamp);

-- Alternative: If timestamps might not be unique, use a composite primary key
-- ALTER TABLE "FE_FEAR_GREED_CMC"
-- ADD CONSTRAINT pk_fe_fear_greed_cmc_timestamp_sentiment
-- PRIMARY KEY (timestamp, sentiment);