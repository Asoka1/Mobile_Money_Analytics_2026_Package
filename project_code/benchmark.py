"""
benchmark.py  –  Section 6.2  Time a fixed selection of queries.

Timing rules:
  - Same machine, one database service at a time.
  - 3 untimed warm-ups, 5 measured runs per case.
  - Timing through final-row receipt using perf_counter.
  - 180 s warm-up timeout, 60 s measured timeout.
  - Results saved to timing_results.csv.

Cases (21 per engine):
  Q1: B, E             (2)
  Q2: full month       (1)
  Q3: B, E             (2)
  Q4: B/E × 4 depths   (8)
  Q5: B, E             (2)
  Q6: B, E             (2)
  Q7: B/E × 2 bounds   (4)
  Total: 21
"""

import csv
import os
import sys
import traceback
from datetime import datetime, timezone, timedelta
from time import perf_counter
from statistics import median

from db_connect import pg_connect, neo_driver, run_pg, run_neo
import queries as Q

CAT = timezone(timedelta(hours=2))
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'timing_results.csv')

TIMEOUT_WARMUP  = 180   # seconds
TIMEOUT_MEASURE = 60    # seconds
N_WARMUP = 3
N_MEASURE = 5

# ── build the list of 21 cases ───────────────────────────────────────────────
CASES = []

for s in ['B', 'E']:
    CASES.append(('Q1', s, Q.Q1_SQL,    Q.Q1_CYPHER,    Q.q1_params(s),    None))
CASES.append(    ('Q2', 'month', Q.Q2_SQL, Q.Q2_CYPHER, Q.q2_params(),      None))
for s in ['B', 'E']:
    CASES.append(('Q3', s, Q.Q3_SQL,    Q.Q3_CYPHER,    Q.q3_params(s),    None))
for s in ['B', 'E']:
    for d in [4, 6, 8, 10]:
        CASES.append(('Q4', f'{s}-d{d}', Q.Q4_SQL, Q.Q4_CYPHER, Q.q4_params(s, d), None))
for s in ['B', 'E']:
    CASES.append(('Q5', s, Q.Q5_SQL,    Q.Q5_CYPHER,    Q.q5_params(s),    None))
for s in ['B', 'E']:
    CASES.append(('Q6', s, Q.Q6_SQL,    Q.Q6_CYPHER,    Q.q6_params(s),    None))
for s in ['B', 'E']:
    for b in [4, 6]:
        CASES.append(('Q7', f'{s}-b{b}', Q.Q7_SQL_LENGTH, Q.Q7_CYPHER_LENGTH,
                       Q.q7_params(s, b), None))

assert len(CASES) == 21, f"Expected 21 cases, got {len(CASES)}"


def time_query(run_fn, query, params, timeout_s):
    """Run one query, return (duration_s, row_count, status)."""
    try:
        start = perf_counter()
        rows  = run_fn(query, params)     # blocking – fetch all rows
        dur   = perf_counter() - start
        if dur > timeout_s:
            return dur, len(rows), 'TIMEOUT'
        return dur, len(rows), 'OK'
    except Exception as e:
        return None, 0, f'ERROR: {e}'


# ─────────────────────────────────────────────────────────────────────────────
# Collect EXPLAIN / PROFILE outside timing for Q2, Q4-B-d10, Q7-B-b6
# ─────────────────────────────────────────────────────────────────────────────
EXPLAIN_CASES = {'Q2', 'Q4-B-d10', 'Q7-B-b6'}

def collect_plans(pg_conn, neo_drv):
    print("\n=== EXPLAIN plans (collected outside timing) ===")
    plan_cases = [
        ('Q2',      Q.Q2_SQL,         Q.Q2_CYPHER,         Q.q2_params()),
        ('Q4-B-d10',Q.Q4_SQL,         Q.Q4_CYPHER,         Q.q4_params('B', 10)),
        ('Q7-B-b6', Q.Q7_SQL_LENGTH,  Q.Q7_CYPHER_LENGTH,  Q.q7_params('B', 6)),
    ]
    for name, sql, cypher, params in plan_cases:
        print(f"\n-- PostgreSQL EXPLAIN (ANALYZE, BUFFERS): {name} --")
        explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {sql}"
        try:
            rows = run_pg(explain_sql, params, conn=pg_conn)
            for row in rows:
                print(row[0])
        except Exception as e:
            print(f"  ERROR: {e}")

        print(f"\n-- Neo4j PROFILE: {name} --")
        profile_cypher = f"PROFILE {cypher}"
        try:
            rows = run_neo(profile_cypher, params, driver=neo_drv)
            for r in rows[:5]:
                print(r)
        except Exception as e:
            print(f"  ERROR: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Main timing loop
# ─────────────────────────────────────────────────────────────────────────────
all_rows = []  # for timing_results.csv

for engine_name in ['postgresql', 'neo4j']:
    print(f"\n{'='*60}")
    print(f"ENGINE: {engine_name.upper()}")
    print(f"{'='*60}")

    if engine_name == 'postgresql':
        conn   = pg_connect()
        run_fn = lambda q, p: run_pg(q, p, conn=conn)
        driver = None
    else:
        driver = neo_driver()
        run_fn = lambda q, p: run_neo(q, p, driver=driver)
        conn   = None

    try:
        for q_name, set_id, sql, cypher, params, _ in CASES:
            query = sql if engine_name == 'postgresql' else cypher
            case_label = f"{q_name}-{set_id}"
            print(f"\n  Case: {case_label}")

            # warm-ups
            for w in range(N_WARMUP):
                d, n, s = time_query(run_fn, query, params, TIMEOUT_WARMUP)
                print(f"    warm-up {w+1}: {d:.2f}s  rows={n}  status={s}")

            # measured runs
            durations = []
            for m in range(N_MEASURE):
                d, n, s = time_query(run_fn, query, params, TIMEOUT_MEASURE)
                if s == 'OK':
                    durations.append(d)
                    print(f"    run {m+1}: {d*1000:.1f} ms  rows={n}")
                else:
                    print(f"    run {m+1}: {s}")
                    durations.append(None)

                cat_now = datetime.now(CAT).isoformat()
                all_rows.append({
                    'case':      case_label,
                    'qname':     q_name,
                    'params':    str(params),
                    'engine':    engine_name,
                    'cat_start': cat_now,
                    'duration_s': d if d is not None else '',
                    'row_count': n,
                    'status':    s,
                })

            valid = [d for d in durations if d is not None]
            if valid:
                med = median(valid)
                print(f"    → median={med*1000:.1f}ms  min={min(valid)*1000:.1f}ms  max={max(valid)*1000:.1f}ms")
    finally:
        if conn:   conn.close()
        if driver: driver.close()

# ─────────────────────────────────────────────────────────────────────────────
# Save results and print summary
# ─────────────────────────────────────────────────────────────────────────────
fieldnames = ['case','qname','params','engine','cat_start','duration_s','row_count','status']
with open(OUT_FILE, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(all_rows)

print(f"\nResults saved: {OUT_FILE}")

# Summary table
print("\n=== TIMING SUMMARY (median ms) ===")
from collections import defaultdict
by_case = defaultdict(lambda: {'postgresql':[], 'neo4j':[]})
for row in all_rows:
    if row['status'] == 'OK' and row['duration_s'] != '':
        by_case[row['case']][row['engine']].append(float(row['duration_s']))

print(f"{'Case':<20} {'PG med ms':>12} {'NEO med ms':>12} {'PG/NEO ratio':>14}")
print("-" * 62)
for case_label, engines in sorted(by_case.items()):
    pg_vals  = engines['postgresql']
    neo_vals = engines['neo4j']
    pg_med   = median(pg_vals)  * 1000 if pg_vals  else float('nan')
    neo_med  = median(neo_vals) * 1000 if neo_vals else float('nan')
    ratio    = pg_med / neo_med if (neo_med and neo_med != 0) else float('nan')
    print(f"{case_label:<20} {pg_med:>12.1f} {neo_med:>12.1f} {ratio:>14.2f}x")

# ─────────────────────────────────────────────────────────────────────────────
# Collect EXPLAIN / PROFILE plans
# ─────────────────────────────────────────────────────────────────────────────
pg_conn2 = pg_connect()
neo_drv2  = neo_driver()
try:
    collect_plans(pg_conn2, neo_drv2)
finally:
    pg_conn2.close()
    neo_drv2.close()
