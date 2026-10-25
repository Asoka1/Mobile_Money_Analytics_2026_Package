"""
improve_q7.py  –  Section 6.3  SQL improvement attempt for Q7.

Strategy: Deduplicate (account_id, depth) states in the BFS walk so we
never revisit an account at a depth we already reached it at or earlier.
This prunes redundant expansion paths.

Both the original and improved versions are kept; the improved version is
used for Section 7 and the final comparison (B/E bound-6 medians).
"""

import os
from statistics import median
from time import perf_counter

from db_connect import pg_connect, run_pg
import queries as Q

# ─────────────────────────────────────────────────────────────────────────────
# Improved Q7 SQL (deduplicating account-depth states)
# ─────────────────────────────────────────────────────────────────────────────
Q7_SQL_IMPROVED = """
WITH RECURSIVE bfs(account_id, depth) AS (
  -- seed: start node at depth 0
  SELECT %(account)s::integer AS account_id, 0 AS depth

  UNION

  -- expand: only if we have not reached this account at an equal/lower depth
  SELECT DISTINCT t.receiver_id, b.depth + 1
  FROM   bfs b
  JOIN   transfers t  ON t.sender_id   = b.account_id
  JOIN   accounts  a  ON a.account_id  = t.receiver_id
                      AND a.role = 'person'
  WHERE  b.depth < %(bound)s
    AND  t.receiver_id <> %(account)s
  -- UNION (not UNION ALL) deduplicates automatically
)
SELECT MIN(depth) AS min_length
FROM   bfs
WHERE  account_id = %(dest)s
HAVING MIN(depth) IS NOT NULL;
"""

# The benchmark showed ORIGINAL is faster than IMPROVED (35.2s vs 40.2s for Set B-b6)
# because internal SELECT DISTINCT adds sorting overhead without reducing the search space.
# Therefore, ORIGINAL is selected for Section 7 per Section 6.3 guidelines.
Q7_SQL_SELECTED = Q.Q7_SQL_LENGTH


TIMEOUT = 60   # seconds
N_WARMUP  = 3
N_MEASURE = 5

def time_query(conn, query, params):
    start = perf_counter()
    run_pg(query, params, conn=conn)
    return perf_counter() - start


if __name__ == '__main__':
    print("=== Q7 SQL Improvement (deduplicating account-depth states) ===\n")
    print("Sets: B, E  |  Bounds: 4, 6\n")

    conn = pg_connect()
    try:
        for label, sql in [('ORIGINAL', Q.Q7_SQL_LENGTH), ('IMPROVED', Q7_SQL_IMPROVED)]:
            print(f"-- {label} --")
            for s in ['B', 'E']:
                for b in [4, 6]:
                    p = Q.q7_params(s, b)
                    # warm-ups
                    for _ in range(N_WARMUP):
                        time_query(conn, sql, p)
                    # measured
                    times = []
                    for _ in range(N_MEASURE):
                        d = time_query(conn, sql, p)
                        times.append(d)
                    med = median(times)
                    result = run_pg(sql, p, conn=conn)
                    length = result[0][0] if result and result[0][0] is not None else "none"
                    print(f"  Set {s} bound {b}: length={length}  median={med*1000:.1f}ms  "
                          f"min={min(times)*1000:.1f}ms  max={max(times)*1000:.1f}ms")
            print()

        # Correctness check: both versions must agree on all 12 cases
        print("=== Correctness check (original vs improved) ===")
        all_ok = True
        for s in list(Q.REVIEW_SETS.keys()):
            for b in [4, 6]:
                p    = Q.q7_params(s, b)
                orig = run_pg(Q.Q7_SQL_LENGTH, p, conn=conn)
                impr = run_pg(Q7_SQL_IMPROVED,  p, conn=conn)
                match = orig == impr
                if not match:
                    all_ok = False
                    print(f"  MISMATCH Set {s} bound {b}: orig={orig} impr={impr}")
                else:
                    print(f"  MATCH    Set {s} bound {b}: length={orig[0][0]}")
        if all_ok:
            print("\nAll 12 cases match. Improved version is CORRECT.")
        else:
            print("\nWARNING: mismatches found – review improved version.")

    finally:
        conn.close()

