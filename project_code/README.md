# Project 2 – Mobile Money Investigations with PostgreSQL and Neo4j

**Course:** Advanced Big Data Analytics  
**Due:** 26 October 2026 at 11:59 PM CAT  

---

## Prerequisites

| Software | Version tested |
|----------|---------------|
| Python   | ≥ 3.11 |
| psycopg (v3) | `pip install psycopg[binary]` |
| neo4j Python driver | `pip install neo4j` |
| numpy    | `pip install numpy` |
| matplotlib | `pip install matplotlib` |
| PostgreSQL | 16+ |
| Neo4j Community | 5.x |

Set up secrets via environment variables (or edit `db_connect.py`):
```bash
export MOBILE_PG_DSN="dbname=mobile_money user=postgres host=localhost port=5432"
export MOBILE_NEO_URI="bolt://localhost:7687"
export MOBILE_NEO_USER="neo4j"
export MOBILE_NEO_PASS="yourpassword"
```

---

## Execution Order

### Section 1 – Capture the data
```bash
# 1.1 Create PostgreSQL database (run once)
createdb mobile_money
psql -d mobile_money -c "SET timezone = 'Africa/Kigali';"

# 1.2 Generate and write CSVs
python capture.py
```
*Screenshot the preview (first 10 rows of each stream) and the final five-stream totals.*

---

### Section 2 – Build PostgreSQL

```bash
# 2.1 + 2.2 Apply schema, indexes, bulk load, and verify
bash load_pg.sh mobile_money /path/to/project_code
```
*Screenshot: definitions & constraints, row counts, role breakdown, data/index sizes.*

---

### Section 3 – Build Neo4j

```bash
# 3.2 Create typed-header import CSVs
python prepare_import.py
# ↑ This prints the neo4j-admin command to run next.

# STOP Neo4j, then run the printed neo4j-admin command, e.g.:
neo4j stop
neo4j-admin database import full neo4j \
  --id-type=integer \
  --nodes=Customer=neo4j_import/neo4j_customers.csv \
  --nodes=Account=neo4j_import/neo4j_accounts.csv \
  --nodes=Device=neo4j_import/neo4j_devices.csv \
  --relationships=OWNS=neo4j_import/neo4j_owns.csv \
  --relationships=USED_DEVICE=neo4j_import/neo4j_used_device.csv \
  --relationships=TRANSFER=neo4j_import/neo4j_transfers.csv \
  --overwrite-destination=true

# START Neo4j and run the post-import Cypher
neo4j start
# In Neo4j Browser or cypher-shell:
:source setup_neo4j.cypher

# 3.3 Inspect one account in both models
python inspect_account.py 998
```
*Screenshot: import completion, constraints/indexes, node/relationship counts, account inspection.*

---

### Section 4 & 5 – Run Q1–Q7 queries

```bash
python run_queries.py
```
*Screenshot all six paired results for each question, plus example chains/cycles/paths.*

---

### Section 6 – Correctness and performance

```bash
# 6.1 Compare all 61 cases
python compare.py

# 6.2 Benchmark (21 cases per engine)
python benchmark.py

# 6.3 SQL improvement for Q7
python improve_q7.py
```
*Screenshot: 61-case status table, explain plans, timing summaries, improvement outcome.*

---

### Section 7 – Concurrent load test

```bash
python load_test.py
```
*Screenshot: active clients, all 16 combination summaries.*

---

### Charts (Sections 4.2, 5.1, 7.2)

```bash
python plot_results.py
```
Produces:
- `chart_q2_daily.png` – daily count and value
- `chart_q4_depth_B.png`, `chart_q4_depth_E.png` – count vs depth
- `chart_load_Q4-d10.png`, `chart_load_Q7-b6.png` – throughput and p95

---

### Final verification (Section 9.2)

```bash
# Re-run correctness comparison and screenshot
python compare.py

# Stop database services and screenshot
neo4j stop
pg_ctl stop -D /usr/local/var/postgresql@17
```

---

## File Map

| File | Section | Purpose |
|------|---------|---------|
| `mobile_money_generator.py` | – | Supplied generator (unchanged) |
| `capture.py` | 1.2 | Stream all 5 iterators to CSV |
| `schema.sql` | 2.1 | PostgreSQL table + constraint definitions |
| `load_pg.sh` | 2.2 | Bulk COPY + index setup + verification |
| `prepare_import.py` | 3.2 | Create Neo4j typed-header CSVs |
| `setup_neo4j.cypher` | 3.2 | Post-import constraints + indexes |
| `inspect_account.py` | 3.3 | SQL/Cypher account inspection |
| `db_connect.py` | 4+ | Shared connection helpers |
| `queries.py` | 4, 5 | Q1–Q7 SQL and Cypher strings + params |
| `run_queries.py` | 4, 5 | Execute Q1–Q7 for all 6 review sets |
| `compare.py` | 6.1 | 61-case correctness comparison |
| `benchmark.py` | 6.2 | 21-case timing per engine |
| `improve_q7.py` | 6.3 | Improved SQL for Q7 (BFS dedup) |
| `load_test.py` | 7 | Concurrent multiprocessing load test |
| `plot_results.py` | 4.2, 5.1, 7.2 | Chart generation (5 PNG charts) |
| `generate_report_pdf.py` | 9.1 | Builds official submission PDF with embedded charts |
| `REPORT.md` | – | Full technical documentation and analytical notes |

---


