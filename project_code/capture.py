"""
capture.py  –  Section 1.2  Build capture.py
Streams records from mobile_money_generator and writes CSVs progressively.
Run from project_code/ directory: python capture.py
"""

import csv
import time
import os
import sys
from itertools import islice

# ── make sure the generator module is findable (parent directory) ────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import mobile_money_generator as g

# ── output directory: same folder as this script ────────────────────────────
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── 1.1  Preview ten records from every stream ──────────────────────────────
print("=" * 60)
print("dataset_info():", g.dataset_info())
print()
for stream_name, fields in g.FIELDS.items():
    iter_fn = getattr(g, f'iter_{stream_name}')
    preview = list(islice(iter_fn(), 10))
    print(f"--- {stream_name} (first 10) ---")
    for row in preview:
        print(row)
    print()
print("=" * 60)


# ── helper: write one stream to CSV ─────────────────────────────────────────
def capture_stream(stream_name, iter_fn, fields, log_every=1_000_000):
    """Write all rows from iter_fn() to <stream_name>.csv.
    Returns (rows_written, elapsed_seconds, file_size_bytes, transfer_audit).
    """
    csv_path = os.path.join(OUT_DIR, f"{stream_name}.csv")
    rows_written = 0
    t_count = 0
    t_earliest = None
    t_latest = None
    t_sum_rwf = 0

    t0 = time.perf_counter()
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in iter_fn():
            writer.writerow(row)
            rows_written += 1

            if stream_name == 'transfers':
                occ = row['occurred_at']
                t_count += 1
                t_earliest = occ if t_earliest is None else min(t_earliest, occ)
                t_latest   = occ if t_latest   is None else max(t_latest,   occ)
                t_sum_rwf += row['amount_rwf']

            if rows_written % log_every == 0:
                print(f"  {stream_name}: {rows_written:,} rows written …")

    elapsed    = time.perf_counter() - t0
    file_bytes = os.path.getsize(csv_path)

    audit = {}
    if stream_name == 'transfers':
        audit = dict(
            count=t_count,
            earliest_occurred_at=t_earliest,
            latest_occurred_at=t_latest,
            sum_amount_rwf=t_sum_rwf,
        )
    return rows_written, elapsed, file_bytes, audit


# ── 1.2  Capture every stream ────────────────────────────────────────────────
STREAMS = [
    ('customers',       g.iter_customers,       g.FIELDS['customers']),
    ('accounts',        g.iter_accounts,        g.FIELDS['accounts']),
    ('devices',         g.iter_devices,         g.FIELDS['devices']),
    ('account_devices', g.iter_account_devices, g.FIELDS['account_devices']),
    ('transfers',       g.iter_transfers,       g.FIELDS['transfers']),
]

EXPECTED_COUNTS = {
    'customers':       228_000,
    'accounts':        248_000,
    'devices':         228_600,
    'account_devices': 285_600,
    'transfers':       20_003_300,
}

print("\nCapturing all streams …\n")
overall_t0 = time.perf_counter()
results = {}

for stream_name, iter_fn, fields in STREAMS:
    print(f"[{stream_name}] starting …")
    rows, secs, fsize, audit = capture_stream(stream_name, iter_fn, fields)
    results[stream_name] = dict(rows=rows, secs=secs, fsize=fsize, audit=audit)
    expected = EXPECTED_COUNTS[stream_name]
    status = "OK" if rows == expected else f"MISMATCH (expected {expected:,})"
    print(f"  -> {rows:,} rows in {secs:.1f}s  {fsize/1e6:.1f} MB  {status}\n")

overall_elapsed = time.perf_counter() - overall_t0

print("=" * 60)
print("CAPTURE SUMMARY")
print("=" * 60)
for sn, r in results.items():
    exp = EXPECTED_COUNTS[sn]
    ok  = "OK" if r['rows'] == exp else f"ERROR (expected {exp:,})"
    print(f"  {sn:16s}: {r['rows']:>12,} rows  {r['fsize']/1e6:8.1f} MB  {r['secs']:6.1f}s  {ok}")

print(f"\n  Total rows: {sum(v['rows'] for v in results.values()):,}")
print(f"  Total time: {overall_elapsed:.1f}s")

t_audit = results['transfers']['audit']
print("\nTRANSFER AUDIT TOTALS")
print(f"  count             : {t_audit['count']:,}")
print(f"  earliest occurred : {t_audit['earliest_occurred_at']}")
print(f"  latest occurred   : {t_audit['latest_occurred_at']}")
print(f"  sum amount_rwf    : {t_audit['sum_amount_rwf']:,} RWF")
print("=" * 60)
