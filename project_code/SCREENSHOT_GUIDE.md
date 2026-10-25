# MSDA 9215 Project 2 – Complete Screenshot Guide
### Master of Science in Big Data Analytics | AUCA Group 13
**Submission Date:** 26 October 2026 at 11:59 PM CAT  
**Target Document:** `Project_2_Final_Report_Group_13.docx`

---

## 📷 General Screenshot Instructions (Course Specification)
As stated in the official course handout:
> *"Embed screenshots of each requested checkpoint in your report, with executed commands, results, taskbar and clock visible. Consolidate repeated cases into readable summary screenshots."*

### How to take screenshots on macOS:
1. **Full Screen (Recommended):** Press `Command (⌘) + Shift + 3`. This captures the entire screen, automatically showing the terminal window, command, output, macOS top menu bar clock, and the Dock/taskbar.
2. **Window Capture:** Press `Command (⌘) + Shift + 4`, then hit the `Spacebar`, and click on the Terminal window.
3. **Pasting:** Open `Project_2_Final_Report_Group_13.docx` in Microsoft Word, Pages, or Google Docs, locate the corresponding `[ PASTE SCREENSHOT X HERE ]` box, and press `Command (⌘) + V`.

---

## 📋 All 20 Screenshot Commands & Checkpoints

Execute these commands from inside the `project_code` directory:
```bash
cd "/Users/apple2019/Desktop/AUCA2025/Big Data Analytics - New - Sept/Project_2_Mobile_Money_Analytics_2026/Project_2_Mobile_Money_Analytics_2026_Package/project_code"
```

---

### Screenshot 1 (Section 1.1) – PostgreSQL & Neo4j Environment Configuration
**Requirement:** Software versions, hardware memory settings, and `Africa/Kigali` timezone.
```bash
psql "dbname=mobile_money user=postgres host=localhost port=5432" -c "SHOW timezone; SHOW shared_buffers; SHOW work_mem; SELECT version();"
cypher-shell -u neo4j -p Mobile2026! "CALL dbms.components() YIELD name, versions, edition;"
```
*Expected Output:* Timezone `Africa/Kigali`, shared_buffers (128MB), work_mem (64MB), PostgreSQL 17, and Neo4j Community 5.26.0.

---

### Screenshot 2 (Section 1.2) – Data Capture 10-Record Preview & Five-Stream Totals
**Requirement:** 10-row preview from generators and final five-stream audit totals.
```bash
python3 -c "import mobile_money_generator as g, itertools; print('--- PREVIEW CUSTOMERS ---'); print(list(itertools.islice(g.iter_customers(), 3))); print('--- PREVIEW TRANSFERS ---'); print(list(itertools.islice(g.iter_transfers(), 3)))"
cat capture.log | tail -22
```
*Expected Output:* First few rows from generator streams, total row count 20,993,500, transfer count 20,003,300, and total sum 231,482,327,870 RWF.

---

### Screenshot 3 (Section 2.1) – PostgreSQL Table Definitions, Foreign Keys & Constraints
**Requirement:** Schema definitions, primary keys, foreign keys, and CHECK constraints.
```bash
psql "dbname=mobile_money user=postgres host=localhost port=5432" -c "\d+ transfers"
psql "dbname=mobile_money user=postgres host=localhost port=5432" -c "\d+ account_devices"
```
*Expected Output:* Column types, NOT NULL, FK constraints to `accounts` and `devices`, and CHECK constraints on positive amounts and valid day ranges.

---

### Screenshot 4 (Section 2.2) – PostgreSQL Bulk Load Audit, Role Verification & Storage Footprint
**Requirement:** Match row counts, transfer totals, confirm 240,000 person / 6,000 merchant / 2,000 agent accounts, and storage size.
```bash
psql "dbname=mobile_money user=postgres host=localhost port=5432" -c "SELECT relname AS table_name, n_live_tup AS row_count FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"
psql "dbname=mobile_money user=postgres host=localhost port=5432" -c "SELECT role, count(*) FROM accounts GROUP BY role ORDER BY count(*) DESC;"
psql "dbname=mobile_money user=postgres host=localhost port=5432" -c "SELECT count(*) AS total_transfers, min(occurred_at), max(occurred_at), sum(amount_rwf) AS total_rwf FROM transfers;"
psql "dbname=mobile_money user=postgres host=localhost port=5432" -c "SELECT pg_size_pretty(pg_database_size('mobile_money')) AS db_size;"
```
*Expected Output:* Table row counts matching capture totals, 240k/6k/2k role breakdown, 231.48B RWF sum, and ~3.62 GB database size.

---

### Screenshot 5 (Section 3.2) – Neo4j Full Import Completion & Constraint Creation
**Requirement:** Full import completion log, unique constraints on IDs, and index on `occurred_at`.
```bash
cat neo4j_import.log | tail -25
cypher-shell -u neo4j -p Mobile2026! "SHOW CONSTRAINTS;"
cypher-shell -u neo4j -p Mobile2026! "SHOW INDEXES;"
```
*Expected Output:* `IMPORT DONE` in 3m 48s, node/relationship counts, unique constraints on `customer_id`, `account_id`, `device_id`, and index on `occurred_at`.

---

### Screenshot 6 (Section 3.2) – Neo4j Graph Entity Counts Verification
**Requirement:** Totals: 704,600 nodes, 20,536,900 relationships, and role breakdown.
```bash
cypher-shell -u neo4j -p Mobile2026! "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC;"
cypher-shell -u neo4j -p Mobile2026! "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS count ORDER BY count DESC;"
cypher-shell -u neo4j -p Mobile2026! "MATCH (a:Account) RETURN a.role AS role, count(a) AS count;"
```
*Expected Output:* 248k accounts, 228.6k devices, 228k customers, 20,003,300 transfers, 285.6k used_devices, 248k owns, and 240k/6k/2k roles.

---

### Screenshot 7 (Section 3.3) – Account 998 Dual-Model Inspection
**Requirement:** SQL JOINs and Cypher MATCH tracing Account 998 to owner, devices, and transfers.
```bash
python3 inspect_account.py 998
```
*Expected Output:* Exact entity correspondence between PostgreSQL and Neo4j: Customer 998 (Kigali), Person role, Device 998, Device 228001, and 81 outbound transfers.

---

### Screenshot 8 (Section 4.1) – Q1 Single-Hour Account Activity
**Requirement:** Paired SQL and Cypher results for Sets A through F during 09:45–10:45 CAT.
```bash
python3 -c "import run_queries as rq; rq.run_q1()"
```
*Expected Output:* Identical counts and total RWF across all 6 review sets in PostgreSQL and Neo4j.

---

### Screenshot 9 (Section 4.2) – Q2 Full-Month Daily Activity Table
**Requirement:** 30 days grouped in CAT time matching audit totals.
```bash
python3 -c "import run_queries as rq; rq.run_q2()" | head -35
```
*Expected Output:* 30 calendar days matching identically between engines, reconciling to 231,482,327,870 RWF.

---

### Screenshot 10 (Section 4.3) – Q3 Shared Devices with Overlapping Periods
**Requirement:** Shared devices with overlapping intervals for Sets A–F.
```bash
python3 -c "import run_queries as rq; rq.run_q3()"
```
*Expected Output:* Shared other account IDs, device IDs, access types, and overlap day intervals matching between SQL and Cypher.

---

### Screenshot 11 (Section 5.1) – Q4 Ownership & Device Network Traversal
**Requirement:** Traversal counts across depths 4, 6, 8, 10 grouped by owner region.
```bash
python3 -c "import run_queries as rq; rq.run_q4()" | head -45
```
*Expected Output:* Account counts grouped by Rwandan province matching across all depths between engines.

---

### Screenshot 12 (Section 5.2) – Q5 Rapid Onward Payments (Layering Chains)
**Requirement:** Rapid 3-hop chains within 600 seconds with 90%–105% value retention.
```bash
python3 -c "import run_queries as rq; rq.run_q5()"
```
*Expected Output:* 1 chain in Sets A, B, C; 0 chains in Sets D, E, F; with transfer IDs, CAT timestamps, and amounts.

---

### Screenshot 13 (Section 5.3) – Q6 Circular Payments (Wash Cycles)
**Requirement:** Closed payment cycles (3–8 hops) returning to source within 1,800 seconds.
```bash
python3 -c "import run_queries as rq; rq.run_q6()"
```
*Expected Output:* 1 cycle in Set A (Length 4, 120s duration), 1 cycle in Set C (Length 6, 200s duration), matching between engines.

---

### Screenshot 14 (Section 5.4) – Q7 Shortest Transfer Connections
**Requirement:** Shortest person-restricted transfer paths at bounds 4 and 6.
```bash
python3 -c "import run_queries as rq; rq.run_q7()"
```
*Expected Output:* Path length comparisons across all 12 cases and supporting path account sequences.

---

### Screenshot 15 (Section 6.1) – 61-Case Correctness Verification & CSV Checks
**Requirement:** Full comparison program status table and independent CSV checks.
```bash
python3 compare.py
```
*Expected Output:* Full table showing `Total: 61 cases PASS: 61 FAIL: 0` and independent CSV verification for Account 147228 and Account 998.

---

### Screenshot 16 (Section 6.2) – Execution Timing Benchmarks & Plans
**Requirement:** Timing comparison table (21 cases) and EXPLAIN ANALYZE / PROFILE plans.
```bash
cat benchmark.log | head -35
cat benchmark.log | grep -A 25 "EXPLAIN (ANALYZE, BUFFERS) - Q7" | head -25
```
*Expected Output:* Median milliseconds comparison and PostgreSQL recursive worktable scan vs Neo4j profile with 114 db hits.

---

### Screenshot 17 (Section 6.3) – Q7 SQL Improvement Before/After Comparison
**Requirement:** SQL optimization attempt correctness, timings, and decision.
```bash
python3 improve_q7.py
```
*Expected Output:* Timings showing original vs improved (35.2s vs 40.2s) and justification for retaining original version.

---

### Screenshot 18 (Section 7.1) – Concurrency Load Test 16-Combination Summary
**Requirement:** Multi-client concurrency test results for 1, 4, 8, 16 clients across Q4-d10 and Q7-b6.
```bash
cat load_test.log | tail -45
```
*Expected Output:* Summary table showing throughput, median latency, p95 latency, and completed queries across all 16 combinations.

---

### Screenshot 19 (Section 9.2) – Git Repository & GitHub Remote Status
**Requirement:** Clean git working tree, commit history, and GitHub remote URL.
```bash
git status
git log -2 --oneline
git remote -v
```
*Expected Output:* Branch `main`, clean working tree, commit history, and remote tracking `https://github.com/Asoka1/Mobile_Money_Analytics_2026_Package.git`.

---

### Screenshot 20 (Section 9.2) – Database Services Status & Clean Shutdown
**Requirement:** Verified engine status and service shutdown confirmation.
```bash
neo4j status
psql "dbname=mobile_money user=postgres host=localhost port=5432" -c "SELECT 'PostgreSQL 17 Active' AS status;"
```
*(When stopping database services post-verification:)*
```bash
neo4j stop
pg_ctl stop -D /usr/local/var/postgresql@17
```
*Expected Output:* Engine status confirmed active or stopped cleanly.
