// =============================================================================
// setup_neo4j.cypher  –  Section 3.2  Post-import Neo4j setup
// Run in Neo4j Browser or cypher-shell after starting Neo4j.
// =============================================================================

// Unique constraints on the three business IDs
CREATE CONSTRAINT con_customer_id IF NOT EXISTS
    FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE;

CREATE CONSTRAINT con_account_id IF NOT EXISTS
    FOR (a:Account) REQUIRE a.account_id IS UNIQUE;

CREATE CONSTRAINT con_device_id IF NOT EXISTS
    FOR (d:Device) REQUIRE d.device_id IS UNIQUE;

// Range index on TRANSFER.occurred_at for time-window queries
CREATE INDEX idx_transfer_occurred IF NOT EXISTS
    FOR ()-[t:TRANSFER]-() ON (t.occurred_at);

// Wait for indexes to come online
CALL db.awaitIndexes(300);

// ─────────────────────────────────────────────────────────────────────────────
// Verification  (Section 3.2 step 4)
// ─────────────────────────────────────────────────────────────────────────────

// Node counts
MATCH (c:Customer) RETURN 'Customer' AS label, count(c) AS n
UNION ALL MATCH (a:Account)  RETURN 'Account'  AS label, count(a) AS n
UNION ALL MATCH (d:Device)   RETURN 'Device'   AS label, count(d) AS n;

// Relationship counts
MATCH ()-[r:OWNS]->()        RETURN 'OWNS'        AS type, count(r) AS n
UNION ALL MATCH ()-[r:USED_DEVICE]->() RETURN 'USED_DEVICE' AS type, count(r) AS n
UNION ALL MATCH ()-[r:TRANSFER]->()    RETURN 'TRANSFER'    AS type, count(r) AS n;

// Account role breakdown
MATCH (a:Account) RETURN a.role AS role, count(a) AS n ORDER BY role;

// One owner per account check
MATCH (a:Account)
WITH a, COUNT { (c:Customer)-[:OWNS]->(a) } AS owner_count
WHERE owner_count <> 1
RETURN count(a) AS accounts_without_exactly_one_owner;  // should be 0

// Unique transfer_id check
MATCH (a)-[t:TRANSFER]->() 
WITH t.transfer_id AS tid, count(*) AS n WHERE n > 1
RETURN count(*) AS duplicate_transfer_ids;  // should be 0

// Transfer audit totals
MATCH ()-[t:TRANSFER]->()
RETURN count(t) AS total_transfers,
       min(t.occurred_at) AS earliest_occurred_at,
       max(t.occurred_at) AS latest_occurred_at,
       sum(t.amount_rwf)  AS sum_amount_rwf;
