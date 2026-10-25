"""
load_test.py  –  Section 7  Concurrent request load test.

Tests Q4 depth-10 and Q7 bound-6 separately.
Client counts: 1, 4, 8, 16 per engine.
Each test is repeated 3 times.

Design:
  - multiprocessing with one persistent connection per process
  - multiprocessing.Barrier to synchronise starts
  - 15-second deadline window per test run
  - 60-second query timeout
  - p95 = sorted latency at position ceil(0.95*n), counting from 1

Results saved to load_test_results.csv.
"""

import csv
import math
import multiprocessing as mp
import os
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from statistics import median
from time import perf_counter

from db_connect import pg_connect, neo_driver, run_pg, run_neo
import queries as Q
from improve_q7 import Q7_SQL_SELECTED  # version selected in Section 6.3

CAT = timezone(timedelta(hours=2))
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'load_test_results.csv')
DEADLINE_S = 15
QUERY_TIMEOUT_S = 60
N_REPEATS = 3

# Sets to cycle: A, B, C
CYCLE_SETS = ['A', 'B', 'C']

# ── workload definitions ─────────────────────────────────────────────────────
WORKLOADS = {
    'Q4-d10': {
        'pg_sql':    Q.Q4_SQL,
        'neo_cypher': Q.Q4_CYPHER,
        'params_fn': lambda s: Q.q4_params(s, 10),
    },
    'Q7-b6': {
        'pg_sql':    Q7_SQL_SELECTED,        # selected version per §6.3
        'neo_cypher': Q.Q7_CYPHER_LENGTH,
        'params_fn': lambda s: Q.q7_params(s, 6),
    },
}


# ── worker function (runs in a subprocess) ───────────────────────────────────
def worker(engine, workload_name, client_id, barrier, result_queue,
           pg_sql, neo_cypher, params_list):
    """One worker process: warm up, wait at barrier, then loop for 15 s."""
    try:
        # open persistent connection
        if engine == 'postgresql':
            conn   = pg_connect()
            conn.execute("SET statement_timeout = 60000;")
            conn.execute("SET work_mem = '64MB';")
            run_fn = lambda q, p: run_pg(q, p, conn=conn)
        else:
            drv    = neo_driver()
            run_fn = lambda q, p: run_neo(q, p, driver=drv)

        query = pg_sql if engine == 'postgresql' else neo_cypher

        # warm up: cycle A-B-C once
        for params in params_list:
            try:
                run_fn(query, params)
            except Exception:
                pass

        # synchronise start
        barrier.wait()
        start_time = perf_counter()
        deadline   = start_time + DEADLINE_S

        records = []   # (set_key, duration, rows, status)
        idx     = 0

        while True:
            set_key = CYCLE_SETS[idx % len(CYCLE_SETS)]
            params  = params_list[idx % len(params_list)]
            idx    += 1

            t0 = perf_counter()
            try:
                rows   = run_fn(query, params)
                dur    = perf_counter() - t0
                status = 'TIMEOUT' if dur > QUERY_TIMEOUT_S else 'OK'
                records.append((set_key, dur, len(rows), status))
            except Exception as e:
                dur = perf_counter() - t0
                err_str = str(e).lower()
                status = 'TIMEOUT' if (dur >= QUERY_TIMEOUT_S or 'timeout' in err_str or 'canceling statement' in err_str) else 'ERROR'
                records.append((set_key, dur, 0, status))

            # check deadline AFTER completing started cycle
            if perf_counter() >= deadline:
                break

        total_elapsed = perf_counter() - start_time

        # close connection
        if engine == 'postgresql':
            conn.close()
        else:
            drv.close()

        # extract successes, errors, timeouts to keep message compact
        latencies = [d for (_, d, n, s) in records if s == 'OK']
        errors    = sum(1 for (_, _, _, s) in records if s not in ('OK', 'TIMEOUT'))
        timeouts  = sum(1 for (_, _, _, s) in records if s == 'TIMEOUT')

        result_queue.put((client_id, latencies, errors, timeouts, total_elapsed))

    except Exception as e:
        result_queue.put((client_id, [], 1, 0, 0))


def p95(latencies):
    if not latencies:
        return float('nan')
    s = sorted(latencies)
    pos = math.ceil(0.95 * len(s))
    return s[pos - 1]


# ── run one experiment (engine × workload × n_clients) ──────────────────────
def run_experiment(engine, workload_name, n_clients, wl_def, rep_num):
    params_list = [wl_def['params_fn'](s) for s in CYCLE_SETS]
    pg_sql      = wl_def['pg_sql']
    neo_cypher  = wl_def['neo_cypher']

    barrier  = mp.Barrier(n_clients)
    rq       = mp.Queue()
    procs    = []

    for cid in range(n_clients):
        p = mp.Process(
            target=worker,
            args=(engine, workload_name, cid, barrier, rq,
                  pg_sql, neo_cypher, params_list),
            daemon=True,
        )
        p.start()
        procs.append(p)

    # DRAIN QUEUE FIRST before joining to prevent pipe buffer deadlock
    all_latencies = []
    all_errors    = 0
    all_timeouts  = 0
    all_elapsed   = []

    for _ in range(n_clients):
        try:
            cid, lats, errs, tos, el = rq.get(timeout=300)
            all_latencies.extend(lats)
            all_errors   += errs
            all_timeouts += tos
            all_elapsed.append(el)
        except Exception:
            all_errors += 1

    for p in procs:
        p.join(timeout=5)
        if p.is_alive():
            p.terminate()

    # metrics
    total_t    = max(all_elapsed) if all_elapsed else DEADLINE_S
    throughput = len(all_latencies) / total_t if total_t > 0 else 0
    med_lat    = median(all_latencies) * 1000 if all_latencies else float('nan')
    p95_lat    = p95(all_latencies)    * 1000 if all_latencies else float('nan')

    cat_now = datetime.now(CAT).isoformat()
    print(f"  rep={rep_num} clients={n_clients}: "
          f"throughput={throughput:.2f}/s  "
          f"med={med_lat:.0f}ms  p95={p95_lat:.0f}ms  "
          f"correct={len(all_latencies)}  errors={all_errors}  timeouts={all_timeouts}")

    return {
        'engine':     engine,
        'workload':   workload_name,
        'n_clients':  n_clients,
        'repetition': rep_num,
        'cat_time':   cat_now,
        'throughput': round(throughput, 4),
        'median_ms':  round(med_lat, 1),
        'p95_ms':     round(p95_lat, 1),
        'correct':    len(all_latencies),
        'errors':     all_errors,
        'timeouts':   all_timeouts,
        'total_s':    round(total_t, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    all_results = []

    # load previously completed valid results if any
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, 'r') as f:
            reader = list(csv.DictReader(f))
            for row in reader:
                # keep only valid completed runs (e.g. correct > 0 or Q4 rows)
                if not (row['engine'] == 'postgresql' and row['workload'] == 'Q7-b6' and int(row.get('correct', 0)) == 0 and int(row.get('errors', 0)) > 0):
                    # convert numeric fields
                    all_results.append({
                        'engine':     row['engine'],
                        'workload':   row['workload'],
                        'n_clients':  int(row['n_clients']),
                        'repetition': int(row['repetition']),
                        'cat_time':   row['cat_time'],
                        'throughput': float(row['throughput']),
                        'median_ms':  float(row['median_ms']) if row['median_ms'] != 'nan' else float('nan'),
                        'p95_ms':     float(row['p95_ms']) if row['p95_ms'] != 'nan' else float('nan'),
                        'correct':    int(row['correct']),
                        'errors':     int(row['errors']),
                        'timeouts':   int(row['timeouts']),
                        'total_s':    float(row['total_s']),
                    })

    for engine in ['postgresql', 'neo4j']:
        for wl_name, wl_def in WORKLOADS.items():
            for n_clients in [1, 4, 8, 16]:
                # check if combo is already fully completed
                existing_for_combo = [r for r in all_results if r['engine'] == engine and r['workload'] == wl_name and r['n_clients'] == n_clients]
                if len(existing_for_combo) >= N_REPEATS:
                    print(f"\n=== {engine.upper()} | {wl_name} | clients={n_clients} (ALREADY COMPLETE, SKIPPING) ===")
                    tpts = [r['throughput'] for r in existing_for_combo]
                    meds = [r['median_ms']  for r in existing_for_combo]
                    p95s = [r['p95_ms']     for r in existing_for_combo]
                    print(f"  SUMMARY: throughput_med={median(tpts):.2f}/s  "
                          f"latency_med_med={median(meds):.0f}ms  "
                          f"p95_med={median(p95s):.0f}ms")
                    continue

                print(f"\n=== {engine.upper()} | {wl_name} | clients={n_clients} ===")
                rep_results = []
                for rep in range(1, N_REPEATS + 1):
                    r = run_experiment(engine, wl_name, n_clients, wl_def, rep)
                    rep_results.append(r)
                    all_results.append(r)
                    # save incrementally so partial progress is safe
                    with open(OUT_FILE, 'w', newline='') as f:
                        w = csv.DictWriter(f, fieldnames=list(all_results[0].keys()))
                        w.writeheader()
                        w.writerows(all_results)

                # summarise repetitions by median throughput
                tpts = [r['throughput'] for r in rep_results]
                meds = [r['median_ms']  for r in rep_results]
                p95s = [r['p95_ms']     for r in rep_results]
                print(f"  SUMMARY: throughput_med={median(tpts):.2f}/s  "
                      f"latency_med_med={median(meds):.0f}ms  "
                      f"p95_med={median(p95s):.0f}ms")


    print(f"\nFinal results saved: {OUT_FILE}")


    # 16-combination summary table
    print("\n=== ALL 16 COMBINATION SUMMARIES (median across reps) ===")
    from collections import defaultdict
    by_combo = defaultdict(list)
    for r in all_results:
        key = (r['engine'], r['workload'], r['n_clients'])
        by_combo[key].append(r)

    print(f"{'Engine':<14} {'Workload':<10} {'Clients':>7} "
          f"{'Tput/s':>8} {'Med ms':>8} {'p95 ms':>8} {'Correct':>8}")
    print("-" * 70)
    for (eng, wl, nc), reps in sorted(by_combo.items()):
        t  = median([r['throughput'] for r in reps])
        m  = median([r['median_ms']  for r in reps])
        p  = median([r['p95_ms']     for r in reps])
        c  = median([r['correct']    for r in reps])
        print(f"{eng:<14} {wl:<10} {nc:>7} {t:>8.2f} {m:>8.0f} {p:>8.0f} {c:>8.0f}")
