-- =============================================================================
-- indexes.sql  –  Section 2.2  Indexes and statistics for PostgreSQL
-- Run after loading data:  \i indexes.sql
-- =============================================================================

SET maintenance_work_mem = '1GB';
SET max_parallel_maintenance_workers = 4;

\echo '--- Creating index idx_acc_cust on accounts (customer_id, account_id) ---'
CREATE INDEX IF NOT EXISTS idx_acc_cust ON accounts (customer_id, account_id);

\echo '--- Creating index idx_ad_dev on account_devices (device_id, account_id) ---'
CREATE INDEX IF NOT EXISTS idx_ad_dev ON account_devices (device_id, account_id);

\echo '--- Creating covering index idx_t_sender on transfers (sender_id, occurred_at) INCLUDE (receiver_id, amount_rwf, transfer_id) ---'
CREATE INDEX IF NOT EXISTS idx_t_sender ON transfers (sender_id, occurred_at)
    INCLUDE (receiver_id, amount_rwf, transfer_id);

\echo '--- Creating covering index idx_t_receiver on transfers (receiver_id, occurred_at) INCLUDE (sender_id, amount_rwf, transfer_id) ---'
CREATE INDEX IF NOT EXISTS idx_t_receiver ON transfers (receiver_id, occurred_at)
    INCLUDE (sender_id, amount_rwf, transfer_id);

\echo '--- Creating BRIN index idx_t_brin on transfers USING brin (occurred_at) ---'
CREATE INDEX IF NOT EXISTS idx_t_brin ON transfers USING brin (occurred_at);

\echo '--- Running ANALYZE ---'
ANALYZE;
