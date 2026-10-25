"""
run_queries.py  –  Sections 4 & 5  Run Q1–Q7 for all review sets and print results.
Screenshots from this script satisfy all "six paired results" requirements.
"""

import sys
import json
from db_connect import pg_connect, neo_driver, run_pg, run_neo
import queries as Q

SETS = list(Q.REVIEW_SETS.keys())   # A, B, C, D, E, F

def header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

# ─────────────────────────────────────────────────────────────────────────────
# Q1 – Account activity in one hour
# ─────────────────────────────────────────────────────────────────────────────
header("Q1  Account activity in specified hour")
print(f"{'Set':4} {'Account':>8} {'Date':>4} {'PG tx_count':>12} {'PG total_rwf':>14} {'NEO tx_count':>12} {'NEO total_rwf':>14}")
for s in SETS:
    p = Q.q1_params(s)
    pg  = run_pg(Q.Q1_SQL, p)
    neo = run_neo(Q.Q1_CYPHER, p)
    pg_cnt, pg_sum   = pg[0]
    neo_row          = neo[0]
    neo_cnt, neo_sum = neo_row['tx_count'], neo_row['total_rwf']
    acct, _, day = Q.REVIEW_SETS[s]
    print(f"{s:4} {acct:>8} {day:>4} {pg_cnt:>12,} {pg_sum:>14,} {neo_cnt:>12,} {neo_sum:>14,}")

# ─────────────────────────────────────────────────────────────────────────────
# Q2 – Daily activity
# ─────────────────────────────────────────────────────────────────────────────
header("Q2  Daily activity (full month)")
p    = Q.q2_params()
pg2  = run_pg(Q.Q2_SQL,    p)
neo2 = run_neo(Q.Q2_CYPHER, p)
print(f"{'Day':12} {'PG count':>10} {'PG total_rwf':>16} {'NEO count':>10} {'NEO total_rwf':>16}")
for pg_row, neo_row in zip(pg2, neo2):
    d, pc, ps = pg_row
    print(f"{d:12} {pc:>10,} {ps:>16,} {neo_row['tx_count']:>10,} {neo_row['total_rwf']:>16,}")
pg_total  = sum(r[1] for r in pg2)
neo_total = sum(r['tx_count'] for r in neo2)
print(f"{'TOTALS':12} {pg_total:>10,}")

# ─────────────────────────────────────────────────────────────────────────────
# Q3 – Shared devices
# ─────────────────────────────────────────────────────────────────────────────
header("Q3  Shared devices")
for s in SETS:
    p   = Q.q3_params(s)
    pg  = run_pg(Q.Q3_SQL,    p)
    neo = run_neo(Q.Q3_CYPHER, p)
    acct, _, _ = Q.REVIEW_SETS[s]
    print(f"Set {s} (account {acct}): PG={len(pg)} rows  NEO={len(neo)} rows")
    if pg:
        print(f"  First row PG:  {pg[0]}")
        print(f"  First row NEO: {neo[0] if neo else 'none'}")

# ─────────────────────────────────────────────────────────────────────────────
# Q4 – Ownership and device network
# ─────────────────────────────────────────────────────────────────────────────
header("Q4  Ownership and device network")
DEPTHS = [4, 6, 8, 10]
for s in ['A', 'B', 'C', 'D', 'E', 'F']:
    for d in DEPTHS:
        p   = Q.q4_params(s, d)
        pg  = run_pg(Q.Q4_SQL,    p)
        neo = run_neo(Q.Q4_CYPHER, p)
        pg_total  = sum(r[1] for r in pg)
        neo_total = sum(r['reached_accounts'] for r in neo)
        acct, _, _ = Q.REVIEW_SETS[s]
        print(f"  Set {s} (acct {acct:>6}) depth {d:>2}: PG={pg_total:>7,}  NEO={neo_total:>7,}")

# ─────────────────────────────────────────────────────────────────────────────
# Q5 – Rapid onward payments
# ─────────────────────────────────────────────────────────────────────────────
header("Q5  Rapid onward payments")
for s in SETS:
    p   = Q.q5_params(s)
    pg  = run_pg(Q.Q5_SQL,    p)
    neo = run_neo(Q.Q5_CYPHER, p)
    acct, _, day = Q.REVIEW_SETS[s]
    print(f"Set {s} (account {acct}, day {day}): PG={len(pg)} chains  NEO={len(neo)} chains")
    if pg:
        print(f"  Example chain: {pg[0]}")

# ─────────────────────────────────────────────────────────────────────────────
# Q6 – Circular payments
# ─────────────────────────────────────────────────────────────────────────────
header("Q6  Circular payments")
for s in SETS:
    p   = Q.q6_params(s)
    pg  = run_pg(Q.Q6_SQL,    p)
    neo = run_neo(Q.Q6_CYPHER, p)
    acct, _, day = Q.REVIEW_SETS[s]
    print(f"Set {s} (account {acct}, day {day}): PG={len(pg)} cycles  NEO={len(neo)} cycles")
    if pg:
        print(f"  Example cycle: {pg[0]}")

# ─────────────────────────────────────────────────────────────────────────────
# Q7 – Shortest transfer connection
# ─────────────────────────────────────────────────────────────────────────────
header("Q7  Shortest transfer connection")
BOUNDS = [4, 6]
for s in SETS:
    acct, dest, _ = Q.REVIEW_SETS[s]
    for bound in BOUNDS:
        p     = Q.q7_params(s, bound)
        pg_l  = run_pg(Q.Q7_SQL_LENGTH, p)
        neo_l = run_neo(Q.Q7_CYPHER_LENGTH, p)
        pg_min  = pg_l[0][0]  if pg_l  else None
        neo_min = neo_l[0]['min_length'] if neo_l else None
        print(f"  Set {s} ({acct}->{dest}) bound={bound}: PG={pg_min}  NEO={neo_min}")
        if pg_min is not None:
            path_p = dict(p)
            path_p['bound'] = pg_min
            pg_p  = run_pg(Q.Q7_SQL_PATH, path_p)
            neo_p = run_neo(Q.Q7_CYPHER_PATH, path_p)
            print(f"    PG path:  {pg_p[0] if pg_p else 'none'}")
            print(f"    NEO path: {neo_p[0] if neo_p else 'none'}")

print()
print("All queries complete.")
