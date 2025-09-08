-- CryptoPrism Dashboard - ETL Tracking Setup
-- Creates database tables and functions for ETL job monitoring

-- Create ETL runs tracking table
CREATE TABLE IF NOT EXISTS etl_runs (
    run_id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'running',
    rows_processed INTEGER DEFAULT 0,
    memory_used_mb INTEGER DEFAULT 0,
    error_message TEXT,
    duration_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_etl_runs_job_name ON etl_runs(job_name);
CREATE INDEX IF NOT EXISTS idx_etl_runs_start_time ON etl_runs(start_time);
CREATE INDEX IF NOT EXISTS idx_etl_runs_status ON etl_runs(status);

-- Create ETL summary stats table for quick dashboard queries
CREATE TABLE IF NOT EXISTS etl_job_stats (
    job_name VARCHAR(255) PRIMARY KEY,
    total_runs INTEGER DEFAULT 0,
    successful_runs INTEGER DEFAULT 0,
    failed_runs INTEGER DEFAULT 0,
    avg_duration_minutes DECIMAL(10,2) DEFAULT 0,
    last_run_time TIMESTAMP WITH TIME ZONE,
    last_run_status VARCHAR(50),
    total_rows_processed BIGINT DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Function to start ETL job tracking
CREATE OR REPLACE FUNCTION log_etl_start(job_name_param VARCHAR(255))
RETURNS INTEGER AS $$
DECLARE
    new_run_id INTEGER;
BEGIN
    INSERT INTO etl_runs (job_name, start_time, status)
    VALUES (job_name_param, CURRENT_TIMESTAMP, 'running')
    RETURNING run_id INTO new_run_id;
    
    -- Initialize or update job stats
    INSERT INTO etl_job_stats (job_name, total_runs, last_run_time)
    VALUES (job_name_param, 1, CURRENT_TIMESTAMP)
    ON CONFLICT (job_name) 
    DO UPDATE SET 
        total_runs = etl_job_stats.total_runs + 1,
        last_run_time = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN new_run_id;
END;
$$ LANGUAGE plpgsql;

-- Function to complete ETL job tracking
CREATE OR REPLACE FUNCTION log_etl_complete(
    run_id_param INTEGER,
    status_param VARCHAR(50),
    rows_processed_param INTEGER DEFAULT 0,
    memory_used_param INTEGER DEFAULT 0,
    error_message_param TEXT DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    job_name_var VARCHAR(255);
    duration_var INTEGER;
BEGIN
    -- Update the ETL run record
    UPDATE etl_runs 
    SET 
        end_time = CURRENT_TIMESTAMP,
        status = status_param,
        rows_processed = rows_processed_param,
        memory_used_mb = memory_used_param,
        error_message = error_message_param,
        duration_minutes = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - start_time)) / 60
    WHERE run_id = run_id_param
    RETURNING job_name, duration_minutes INTO job_name_var, duration_var;
    
    -- Update job statistics
    UPDATE etl_job_stats 
    SET 
        successful_runs = CASE WHEN status_param = 'success' THEN successful_runs + 1 ELSE successful_runs END,
        failed_runs = CASE WHEN status_param = 'failed' THEN failed_runs + 1 ELSE failed_runs END,
        last_run_status = status_param,
        total_rows_processed = total_rows_processed + COALESCE(rows_processed_param, 0),
        avg_duration_minutes = (
            SELECT AVG(duration_minutes) 
            FROM etl_runs 
            WHERE job_name = job_name_var AND status IN ('success', 'failed')
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE job_name = job_name_var;
END;
$$ LANGUAGE plpgsql;

-- Create data quality tracking table
CREATE TABLE IF NOT EXISTS data_quality_checks (
    check_id SERIAL PRIMARY KEY,
    check_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    check_type VARCHAR(100) NOT NULL, -- 'primary_key', 'null_check', 'duplicate_check', etc.
    expected_count INTEGER,
    actual_count INTEGER,
    status VARCHAR(50) DEFAULT 'pending', -- 'passed', 'failed', 'warning'
    error_details TEXT,
    check_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for data quality checks
CREATE INDEX IF NOT EXISTS idx_data_quality_table_name ON data_quality_checks(table_name);
CREATE INDEX IF NOT EXISTS idx_data_quality_check_time ON data_quality_checks(check_time);
CREATE INDEX IF NOT EXISTS idx_data_quality_status ON data_quality_checks(status);

-- Function to log data quality check
CREATE OR REPLACE FUNCTION log_data_quality_check(
    check_name_param VARCHAR(255),
    table_name_param VARCHAR(255),
    check_type_param VARCHAR(100),
    expected_count_param INTEGER,
    actual_count_param INTEGER,
    status_param VARCHAR(50),
    error_details_param TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    new_check_id INTEGER;
BEGIN
    INSERT INTO data_quality_checks (
        check_name, table_name, check_type, 
        expected_count, actual_count, status, error_details
    )
    VALUES (
        check_name_param, table_name_param, check_type_param,
        expected_count_param, actual_count_param, status_param, error_details_param
    )
    RETURNING check_id INTO new_check_id;
    
    RETURN new_check_id;
END;
$$ LANGUAGE plpgsql;

-- Insert sample data for testing (optional)
INSERT INTO etl_runs (job_name, start_time, end_time, status, rows_processed, duration_minutes)
VALUES 
    ('gcp_dmv_rat', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP - INTERVAL '1 hour 45 minutes', 'success', 1000, 15),
    ('gcp_dmv_core', CURRENT_TIMESTAMP - INTERVAL '1 hour', CURRENT_TIMESTAMP - INTERVAL '45 minutes', 'success', 1500, 15),
    ('gcp_dmv_mom', CURRENT_TIMESTAMP - INTERVAL '30 minutes', CURRENT_TIMESTAMP - INTERVAL '25 minutes', 'success', 800, 5)
ON CONFLICT DO NOTHING;

-- Update job stats for sample data
INSERT INTO etl_job_stats (job_name, total_runs, successful_runs, failed_runs, last_run_time, last_run_status, total_rows_processed)
VALUES 
    ('gcp_dmv_rat', 1, 1, 0, CURRENT_TIMESTAMP - INTERVAL '1 hour 45 minutes', 'success', 1000),
    ('gcp_dmv_core', 1, 1, 0, CURRENT_TIMESTAMP - INTERVAL '45 minutes', 'success', 1500),
    ('gcp_dmv_mom', 1, 1, 0, CURRENT_TIMESTAMP - INTERVAL '25 minutes', 'success', 800)
ON CONFLICT (job_name) DO NOTHING;

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON etl_runs TO your_user;
-- GRANT ALL PRIVILEGES ON etl_job_stats TO your_user;
-- GRANT ALL PRIVILEGES ON data_quality_checks TO your_user;

-- Create view for dashboard queries
CREATE OR REPLACE VIEW etl_dashboard_summary AS
SELECT 
    COUNT(*) as total_runs,
    COUNT(*) FILTER (WHERE status = 'success') as successful_runs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_runs,
    COUNT(*) FILTER (WHERE status = 'running') as running_runs,
    AVG(duration_minutes) FILTER (WHERE status IN ('success', 'failed')) as avg_duration,
    MAX(start_time) as last_run_time,
    SUM(rows_processed) as total_rows_processed
FROM etl_runs
WHERE start_time >= CURRENT_DATE - INTERVAL '7 days';

COMMENT ON TABLE etl_runs IS 'Tracks ETL job executions with timing and status information';
COMMENT ON TABLE etl_job_stats IS 'Aggregated statistics per ETL job for dashboard performance';
COMMENT ON TABLE data_quality_checks IS 'Data quality validation results and checks';
COMMENT ON FUNCTION log_etl_start IS 'Starts ETL job tracking and returns run_id';
COMMENT ON FUNCTION log_etl_complete IS 'Completes ETL job tracking with status and metrics';

-- Print setup completion message
DO $$ 
BEGIN 
    RAISE NOTICE 'CryptoPrism ETL tracking setup completed successfully!';
    RAISE NOTICE 'Tables created: etl_runs, etl_job_stats, data_quality_checks';
    RAISE NOTICE 'Functions created: log_etl_start(), log_etl_complete(), log_data_quality_check()';
    RAISE NOTICE 'Dashboard view created: etl_dashboard_summary';
    RAISE NOTICE 'Sample data inserted for testing';
END $$;