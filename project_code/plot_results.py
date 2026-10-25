"""
plot_results.py  –  Sections 4.2, 5.1, 7.2
Generates charts required by the project.
Reads from timing_results.csv and load_test_results.csv.
Also produces daily activity charts from Q2 results.
"""

import csv
import os
import math
from collections import defaultdict
from statistics import median

# Try to import matplotlib; if not installed, print instructions
try:
    import matplotlib
    matplotlib.use('Agg')  # non-interactive backend for screenshots
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("matplotlib not installed. Run:  pip install matplotlib")

SRC_DIR = os.path.dirname(os.path.abspath(__file__))


def save_fig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Q2 – Daily count and value (requires run_queries.py to have written output)
#    We regenerate from the database directly.
# ─────────────────────────────────────────────────────────────────────────────
def plot_daily_activity():
    from db_connect import run_pg
    import queries as Q
    rows = run_pg(Q.Q2_SQL, {})
    days   = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    totals = [r[2] / 1e9 for r in rows]  # billions RWF

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7))
    ax1.bar(days, counts, color='steelblue')
    ax1.set_title('Daily Transfer Count – September 2026')
    ax1.set_xlabel('Date (CAT)')
    ax1.set_ylabel('Number of transfers')
    ax1.tick_params(axis='x', rotation=45)

    ax2.bar(days, totals, color='darkorange')
    ax2.set_title('Daily Transfer Value – September 2026')
    ax2.set_xlabel('Date (CAT)')
    ax2.set_ylabel('Total (billions RWF)')
    ax2.tick_params(axis='x', rotation=45)

    save_fig(os.path.join(SRC_DIR, 'chart_q2_daily.png'))


# ─────────────────────────────────────────────────────────────────────────────
# 2. Q4 – Count vs depth plot (run_queries must have been run first,
#    use the timing_results or re-query)
# ─────────────────────────────────────────────────────────────────────────────
def plot_q4_depth():
    from db_connect import run_pg, run_neo
    import queries as Q

    depths = [4, 6, 8, 10]
    for s in ['B', 'E']:
        pg_counts  = []
        neo_counts = []
        for d in depths:
            p  = Q.q4_params(s, d)
            pg  = run_pg(Q.Q4_SQL,    p)
            neo = run_neo(Q.Q4_CYPHER, p)
            pg_counts.append(sum(r[1] for r in pg))
            neo_counts.append(sum(r['reached_accounts'] for r in neo))

        plt.figure(figsize=(7, 4))
        plt.plot(depths, pg_counts,  'o-', label='PostgreSQL')
        plt.plot(depths, neo_counts, 's--', label='Neo4j')
        plt.title(f'Q4 Reached Accounts vs Depth – Set {s}')
        plt.xlabel('Depth (max links)')
        plt.ylabel('Distinct accounts reached')
        plt.xticks(depths)
        plt.legend()
        save_fig(os.path.join(SRC_DIR, f'chart_q4_depth_{s}.png'))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Load test – throughput and p95 vs client count
# ─────────────────────────────────────────────────────────────────────────────
def plot_load_test():
    lt_file = os.path.join(SRC_DIR, 'load_test_results.csv')
    if not os.path.exists(lt_file):
        print(f"load_test_results.csv not found – run load_test.py first.")
        return

    with open(lt_file) as f:
        rows = list(csv.DictReader(f))

    by_combo = defaultdict(list)
    for r in rows:
        key = (r['engine'], r['workload'], int(r['n_clients']))
        by_combo[key].append(r)

    clients = [1, 4, 8, 16]

    for wl in ['Q4-d10', 'Q7-b6']:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
        fig.suptitle(f'Load Test: {wl}')

        for engine, style in [('postgresql', 'o-'), ('neo4j', 's--')]:
            tpts = []
            p95s = []
            for nc in clients:
                reps = by_combo.get((engine, wl, nc), [])
                if reps:
                    tpts.append(median([float(r['throughput']) for r in reps]))
                    p_vals = [60000.0 if r['p95_ms'] == 'nan' else float(r['p95_ms']) for r in reps]
                    p95s.append(median(p_vals))
                else:
                    tpts.append(0)
                    p95s.append(0)

            ax1.plot(clients, tpts, style, label=engine)
            ax2.plot(clients, p95s, style, label=engine)

        ax1.set_title('Throughput')
        ax1.set_xlabel('Client count')
        ax1.set_ylabel('Correct completions / s')
        ax1.set_xticks(clients)
        ax1.legend()

        ax2.set_title('p95 Latency')
        ax2.set_xlabel('Client count')
        ax2.set_ylabel('p95 latency (ms)')
        ax2.set_xticks(clients)
        ax2.legend()

        save_fig(os.path.join(SRC_DIR, f'chart_load_{wl}.png'))


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if not HAS_MPL:
        print("Install matplotlib and re-run: pip install matplotlib")
        raise SystemExit(1)

    print("Generating charts …")
    plot_daily_activity()
    plot_q4_depth()
    plot_load_test()
    print("Done.")
