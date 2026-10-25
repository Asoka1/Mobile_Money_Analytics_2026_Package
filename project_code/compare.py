"""
compare.py  –  Section 6.1  Correctness comparison program (61 cases)
Runs Q1–Q7 on both engines, normalises output, and reports PASS/FAIL.

Also includes independent verification of:
  - one device overlap (Q3) against CSV rows
  - one chain/cycle (Q5/Q6) against CSV rows
"""

import csv
import math
import os
import sys

from db_connect import pg_connect, neo_driver, run_pg, run_neo
import queries as Q

SRC_DIR = os.path.dirname(os.path.abspath(__file__))

# ── normalise helpers ────────────────────────────────────────────────────────
def norm_int(v):
    if v is None:
        return None
    return int(v)

def norm_row(row):
    """Convert all values to int where possible; leave strings."""
    out = []
    for v in row:
        if v is None:
            out.append(None)
        else:
            try:
                out.append(int(v))
            except (TypeError, ValueError):
                out.append(str(v))
    return tuple(out)

def sort_rows(rows):
    return sorted([norm_row(r) for r in rows])

def rows_from_pg(pg_rows):
    return sort_rows([tuple(r) for r in pg_rows])

def rows_from_neo(neo_rows):
    return sort_rows([tuple(v for v in r.values()) for r in neo_rows])


# ── result table ─────────────────────────────────────────────────────────────
results = []   # list of (case_id, label, status, pg_count, neo_count)

def check(case_id, label, pg_rows, neo_rows, key_fn=None):
    """Compare sorted pg vs neo rows; record PASS/FAIL."""
    pg_s  = sort_rows([tuple(r) for r in pg_rows])
    neo_s = sort_rows([tuple(v for v in r.values()) for r in neo_rows])
    ok    = (pg_s == neo_s)
    results.append((case_id, label, 'PASS' if ok else 'FAIL',
                    len(pg_rows), len(neo_rows)))
    if not ok:
        print(f"  MISMATCH {case_id} {label}")
        print(f"    PG  (first 3): {pg_s[:3]}")
        print(f"    NEO (first 3): {neo_s[:3]}")
    return ok


SETS  = list(Q.REVIEW_SETS.keys())
case  = 0

pg_conn = pg_connect()
driver  = neo_driver()

try:
    # ── Q1 (6 cases) ────────────────────────────────────────────────────────
    for s in SETS:
        case += 1
        p = Q.q1_params(s)
        pg  = run_pg(Q.Q1_SQL,    p, conn=pg_conn)
        neo = run_neo(Q.Q1_CYPHER, p, driver=driver)
        check(case, f"Q1-{s}", pg, neo)

    # ── Q2 (1 case) ─────────────────────────────────────────────────────────
    case += 1
    p   = Q.q2_params()
    pg2  = run_pg(Q.Q2_SQL,    p, conn=pg_conn)
    neo2 = run_neo(Q.Q2_CYPHER, p, driver=driver)
    check(case, "Q2-month", pg2, neo2)

    # ── Q3 (6 cases) ────────────────────────────────────────────────────────
    for s in SETS:
        case += 1
        p   = Q.q3_params(s)
        pg  = run_pg(Q.Q3_SQL,    p, conn=pg_conn)
        neo = run_neo(Q.Q3_CYPHER, p, driver=driver)
        check(case, f"Q3-{s}", pg, neo)

    # ── Q4 (24 cases: 6 sets × 4 depths) ────────────────────────────────────
    for s in SETS:
        for depth in [4, 6, 8, 10]:
            case += 1
            p   = Q.q4_params(s, depth)
            pg  = run_pg(Q.Q4_SQL,    p, conn=pg_conn)
            neo = run_neo(Q.Q4_CYPHER, p, driver=driver)
            check(case, f"Q4-{s}-d{depth}", pg, neo)

    # ── Q5 (6 cases) ────────────────────────────────────────────────────────
    for s in SETS:
        case += 1
        p   = Q.q5_params(s)
        pg  = run_pg(Q.Q5_SQL,    p, conn=pg_conn)
        neo = run_neo(Q.Q5_CYPHER, p, driver=driver)
        check(case, f"Q5-{s}", pg, neo)

    # ── Q6 (6 cases) ────────────────────────────────────────────────────────
    for s in SETS:
        case += 1
        p   = Q.q6_params(s)
        pg  = run_pg(Q.Q6_SQL,    p, conn=pg_conn)
        neo = run_neo(Q.Q6_CYPHER, p, driver=driver)
        check(case, f"Q6-{s}", pg, neo)

    # ── Q7 lengths (6 sets × 2 bounds = 12 cases) ────────────────────────────
    for s in SETS:
        for bound in [4, 6]:
            case += 1
            p    = Q.q7_params(s, bound)
            pg   = run_pg(Q.Q7_SQL_LENGTH, p, conn=pg_conn)
            neo  = run_neo(Q.Q7_CYPHER_LENGTH, p, driver=driver)
            check(case, f"Q7-len-{s}-b{bound}", pg, neo)

finally:
    pg_conn.close()
    driver.close()

# ── print summary table ──────────────────────────────────────────────────────
print()
print(f"{'#':>3}  {'Case':<22} {'Status':>6}  {'PG rows':>8}  {'NEO rows':>9}")
print("-" * 58)
passes = fails = 0
for cid, lbl, status, pgn, neon in results:
    mark = "PASS" if status == 'PASS' else "FAIL <<"
    print(f"{cid:>3}  {lbl:<22} {mark:>8}  {pgn:>8,}  {neon:>9,}")
    if status == 'PASS':
        passes += 1
    else:
        fails += 1

print("-" * 58)
print(f"Total: {case} cases   PASS: {passes}   FAIL: {fails}")

# ── independent CSV verification ─────────────────────────────────────────────
print()
print("=" * 60)
print("INDEPENDENT CSV VERIFICATION")
print("=" * 60)

# 1. Verify one Q3 device overlap directly from account_devices.csv
print("\n[1] Device overlap – checking Set B (account 147228) from CSV …")
target_account = 147228
csv_path = os.path.join(SRC_DIR, 'account_devices.csv')
target_rows  = []
overlap_rows = []
with open(csv_path) as f:
    for row in csv.DictReader(f):
        if int(row['account_id']) == target_account:
            target_rows.append(row)

with open(csv_path) as f:
    all_ad = list(csv.DictReader(f))

print(f"  account {target_account} is on {len(target_rows)} device(s)")
for tr in target_rows:
    dev = int(tr['device_id'])
    fd1, ld1 = int(tr['first_day']), int(tr['last_day'])
    for row in all_ad:
        if int(row['device_id']) == dev and int(row['account_id']) != target_account:
            fd2, ld2 = int(row['first_day']), int(row['last_day'])
            ovs = max(fd1, fd2)
            ove = min(ld1, ld2)
            if ovs <= ove:
                overlap_rows.append((int(row['account_id']), dev, ovs, ove))
print(f"  Overlapping accounts found: {len(overlap_rows)}")
if overlap_rows:
    print(f"  First overlap: {overlap_rows[0]}")

# 2. Verify one Q5 chain directly from transfers.csv
print("\n[2] Rapid onward payment chain – Set A (account 998, day 6) from CSV …")
START_DAY6 = 1788213600 + 5*86400 + 9*3600 + 45*60   # 2026-09-06 09:45 CAT
END_DAY6   = START_DAY6 + 3600

# Load relevant transfers into memory (only small slice needed)
relevant = []
with open(os.path.join(SRC_DIR, 'transfers.csv')) as f:
    for row in csv.DictReader(f):
        occ = int(row['occurred_at'])
        if occ >= START_DAY6 - 1800 and occ < END_DAY6 + 1800:
            relevant.append({k: int(v) for k, v in row.items()})

first_hop = [r for r in relevant
             if r['sender_id'] == 998
             and START_DAY6 <= r['occurred_at'] < END_DAY6]
print(f"  First-hop transfers from acct 998: {len(first_hop)}")
chains_found = 0
for t1 in first_hop:
    second_hop = [r for r in relevant
                  if r['sender_id'] == t1['receiver_id']
                  and t1['occurred_at'] < r['occurred_at'] <= t1['occurred_at']+600
                  and 90*t1['amount_rwf'] <= 100*r['amount_rwf'] <= 105*t1['amount_rwf']]
    for t2 in second_hop:
        third_hop = [r for r in relevant
                     if r['sender_id'] == t2['receiver_id']
                     and t2['occurred_at'] < r['occurred_at'] <= t2['occurred_at']+600
                     and 90*t2['amount_rwf'] <= 100*r['amount_rwf'] <= 105*t2['amount_rwf']
                     and len({998, t1['receiver_id'], t2['receiver_id'], r['receiver_id']}) == 4]
        chains_found += len(third_hop)
        if third_hop:
            print(f"  Example chain (CSV): t1={t1['transfer_id']} t2={t2['transfer_id']} t3={third_hop[0]['transfer_id']}")
print(f"  Chains verified from CSV: {chains_found}")
