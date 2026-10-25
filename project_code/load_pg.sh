#!/usr/bin/env bash
# =============================================================================
# load_pg.sh  –  Section 2.2  Bulk-load CSVs into PostgreSQL
#
# Usage: bash load_pg.sh <db_name> <csv_dir>
#   e.g. bash load_pg.sh mobile_money /path/to/project_code
#
# Requirements: psql on PATH, schema.sql already applied.
# =============================================================================

set -euo pipefail

DB="${1:-mobile_money}"
CSV_DIR="${2:-$(dirname "$0")}"

PSQL="psql -d $DB -v ON_ERROR_STOP=1"

echo "=== Loading into database: $DB ==="
echo "=== CSV directory: $CSV_DIR ==="

# Ensure schema is applied first
$PSQL -f "$(dirname "$0")/schema.sql"

echo ""
echo "--- Bulk loading (COPY) ---"

time $PSQL -c "\copy customers       FROM '${CSV_DIR}/customers.csv'       CSV HEADER"
time $PSQL -c "\copy devices         FROM '${CSV_DIR}/devices.csv'         CSV HEADER"
time $PSQL -c "\copy accounts        FROM '${CSV_DIR}/accounts.csv'        CSV HEADER"
time $PSQL -c "\copy account_devices FROM '${CSV_DIR}/account_devices.csv' CSV HEADER"
time $PSQL -c "\copy transfers       FROM '${CSV_DIR}/transfers.csv'       CSV HEADER"

echo ""
echo "--- Section 2.2: Creating indexes and running ANALYZE ---"
time $PSQL -f "$(dirname "$0")/indexes.sql"

echo ""
echo "=== Row count verification ==="
$PSQL -c "
SELECT 'customers'       AS tbl, COUNT(*) AS n FROM customers
UNION ALL SELECT 'accounts',       COUNT(*) FROM accounts
UNION ALL SELECT 'devices',        COUNT(*) FROM devices
UNION ALL SELECT 'account_devices',COUNT(*) FROM account_devices
UNION ALL SELECT 'transfers',      COUNT(*) FROM transfers;
"

echo ""
echo "=== Account roles ==="
$PSQL -c "SELECT role, COUNT(*) FROM accounts GROUP BY role ORDER BY role;"

echo ""
echo "=== Transfer audit totals ==="
$PSQL -c "
SELECT COUNT(*) AS transfer_count,
       MIN(occurred_at) AS earliest_occurred_at,
       MAX(occurred_at) AS latest_occurred_at,
       SUM(amount_rwf)  AS sum_amount_rwf
FROM transfers;
"

echo ""
echo "=== Database sizes (GB = 10^9 bytes) ==="
$PSQL -c "
SELECT pg_size_pretty(pg_database_size('$DB')) AS db_total_size;
"
$PSQL -c "
SELECT relname AS table_name,
       pg_size_pretty(pg_total_relation_size(oid)) AS total_size,
       pg_size_pretty(pg_relation_size(oid))       AS table_size,
       pg_size_pretty(pg_total_relation_size(oid)
                    - pg_relation_size(oid))        AS index_size
FROM pg_class
WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace
ORDER BY pg_total_relation_size(oid) DESC;
"

echo "=== Load complete ==="
