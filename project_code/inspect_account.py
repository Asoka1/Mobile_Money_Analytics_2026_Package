"""
inspect_account.py  –  Section 3.3
Trace one loaded account to its owner, a device and an outgoing transfer
using both SQL JOINs and Cypher MATCH.  Demonstrates the correspondence
between foreign-key relationships and graph edges.

Usage:  python inspect_account.py [account_id]
Default account: 998 (Set A review account)
"""

import sys
from db_connect import pg_connect, neo_driver, run_pg, run_neo

ACCOUNT_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 998

# ── SQL version ──────────────────────────────────────────────────────────────
SQL = """
SELECT a.account_id,
       a.role,
       c.customer_id,
       c.region,
       ad.device_id,
       d.access_type,
       ad.first_day,
       ad.last_day,
       ad.observations,
       t.transfer_id,
       t.receiver_id,
       t.occurred_at,
       t.amount_rwf
FROM   accounts        a
JOIN   customers       c  ON c.customer_id = a.customer_id
JOIN   account_devices ad ON ad.account_id = a.account_id
JOIN   devices         d  ON d.device_id   = ad.device_id
JOIN   transfers       t  ON t.sender_id   = a.account_id
WHERE  a.account_id = %(account)s
LIMIT  1;
"""

# ── Cypher version ───────────────────────────────────────────────────────────
CYPHER = """
MATCH  (c:Customer)-[:OWNS]->(a:Account {account_id: $account})
       -[:USED_DEVICE]->(d:Device)
MATCH  (a)-[t:TRANSFER]->()
RETURN a.account_id  AS account_id,
       a.role        AS role,
       c.customer_id AS customer_id,
       c.region      AS region,
       d.device_id   AS device_id,
       d.access_type AS access_type,
       t.transfer_id AS transfer_id,
       t.occurred_at AS occurred_at,
       t.amount_rwf  AS amount_rwf
LIMIT  1;
"""

print(f"=== Inspect account {ACCOUNT_ID} ===\n")

print("--- SQL JOIN result ---")
pg_rows = run_pg(SQL, {'account': ACCOUNT_ID})
if pg_rows:
    r = pg_rows[0]
    print(f"  account_id  : {r[0]}")
    print(f"  role        : {r[1]}")
    print(f"  customer_id : {r[2]}")
    print(f"  region      : {r[3]}")
    print(f"  device_id   : {r[4]}")
    print(f"  access_type : {r[5]}")
    print(f"  first_day   : {r[6]}")
    print(f"  last_day    : {r[7]}")
    print(f"  observations: {r[8]}")
    print(f"  transfer_id : {r[9]}")
    print(f"  receiver_id : {r[10]}")
    print(f"  occurred_at : {r[11]}")
    print(f"  amount_rwf  : {r[12]:,}")
else:
    print("  No result.")

print("\n--- Cypher MATCH result ---")
neo_rows = run_neo(CYPHER, {'account': ACCOUNT_ID})
if neo_rows:
    r = neo_rows[0]
    for k, v in r.items():
        print(f"  {k:14s}: {v:,}" if isinstance(v, int) else f"  {k:14s}: {v}")
else:
    print("  No result.")

print("""
--- Explanation ---
Foreign keys in SQL <-> Graph relationships in Neo4j:
  accounts.customer_id -> customers.customer_id   ≡   (:Customer)-[:OWNS]->(:Account)
  account_devices.device_id -> devices.device_id  ≡   (:Account)-[:USED_DEVICE]->(:Device)
  transfers.sender_id   -> accounts.account_id    ≡   (:Account)-[:TRANSFER]->(:Account)
  transfers.receiver_id -> accounts.account_id    ≡   (:Account)-[:TRANSFER]->(:Account)

If repeated payments between the same accounts were collapsed to one edge:
  - transfer_id, occurred_at, and amount_rwf would be lost (or overwritten).
  - Time-ordered analysis (Q5/Q6) and audit totals (Q2) would be impossible.
  - Direction could be preserved but individual events could not.
""")
