# Mobile Money Investigations with PostgreSQL and Neo4j
### AUCA Master of Science in Big Data Analytics — MSDA 9215 (Project 2)

**Academic Institution:** Adventist University of Central Africa (AUCA)  
**Module:** MSDA 9215 – Advanced Big Data Analytics  
**Date:** 26 October 2026  
**Group:** Group 13  

#### Group Members:
1. **Asoka Niyonsaba Jean Claude** (Student ID: 101410) — *Query Algorithms, SQL Optimization, Relational Benchmarking*
2. **Eric Kwizera** (Student ID: 101395) — *Multiprocessing Concurrency Engine, Load Testing & Scalability Analysis*
3. **Gisele Ishimwe** (Student ID: 101407) — *Forensic Network Topology, AML Cycle Detection & Decision Matrix*

---

## Project Overview

This repository contains the complete forensic and architectural investigation comparing **PostgreSQL 17** (relational RDBMS) and **Neo4j Community 5.26.0** (native graph database) over a large-scale mobile money transaction dataset in Rwanda for September 2026.

### Key Dataset Metrics (Reconciled & Verified):
- **Transfers:** `20,003,300` transactions
- **Total Amount Transferred:** `231,482,327,870 RWF` (231.48 Billion RWF)
- **Customers:** `228,000` across all 5 Rwandan provinces
- **Accounts:** `248,000` (`240,000` personal, `6,000` merchant, `2,000` agent)
- **Devices:** `228,600` handsets and POS terminals
- **Temporal Span:** September 1, 2026 to September 30, 2026 (`Africa/Kigali`, UTC+2)
- **Generator Integrity:** SHA-256 hash `2ea0e59d2b7b987d84a3d151bd9d1ad7b3052bfbc25abf1466c8e94467e9455a` (100% intact)

---

## Key Measured Findings

1. **Exact 61-Case Correctness:** All 61 analytical queries (Q1–Q7) matched between PostgreSQL and Neo4j (`compare.py`).
2. **Relational Aggregation Superiority:** PostgreSQL executes whole-dataset daily rollups (Q2, 20M rows) in **1.4s vs 6.2s** (4.4× faster than Neo4j) via BRIN-indexed parallel scans.
3. **Graph Traversal Superiority:** Neo4j outperforms PostgreSQL by up to **5,660×** on multi-hop network pathfinding:
   - **Q4 Depth-10 Traversal:** `2.0 ms` (Neo4j) vs `2,382 ms` (PostgreSQL) — **1,191× speedup**.
   - **Q7 Bound-6 Shortest Path:** `6.3 ms` (Neo4j) vs `35,398 ms` (PostgreSQL) — **5,660× speedup**.
4. **Concurrency Scaling:** Under concurrent load testing (1 to 16 clients):
   - **PostgreSQL** collapses beyond 8 clients due to OS process worktable memory thrashing and buffer locks.
   - **Neo4j** scales linearly to **2,680 queries/s** on Q7-b6 and **2,053 queries/s** on Q4-d10 with $p95$ latency under 16 ms.
5. **AML Forensic Discovery:** Graph traversal exposed an active **4-hop circular laundering cycle** originating from Account 998, returning 200,000 RWF to source in 120 seconds with 2% fee decay across a single shared handset (**Device 228001**), undetectable via single-account relational rollups.
6. **Defended Architecture:** We defend a **hybrid polyglot persistence architecture** combining PostgreSQL for transactional ledgers with Neo4j for real-time AML surveillance.

---

## Visualizations

All 5 high-resolution analytical charts are available in `project_code/`:
- `chart_q2_daily.png` — Daily transfer count & value across September 2026.
- `chart_q4_depth_B.png` & `chart_q4_depth_E.png` — Reached account scaling across depths 4 to 10 for Sets B & E.
- `chart_load_Q4-d10.png` — Multi-client concurrency throughput and $p95$ latency for Q4 depth 10.
- `chart_load_Q7-b6.png` — Multi-client concurrency throughput and $p95$ latency for Q7 bound 6.


---

## Repository Structure

```
.
├── Project_2_Mobile_Money_Analytics_2026.pdf   # Official course assignment handout
├── mobile_money_generator.py                   # Supplied course generator (strictly unchanged)
├── README.md                                   # Root project overview & navigation
├── .gitignore                                  # Excludes local 20M-row CSV datasets
└── project_code/
    ├── Project_2_Final_Report_Group_13.pdf     # Official comprehensive submission report (7 pages)
    ├── REPORT.md                               # Full markdown technical & forensic documentation
    ├── README.md                               # Detailed execution guide in milestone order
    ├── capture.py                              # Section 1.2: 5-stream data capture engine
    ├── schema.sql                              # Section 2.1: 3NF relational schema & constraints
    ├── load_pg.sh                              # Section 2.2: PostgreSQL bulk COPY loader & verifier
    ├── indexes.sql                             # Section 2.2: Covering B-tree and BRIN indexes
    ├── prepare_import.py                       # Section 3.2: Typed-header CSV generator for Neo4j
    ├── setup_neo4j.cypher                      # Section 3.2: Neo4j unique constraints & indexes
    ├── inspect_account.py                      # Section 3.3: Dual-engine account trace
    ├── db_connect.py                           # Database connection wrappers
    ├── queries.py                              # Parameterized Q1–Q7 SQL & Cypher implementations
    ├── run_queries.py                          # Query runner across all 6 review sets (A–F)
    ├── compare.py                              # Section 6.1: 61-case correctness verification
    ├── benchmark.py                            # Section 6.2: 21-case timing harness (warm-up + 5 runs)
    ├── improve_q7.py                           # Section 6.3: SQL optimization attempt & analysis
    ├── load_test.py                            # Section 7.1: Multiprocessing concurrent load test
    ├── plot_results.py                         # Chart generator for 5 analytical PNG plots
    ├── generate_report_pdf.py                  # ReportLab compilation script for submission PDF
    ├── timing_results.csv                      # Raw benchmark measurement timings
    ├── load_test_results.csv                   # Raw concurrency load test measurements
    └── *.log                                   # Execution and verification logs
```

---

## Execution Order & Reproduction

To reproduce all benchmarks and reports from a fresh clone:

```bash
cd project_code

# 1. Capture the dataset (generates 20,993,500 rows across 5 CSVs)
python3 capture.py

# 2. Build PostgreSQL (loads data, applies constraints and indexes)
bash load_pg.sh mobile_money .

# 3. Build Neo4j (generates import headers and imports graph)
python3 prepare_import.py
neo4j stop
# Run the neo4j-admin command output by prepare_import.py
neo4j start
# Run setup_neo4j.cypher via cypher-shell

# 4. Run analytical queries (Q1–Q7)
python3 run_queries.py

# 5. Verify correctness across all 61 cases
python3 compare.py

# 6. Execute benchmark timing (21 cases per engine)
python3 benchmark.py

# 7. Evaluate SQL optimization for Q7
python3 improve_q7.py

# 8. Run concurrent load test (1, 4, 8, 16 clients)
python3 load_test.py

# 9. Generate analytical charts
python3 plot_results.py

# 10. Generate official PDF submission report
python3 generate_report_pdf.py
```

---

## Ethics & Academic Integrity

- The data generator (`mobile_money_generator.py`) is completely unchanged.
- All database queries are fully parameterized without hard-coded results.
- Large raw CSV datasets remain local in accordance with course instructions.
