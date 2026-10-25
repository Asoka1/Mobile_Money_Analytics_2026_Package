-- =============================================================================
-- schema.sql  –  Section 2.1  Define the five PostgreSQL tables
-- Run in psql:  \i schema.sql
-- =============================================================================

-- Time zone (Section 1.1)
SET timezone = 'Africa/Kigali';

-- =============================================================================
-- Drop in reverse dependency order (idempotent re-run)
-- =============================================================================
DROP TABLE IF EXISTS transfers       CASCADE;
DROP TABLE IF EXISTS account_devices CASCADE;
DROP TABLE IF EXISTS accounts        CASCADE;
DROP TABLE IF EXISTS devices         CASCADE;
DROP TABLE IF EXISTS customers       CASCADE;

-- =============================================================================
-- 1. customers
-- =============================================================================
CREATE TABLE customers (
    customer_id  INTEGER  NOT NULL,
    region       TEXT     NOT NULL,

    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);

-- =============================================================================
-- 2. devices
-- =============================================================================
CREATE TABLE devices (
    device_id    INTEGER  NOT NULL,
    access_type  TEXT     NOT NULL,

    CONSTRAINT pk_devices PRIMARY KEY (device_id)
);

-- =============================================================================
-- 3. accounts  (depends on customers)
-- =============================================================================
CREATE TABLE accounts (
    account_id   INTEGER  NOT NULL,
    customer_id  INTEGER  NOT NULL,
    role         TEXT     NOT NULL,

    CONSTRAINT pk_accounts  PRIMARY KEY (account_id),
    CONSTRAINT fk_acc_cust  FOREIGN KEY (customer_id)
                            REFERENCES customers (customer_id)
);

-- =============================================================================
-- 4. account_devices  (depends on accounts + devices)
-- =============================================================================
CREATE TABLE account_devices (
    account_id   INTEGER   NOT NULL,
    device_id    INTEGER   NOT NULL,
    first_day    SMALLINT  NOT NULL,
    last_day     SMALLINT  NOT NULL,
    observations INTEGER   NOT NULL,

    CONSTRAINT pk_acct_dev    PRIMARY KEY (account_id, device_id),
    CONSTRAINT fk_ad_account  FOREIGN KEY (account_id)
                              REFERENCES accounts (account_id),
    CONSTRAINT fk_ad_device   FOREIGN KEY (device_id)
                              REFERENCES devices  (device_id),
    CONSTRAINT chk_ad_obs     CHECK (observations > 0),
    CONSTRAINT chk_ad_days    CHECK (0 <= first_day AND first_day <= last_day
                                     AND last_day <= 29)
);

-- =============================================================================
-- 5. transfers  (depends on accounts ×2)
-- =============================================================================
CREATE TABLE transfers (
    transfer_id  BIGINT   NOT NULL,
    sender_id    INTEGER  NOT NULL,
    receiver_id  INTEGER  NOT NULL,
    occurred_at  BIGINT   NOT NULL,
    amount_rwf   INTEGER  NOT NULL,

    CONSTRAINT pk_transfers   PRIMARY KEY (transfer_id),
    CONSTRAINT fk_t_sender    FOREIGN KEY (sender_id)
                              REFERENCES accounts (account_id),
    CONSTRAINT fk_t_receiver  FOREIGN KEY (receiver_id)
                              REFERENCES accounts (account_id),
    CONSTRAINT chk_t_amount   CHECK (amount_rwf > 0)
);

-- =============================================================================
-- End of Section 2.1 Table and Constraint Definitions
-- (Section 2.2 secondary indexes are defined in indexes.sql and applied post-load)
-- =============================================================================
\echo 'Section 2.1: Schema, primary keys, foreign keys and check constraints created.'
