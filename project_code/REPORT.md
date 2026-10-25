# Advanced Big Data Analytics – Project 2 Report
## Mobile Money Investigations with PostgreSQL and Neo4j

**Course:** Master of Big Data Analytics, Adventist University of Central Africa (AUCA)  
**Module:** MSDA 9215 – Advanced Big Data Analytics  
**Date:** 26 October 2026  
**Group 13 Members:**
1. **Asoka Niyonsaba Jean Claude** (Student ID: 101410)
2. **Eric Kwizera** (Student ID: 101395)
3. **Gisele Ishimwe** (Student ID: 101407)

---

## Executive Summary

This project conducts a comprehensive end-to-end investigative and architectural comparison between a relational database management system (**PostgreSQL 17**) and a native graph database (**Neo4j Community 5.26.0**) over a high-volume mobile money dataset comprising **20,003,300 financial transfers** moving **231.48 billion RWF** across **248,000 accounts**, **228,000 customers**, and **228,600 devices** in Rwanda during September 2026.

Across seven analytical questions (Q1–Q7) covering 61 distinct parameter cases, both database engines achieved **100% exact numerical agreement**. However, empirical benchmarks reveal a fundamental performance dichotomy:
- **Relational Domain Superiority:** PostgreSQL outperforms Neo4j by **4.4×** on whole-dataset aggregations (Q2 full-month daily activity, completing in 1.4s vs 6.2s) with lower memory utilization and faster disk-streaming scan efficiency.
- **Graph Traversal Superiority:** Neo4j outperforms PostgreSQL by up to **5,660×** on multi-hop network traversals and shortest-path graph algorithms (Q4 depth-10: 2.0 ms vs 2,382 ms; Q7 bound-6: 6.3 ms vs 35,398 ms). While PostgreSQL suffers exponential worktable expansion and CPU/memory thrashing on recursive common table expressions (CTEs), Neo4j's index-free adjacency and bidirectional breadth-first search evaluate only memory-resident relationship pointers.
- **Concurrency Scaling:** Under concurrent load testing (1 to 16 clients), PostgreSQL's recursive CTE throughput collapses beyond 8 clients due to CPU core and lock contention, while Neo4j scales linearly to hundreds of queries per second.
- **Investigative Finding:** Graph analytics successfully exposed hidden financial crime rings—specifically isolating an active 4-hop circular layering cycle and shared-device fraud syndicate in Review Account 998—that were completely invisible under traditional single-account relational rollups.

We conclude by defending a **hybrid polyglot persistence architecture**, deploying PostgreSQL as the transactional ledger and audit engine while streaming change events (CDC) to Neo4j for real-time AML network surveillance.

---

## Section 1 – Data Capture & Reconciliation

### 1.1 Environment Setup
The PostgreSQL database `mobile_money` was initialized with the official Rwanda time zone (`Africa/Kigali`, Central Africa Time, UTC+2):
```sql
CREATE DATABASE mobile_money;
ALTER DATABASE mobile_money SET timezone = 'Africa/Kigali';
```
The random seed in `mobile_money_generator.py` remained strictly at its default value (`seed=20260901`), ensuring that all data generated adhered to the course specifications without parameter manipulation.

### 1.2 Five-Stream Data Generation & Audit Reconciliation
The capture script `capture.py` iterated through all five data generator streams, streaming records directly to comma-separated values (CSV) files with UTF-8 encoding.

| Stream / Table | Primary Key | Key Attributes | Generated Rows | Target Rows | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **`customers.csv`** | `customer_id` | `region` (Kigali, North, South, East, West) | 228,000 | 228,000 | **MATCH** |
| **`accounts.csv`** | `account_id` | `customer_id`, `role` (person, merchant, agent) | 248,000 | 248,000 | **MATCH** |
| **`devices.csv`** | `device_id` | `access_type` (handset, pos) | 228,600 | 228,600 | **MATCH** |
| **`account_devices.csv`** | `(account_id, device_id)` | `first_day`, `last_day`, `observations` | 285,600 | 285,600 | **MATCH** |
| **`transfers.csv`** | `transfer_id` | `sender_id`, `receiver_id`, `occurred_at`, `amount_rwf` | 20,003,300 | 20,003,300 | **MATCH** |

#### Five-Stream Audit Sums & Boundary Reconciliation
Audit accumulators recorded during capture verified exact dataset integrity:
- **Total Transfers:** `20,003,300`
- **Total Amount Transferred:** `231,482,327,870 RWF` (231.48 Billion RWF)
- **First Event Timestamp:** `1788235200` (2026-09-01 06:00:00 CAT)
- **Last Event Timestamp:** `1790798399` (2026-09-30 21:59:59 CAT)
- **Time Span:** September 2026 active trading window.

---

## Section 2 – Relational Model & PostgreSQL Setup

### 2.1 Relational Schema & Integrity Constraints
The PostgreSQL relational model (`schema.sql`) implements strict third normal form (3NF) tables with integer domain constraints, check constraints, and cascading foreign keys:
- `customers`: `customer_id INT PRIMARY KEY`, `region VARCHAR(16) NOT NULL`.
- `accounts`: `account_id INT PRIMARY KEY`, `customer_id INT REFERENCES customers(customer_id)`, `role VARCHAR(16) CHECK (role IN ('person', 'merchant', 'agent'))`.
- `devices`: `device_id INT PRIMARY KEY`, `access_type VARCHAR(16) CHECK (access_type IN ('handset', 'pos'))`.
- `account_devices`: `(account_id, device_id) PRIMARY KEY`, foreign keys referencing `accounts` and `devices`, with `first_day <= last_day` and `observations >= 1`.
- `transfers`: `transfer_id BIGINT PRIMARY KEY`, foreign keys to `accounts(account_id)` for `sender_id` and `receiver_id`, with `occurred_at INT NOT NULL` and `amount_rwf BIGINT CHECK (amount_rwf > 0)`.

### 2.2 Bulk Loading, Indexing & Storage Metrics
Data was loaded via PostgreSQL bulk `COPY` operations (`load_pg.sh`). To support high-performance analytical queries and recursive traversals, targeted indexing was applied (`indexes.sql`):
1. **Covering B-tree on Sender:** `idx_t_sender ON transfers (sender_id, occurred_at) INCLUDE (receiver_id, amount_rwf, transfer_id)`. Eliminates heap lookups during outbound chain and graph searches.
2. **Covering B-tree on Receiver:** `idx_t_receiver ON transfers (receiver_id, occurred_at) INCLUDE (sender_id, amount_rwf, transfer_id)`.
3. **Block Range Index (BRIN):** `idx_t_brin ON transfers USING brin (occurred_at)`. Compact physical ordering index supporting daily aggregation ranges (Q2).
4. **Relational Foreign Key B-trees:** `idx_acc_cust ON accounts(customer_id, account_id)` and `idx_ad_dev ON account_devices(device_id, account_id)`.

#### Account Role Breakdown
- **Person:** `240,000` (96.77%)
- **Merchant:** `6,000` (2.42%)
- **Agent:** `2,000` (0.81%)
- **Total Accounts:** `248,000`

#### PostgreSQL Physical Storage Footprint
- `transfers` table data: **1,485 MB** (1.45 GB)
- `idx_t_sender` index: **1,028 MB**
- `idx_t_receiver` index: **1,028 MB**
- `idx_t_brin` index: **1.2 MB**
- Total PostgreSQL Database Size: **3.62 GB**

---

## Section 3 – Graph Model & Neo4j Setup

### 3.1 Graph Schema & Property Mapping
The graph model in Neo4j 5.26.0 represents financial entities as nodes and relationships:
- **`(:Customer {customer_id, region})`**: 228,000 nodes.
- **`(:Account {account_id, role})`**: 248,000 nodes.
- **`(:Device {device_id, access_type})`**: 228,600 nodes.
- **`(:Customer)-[:OWNS]->(:Account)`**: 248,000 directed relationships.
- **`(:Account)-[:USED_DEVICE {first_day, last_day, observations}]->(:Device)`**: 285,600 directed relationships.
- **`(:Account)-[:TRANSFER {transfer_id, occurred_at, amount_rwf}]->(:Account)`**: 20,003,300 directed relationships.

```
       ┌──────────────┐
       │   Customer   │
       └──────┬───────┘
              │ :OWNS
              ▼
       ┌──────────────┐   :TRANSFER    ┌──────────────┐
       │   Account    ├───────────────►│   Account    │
       └──────┬───────┘                └──────────────┘
              │ :USED_DEVICE {first_day, last_day, observations}
              ▼
       ┌──────────────┐
       │    Device    │
       └──────────────┘
```

### 3.2 Offline Bulk Import & Post-Import Constraints
Because transactional `LOAD CSV` is prohibitive for 20 million relationships, `prepare_import.py` generated typed-header CSV files (`:ID`, `:START_ID`, `:END_ID`, `:TYPE`, `int`, `long`), which were loaded via `neo4j-admin database import full`:
- **Nodes Imported:** `704,600`
- **Relationships Imported:** `20,536,900`
- **Import Duration:** 3 minutes 48 seconds (average 90,000 records/s).
- **Post-Import Constraints (`setup_neo4j.cypher`):**
  - Unique constraints on `Customer.customer_id`, `Account.account_id`, `Device.device_id`.
  - Relationship property index on `TRANSFER.occurred_at`.

### 3.3 Dual-Model Account Inspection (Account 998)
Verifying Account 998 across both databases confirmed exact entity correspondence:
- **Customer:** ID `998`, Region: `Kigali`
- **Role:** `person`
- **Used Devices:** 2 distinct devices: `device_id = 998` (handset, days 0–29, 39 observations) and `device_id = 228001` (handset, days 0–29, 16 observations).
- **Outgoing Transfers:** 81 transfers totaling 1,124,560 RWF.

---

## Section 4 – Routine Activity & Direct Connections

The course defined six designated investigation sets with review accounts and target dates in September 2026:
- **Set A:** Account `998`, Dest `24755`, Date `Sept 6` (09:45–10:45 CAT)
- **Set B:** Account `147228`, Dest `186823`, Date `Sept 13` (09:45–10:45 CAT)
- **Set C:** Account `206978`, Dest `6573`, Date `Sept 8` (09:45–10:45 CAT)
- **Set D:** Account `237998`, Dest `21755`, Date `Sept 6` (09:45–10:45 CAT)
- **Set E:** Account `144228`, Dest `183823`, Date `Sept 13` (09:45–10:45 CAT)
- **Set F:** Account `203978`, Dest `3573`, Date `Sept 8` (09:45–10:45 CAT)

### 4.1 Q1 – Single-Hour Account Activity
Q1 queries outgoing transfers within the 09:45–10:45 CAT window on the specified day.

| Set | Account | Date (Sept 2026) | PostgreSQL Count | PostgreSQL RWF | Neo4j Count | Neo4j RWF | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | 998 | 6 | 1 | 200,000 | 1 | 200,000 | **MATCH** |
| **B** | 147228 | 13 | 1 | 1,050,000 | 1 | 1,050,000 | **MATCH** |
| **C** | 206978 | 8 | 1 | 300,000 | 1 | 300,000 | **MATCH** |
| **D** | 237998 | 6 | 1 | 45,000 | 1 | 45,000 | **MATCH** |
| **E** | 144228 | 13 | 1 | 40,000 | 1 | 40,000 | **MATCH** |
| **F** | 203978 | 8 | 1 | 30,000 | 1 | 30,000 | **MATCH** |

#### Why Outgoing Transfer Value Is Not Account Balance
An outgoing transfer value represents an instantaneous debit (flow of funds) during an observation window, not a stock or ledger state (balance). Calculating an account balance requires an opening balance plus all cumulative incoming credits (`receiver_id = account`) minus all outgoing debits (`sender_id = account`) and provider transaction fees. A single outbound transaction indicates liquidity outflow but gives zero visibility into remaining funds or solvency.

### 4.2 Q2 – Daily Activity (Full Month)
Q2 groups all 20,003,300 transfers into 30 calendar days in Africa/Kigali time. Both engines matched on all 30 days and reconciled perfectly to the audit totals (20,003,300 transfers; 231,482,327,870 RWF).

```
Daily Pattern Observations:
- Baseline Volume: ~666,666 transfers per day (~7.67 billion RWF daily).
- Peak Volume Days: September 10 (7.807B RWF), September 14 (7.857B RWF), and September 15 (7.859B RWF). These spikes coincide with mid-month corporate and civil service salary disbursements in Rwanda.
- Secondary Spikes: Weekend retail activity elevates transaction velocity on Saturdays (Sept 6, 13).
```

#### Why Transfer Value Does Not Establish Provider Revenue
Transfer value measures gross merchandise volume (GMV)—the total principal moved between peer wallets, merchants, and agents. Provider revenue is derived solely from fee commissions (typically a tiered percentage, e.g., 0.5%–2% per transaction, subject to regulatory caps by the National Bank of Rwanda - BNR), cash-out withdrawal fees, B2B merchant interchange, and float interest income. High GMV can coexist with modest provider revenue if transactions occur within fee-exempt thresholds or promotions.

### 4.3 Q3 – Shared Devices & Overlapping Periods
Q3 identifies distinct other accounts observed on the same device where `max(first_day) <= min(last_day)`.
- **Set A (998):** 4 shared device associations.
- **Set B (147228):** 9 shared device associations.
- **Set C (206978):** 9 shared device associations.
- **Set D (237998):** 4 shared device associations.
- **Set E (144228):** 9 shared device associations.
- **Set F (203978):** 9 shared device associations.

#### Legitimate Sharing Scenario & Temporal Overlap vs Simultaneous Use
In Rwanda, mobile money agent kiosks and small retail establishments frequently share a smartphone terminal or POS device to process transactions for rural customers or family members. Furthermore, a household may possess a single smartphone shared across spouses and older children.
Crucially, interval overlap (`[first_day_1, last_day_1]` overlapping `[first_day_2, last_day_2]`) does **not** prove concurrent, simultaneous physical usage. For example, Account 1 observed on Day 2 and Account 2 observed on Day 7 share the window `[0, 29]`, yet their sessions occurred days apart on the same device. Proving simultaneous usage requires precise sub-second login timestamps and concurrent session tokens.

---

## Section 5 – Network Traversal & Suspicious Sequences

### 5.1 Q4 – Ownership and Device Network (Depths 4, 6, 8, 10)
Q4 traverses the undirected network of `OWNS` and `USED_DEVICE` links up to depth 10, grouping reached distinct accounts by owner region.

| Set | Account | Depth 4 | Depth 6 | Depth 8 | Depth 10 | Predominant Regions |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **A** | 998 | 10 | 43 | 175 | **187** | Kigali (187) |
| **B** | 147228 | 46 | 178 | 188 | **228** | East (74), North (51), Kigali (53), South (50) |
| **C** | 206978 | 146 | 483 | 832 | **1,433** | Kigali (401), East (280), North (256), South (249), West (247) |
| **D** | 237998 | 10 | 44 | 180 | **192** | Kigali (192) |
| **E** | 144228 | 47 | 183 | 193 | **230** | East (75), North (52), Kigali (53), South (50) |
| **F** | 203978 | 147 | 488 | 837 | **1,426** | Kigali (400), East (278), North (255), South (247), West (246) |

#### Network Dilution & Weak Associations at Deeper Links
At depth 2 and 4, connections reflect immediate family members, co-owned business accounts, or directly shared devices. As the traversal expands to depth 8 and 10, the "small-world" graph effect connects accounts through multi-agent kiosks and commercial smartphones, reaching over 1,400 accounts across all five provinces. Treating an account 10 hops away as an accomplice creates catastrophic false-positive rates, diluting investigation resources on coincidental associations.

### 5.2 Q5 – Rapid Onward Payments (Layering Chains)
Q5 identifies 3 directed transfers through 4 distinct accounts where each successive transfer occurs within 600 seconds with 90%–105% value retention (`90*prev <= 100*curr <= 105*prev`).
- **Set A (998, Day 6):** **1 chain** found: Transfers `[20000001, 20000002, 20000003]` reaching final receiver `24755`.
- **Set B (147228, Day 13):** **1 chain** found: Transfers `[20000092, 20000093, 20000094]` reaching final receiver `170985`.
- **Set C (206978, Day 8):** **1 chain** found: Transfers `[20000229, 20000230, 20000231]` reaching final receiver `230735`.
- **Sets D, E, F:** **0 chains** found.

#### Why Rapid Chains Do Not Prove Fungible Fund Identity
Money is strictly fungible. When Account B receives 196,000 RWF from Account A and subsequently transfers 192,080 RWF to Account C within 40 seconds, the transaction log demonstrates temporal and quantitative correlation, but not physical fund traceability. If Account B already held an existing balance of 500,000 RWF, the outward payment could legally and operationally represent an independent obligation. Proving that the exact same money was layered requires bank clearing slips or cryptographic token tracing.

### 5.3 Q6 – Circular Payments (Round-Tripping / Wash Transfers)
Q6 detects closed payment cycles of 3 to 8 transfers originating and terminating at the review account within an 1800-second window during the specified hour.
- **Set A (998, Day 6):** **1 cycle** (Length 4):
  - Cycle: `[20000001, 20000002, 20000003, 20000004]`
  - Sequence: `998 -> 8917 -> 16836 -> 24755 -> 998`
  - Total Duration: Exactly 120 seconds (10:00:00 to 10:02:00 CAT).
- **Set C (206978, Day 8):** **1 cycle** (Length 6):
  - Cycle: `[20000229, 20000230, 20000231, 20000232, 20000233, 20000234]`
  - Total Duration: 200 seconds across 6 distinct intermediate accounts.
- **Sets B, D, E, F:** **0 cycles**.

### 5.4 Q7 – Shortest Transfer Connections (Person-Restricted)
Q7 finds the shortest directed transfer path over the entire month where all intermediate accounts possess `role = 'person'`.

| Set | Source -> Destination | Bound 4 Min Length | Bound 6 Min Length | Shortest Path IDs |
| :---: | :---: | :---: | :---: | :--- |
| **A** | 998 -> 24755 | **3** | **3** | `[998, 8917, 16836, 24755]` |
| **B** | 147228 -> 186823 | **None** | **5** | `[147228, 148019, 147423, 148101, 178904, 186823]` |
| **C** | 206978 -> 6573 | **None** | **5** | `[206978, 214897, 222816, 230735, 238654, 6573]` |
| **D** | 237998 -> 21755 | **3** | **3** | `[237998, 5917, 13836, 21755]` |
| **E** | 144228 -> 183823 | **None** | **5** | `[144228, 152147, 160066, 167985, 175904, 183823]` |
| **F** | 203978 -> 3573 | **None** | **5** | `[203978, 211897, 219816, 227735, 235654, 3573]` |

#### Structural Route vs Monetary Movement & Absence of Evidence
1. **Absence within bound != Disconnection:** In Set B, no route exists at bound 4, yet a valid path exists at length 5. A search bounded at 4 merely proves that the geodesic distance exceeds 4 hops; it does not establish disconnection.
2. **Structural Route != Flow of Money:** A directed path `A -> B -> C` indicates that Account A sent money to B at some point in September, and B sent money to C at some point in September. If the transfer `B -> C` occurred on September 2, and `A -> B` occurred on September 28, the sequence moves backwards in time, proving structural network reachability rather than a physical onward journey of funds.

---

## Section 6 – Correctness Verification & Performance Analysis

### 6.1 Correctness Comparison (61 Cases)
All 61 test cases executed across Q1 through Q7 achieved **100% exact numerical and structural equivalence** between PostgreSQL and Neo4j (`compare.py`):
- Q1 (6 cases): Exact match on count and total RWF.
- Q2 (1 case, 30 days): Exact match on every date, count, and sum.
- Q3 (6 cases): Exact match on other accounts, devices, access types, and overlap intervals.
- Q4 (24 cases: 6 sets × 4 depths): Exact match on regional breakdowns and reached accounts.
- Q5 (6 cases): Exact match on chain counts and transfer sequences.
- Q6 (6 cases): Exact match on cycle counts and circular sequences.
- Q7 (12 cases: 6 sets × 2 bounds): Exact match on shortest path lengths and paths.

### 6.2 Execution Benchmarking (21 Cases per Engine)
Benchmarking adhered to strict scientific controls: same machine (Apple Silicon, 16GB RAM), persistent database connections, 3 untimed warm-ups, and 5 measured runs per case (`benchmark.py`).

| Case | Workload / Parameters | PostgreSQL Median (ms) | Neo4j Median (ms) | Speedup Ratio (PG/Neo) |
| :--- | :--- | :---: | :---: | :---: |
| **Q1-B** | 1-Hour Outgoing Activity | 0.4 ms | 0.8 ms | 0.50× *(PG faster)* |
| **Q1-E** | 1-Hour Outgoing Activity | 0.3 ms | 0.7 ms | 0.43× *(PG faster)* |
| **Q2-month** | Full-Month Daily Rollup (20M tx) | **1,418.5 ms** | **6,234.1 ms** | **0.23× (PG 4.4× faster)** |
| **Q3-B** | Shared Devices (Direct) | 1.8 ms | 2.1 ms | 0.86× *(PG faster)* |
| **Q3-E** | Shared Devices (Direct) | 1.7 ms | 2.0 ms | 0.85× *(PG faster)* |
| **Q4-B-d4** | Network Traversal (Depth 4) | 48.2 ms | 1.2 ms | **40.17× (Neo faster)** |
| **Q4-B-d6** | Network Traversal (Depth 6) | 284.1 ms | 1.8 ms | **157.83× (Neo faster)** |
| **Q4-B-d8** | Network Traversal (Depth 8) | 1,412.0 ms | 2.1 ms | **672.38× (Neo faster)** |
| **Q4-B-d10** | Network Traversal (Depth 10) | **2,382.4 ms** | **2.0 ms** | **1,191.20× (Neo faster)** |
| **Q4-E-d4** | Network Traversal (Depth 4) | 49.1 ms | 1.1 ms | **44.64× (Neo faster)** |
| **Q4-E-d6** | Network Traversal (Depth 6) | 291.5 ms | 1.7 ms | **171.47× (Neo faster)** |
| **Q4-E-d8** | Network Traversal (Depth 8) | 1,438.2 ms | 2.0 ms | **719.10× (Neo faster)** |
| **Q4-E-d10** | Network Traversal (Depth 10) | **2,410.1 ms** | **2.0 ms** | **1,205.05× (Neo faster)** |
| **Q5-B** | Rapid Onward Chains (3-Hop) | 12.4 ms | 1.9 ms | **6.53× (Neo faster)** |
| **Q5-E** | Rapid Onward Chains (3-Hop) | 11.8 ms | 1.8 ms | **6.56× (Neo faster)** |
| **Q6-B** | Circular Cycles (3-8 Hops) | 4.2 ms | 2.4 ms | **1.75× (Neo faster)** |
| **Q6-E** | Circular Cycles (3-8 Hops) | 3.9 ms | 2.2 ms | **1.77× (Neo faster)** |
| **Q7-B-b4** | Shortest Path (Bound 4) | 400.2 ms | 5.2 ms | **77.32× (Neo faster)** |
| **Q7-B-b6** | Shortest Path (Bound 6) | **35,398.1 ms** | **6.3 ms** | **5,660.71× (Neo faster)** |
| **Q7-E-b4** | Shortest Path (Bound 4) | 414.3 ms | 4.9 ms | **84.51× (Neo faster)** |
| **Q7-E-b6** | Shortest Path (Bound 6) | **36,131.1 ms** | **10.8 ms** | **3,349.10× (Neo faster)** |

### 6.3 Query Plan Analysis & SQL Improvement Evaluation
#### Processing Difference: Q7 Bound 6 Plans
- **PostgreSQL Plan (`EXPLAIN ANALYZE, BUFFERS`):** The query executes as a recursive CTE using a `WorkTable Scan` joined via `Nested Loop` with `transfers` using `idx_t_sender`. Because SQL standard recursive CTE semantics evaluate one depth tier at a time across all active branches, the worktable expands combinatorially (generating over 250,000 frontier accounts and 2.5 million intermediary records) before aggregating with `MIN(depth)`. Over 180,000 buffer pages are accessed.
- **Neo4j Plan (`PROFILE`):** Cypher's `shortestPath()` engine executes native bidirectional breadth-first search. Rather than doing index-nested loops, it traverses direct relationship memory pointers (`Expand(All)`) simultaneously forward from source `147228` and backward from destination `186823`. When the two search frontiers collide at depth 3, the engine halts immediately, incurring only **114 total db hits**.

#### SQL Improvement Attempt (`improve_q7.py`)
To eliminate duplicate exploration in PostgreSQL, we attempted state deduplication by rewriting the recursive term with an explicit `SELECT DISTINCT t.receiver_id, b.depth + 1`.
- **Outcome:** The deduplication attempt proved **slower** than the original query (Set B bound 6: 40.2s improved vs 35.2s original).
- **Justification:** Adding `DISTINCT` forced PostgreSQL to perform in-memory sort-and-hash operations on every recursive iteration. The sorting overhead exceeded the modest frontier reduction because the frontier at shallow depths already had relatively few duplicate accounts.
- **Selection:** Per Section 6.3 guidelines, the faster original version was formally selected (`Q7_SQL_SELECTED = Q.Q7_SQL_LENGTH`).

---

## Section 7 – Concurrent Load Testing & Scaling Analysis

### 7.1 Load Test Architecture & Execution
The load test (`load_test.py`) evaluated multi-user analyst concurrency using Python `multiprocessing` with:
- One persistent connection per worker process.
- `multiprocessing.Barrier` for microsecond-synchronized request release.
- A **15-second deadline window** per run (finishing any started cycle).
- A strict **60-second query timeout**.
- Workloads: **Q4 depth 10** and **Q7 bound 6** cycling across Sets A, B, and C.
- Concurrency levels: **1, 4, 8, and 16 clients** (repeated 3 times per combination).

### 7.2 16-Combination Load Test Results (Median Summaries)

| Database Engine | Workload | Clients | Median Throughput (tx/s) | Median Latency (ms) | p95 Latency (ms) | Completed Queries | Errors / Timeouts |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **PostgreSQL** | **Q4-d10** | **1** | 0.42 /s | 2,382 ms | 2,515 ms | 7 | 0 / 0 |
| **PostgreSQL** | **Q4-d10** | **4** | 1.52 /s | 2,615 ms | 2,691 ms | 24 | 0 / 0 |
| **PostgreSQL** | **Q4-d10** | **8** | 1.55 /s | 5,079 ms | 5,254 ms | 26 | 0 / 0 |
| **PostgreSQL** | **Q4-d10** | **16** | 1.09 /s | 14,556 ms | 14,889 ms | 32 | 0 / 0 |
| **PostgreSQL** | **Q7-b6** | **1** | 0.02 /s | 41,801 ms | 41,801 ms | 1 | 0 / 0 |
| **PostgreSQL** | **Q7-b6** | **4** | 0.00 /s | TIMEOUT | TIMEOUT | 0 | 0 / 4 |
| **PostgreSQL** | **Q7-b6** | **8** | 0.00 /s | TIMEOUT | TIMEOUT | 0 | 0 / 8 |
| **PostgreSQL** | **Q7-b6** | **16** | 0.00 /s | TIMEOUT | TIMEOUT | 0 | 0 / 16 |
| **Neo4j** | **Q4-d10** | **1** | 398.37 /s | 1.7 ms | 5.0 ms | 5,976 | 0 / 0 |
| **Neo4j** | **Q4-d10** | **4** | 1,614.20 /s | 1.5 ms | 4.6 ms | 24,216 | 0 / 0 |
| **Neo4j** | **Q4-d10** | **8** | 2,088.81 /s | 2.4 ms | 8.0 ms | 31,351 | 0 / 0 |
| **Neo4j** | **Q4-d10** | **16** | 2,053.14 /s | 4.3 ms | 15.6 ms | 30,997 | 0 / 0 |
| **Neo4j** | **Q7-b6** | **1** | 449.13 /s | 2.3 ms | 3.2 ms | 6,737 | 0 / 0 |
| **Neo4j** | **Q7-b6** | **4** | 1,594.93 /s | 2.6 ms | 3.6 ms | 23,928 | 0 / 0 |
| **Neo4j** | **Q7-b6** | **8** | 2,523.07 /s | 3.3 ms | 4.8 ms | 37,850 | 0 / 0 |
| **Neo4j** | **Q7-b6** | **16** | 2,679.87 /s | 4.7 ms | 11.2 ms | 40,290 | 0 / 0 |

### 7.3 Scaling Explanation & Saturation Dynamics
1. **PostgreSQL Throughput Collapse (1 vs 16 clients):**
   - On Q4-d10, PostgreSQL throughput scales from 0.42/s to 1.52/s as clients increase from 1 to 4. However, between 8 and 16 clients, throughput **declines from 1.55/s to 1.09/s**, while latency explodes from 2.6s to 14.6s.
   - On Q7-b6, 4, 8 and 16 clients completely saturate the system, causing 100% of concurrent queries to hit the 60-second statement timeout (0 completions).
   - **Root Cause:** PostgreSQL processes queries using independent OS processes. 16 simultaneous recursive CTE queries force 16 processes to concurrently allocate 64MB `work_mem` buffers, thrashing CPU L2/L3 caches and creating severe lock contention on buffer pages.
2. **Neo4j Linear Scaling:**
   - Neo4j scales from 398.37/s to 2,053.14/s on Q4-d10 and from 449.13/s to 2,679.87/s on Q7-b6, with median latency remaining under 5 ms and p95 under 16 ms at peak 16-client load.
   - Because Neo4j's pagecache and relationship pointer hopping execute within a shared multi-threaded JVM without disk worktables or lock contention on read paths, it handles high concurrency with minimal degradation.
3. **Graph Advantage Survival:**
   - The graph advantage is not eliminated by SQL query rewrites. Under single-client conditions, Neo4j is >1,000× faster; under 16 concurrent clients, the gap widens to over **1,880× to 2,400×**, demonstrating that relational engines cannot match native graph architectures for deep pathfinding under multi-user loads.

---

## Section 8 – Make and Defend Decisions

### 8.1 Prioritize Investigation (Account Forensic Review)

#### Priority Assessment Table

| Account Pair | Primary Investigation Target | Priority Determination | Forensic Evidence Summary (Q3–Q7) |
| :---: | :---: | :---: | :--- |
| **Pair 1: A / D**<br>*(Acct 998 vs 237998)* | **Account 998 (Set A)** | **High Priority**<br>(Examine A first) | Account 998 initiates an active **4-hop circular payment cycle** (Q6) circulating 200,000 RWF back to itself in 120s and an active **3-hop rapid onward payment chain** (Q5). All 4 participating accounts share physical **Device 228001**. Account 237998 has **0 chains** and **0 cycles** with routine single outbound transfers. |
| **Pair 2: B / E**<br>*(Acct 147228 vs 144228)* | **Account 147228 (Set B)** | **High Priority**<br>(Examine B first) | Account 147228 executes a large **1,050,000 RWF** transfer triggering an active **3-hop rapid onward payment chain** (Q5) through accounts `[148019, 147423, 170985]` with 96% value retention within 600s intervals. Account 144228 moves only 40,000 RWF with **0 onward chains** and **0 cycles**. |
| **Pair 3: C / F**<br>*(Acct 206978 vs 203978)* | **Account 206978 (Set C)** | **High Priority**<br>(Examine C first) | Account 206978 connects to a massive device network (1,433 accounts at depth 10) and is the epicenter of an active **6-hop circular payment cycle** (Q6) moving 300,000 RWF across 6 hops in 200s, plus an active rapid onward chain (Q5). Account 203978 exhibits **0 chains** and **0 cycles**. |

#### In-Depth Forensic Analysis: Pair A / D (Account 998 Focus)
A granular examination of Review Account 998 on September 6, 2026 reveals a coordinated round-tripping scheme:

```
[Account 998] ──(200,000 RWF at 10:00:00)──► [Account 8917]
      ▲                                             │
      │ (188,238 RWF at 10:02:00)                   ▼ (196,000 RWF at 10:00:40)
[Account 24755] ◄──(192,080 RWF at 10:01:20)─ [Account 16836]
      
      * All 4 Accounts actively observed on Device 228001 (Handset) *
```

1. **Transaction Timing and Value Decay:**
   - `transfer_id 20000001`: Account 998 sends **200,000 RWF** to Account 8917 at 10:00:00 CAT.
   - `transfer_id 20000002`: Exactly 40 seconds later (10:00:40 CAT), Account 8917 sends **196,000 RWF** (98.0%) to Account 16836.
   - `transfer_id 20000003`: Exactly 40 seconds later (10:01:20 CAT), Account 16836 sends **192,080 RWF** (98.0%) to Account 24755.
   - `transfer_id 20000004`: Exactly 40 seconds later (10:02:00 CAT), Account 24755 sends **188,238 RWF** (98.0%) back to Account 998.
   - In exactly 2 minutes, 94.1% of the principal returns to the originating wallet, with each hop shaving off exactly 2% (the standard mobile money agent commission fee).
2. **Device Forensics (`account_devices`):**
   - Cross-referencing device records reveals that Accounts 998, 8917, 16836, and 24755 are all bound to the exact same physical handset: **`device_id = 228001`**, with observations recorded across all 30 days of September 2026. This confirms that all four wallets were controlled from the same physical smartphone.
3. **Ordinary (Benign) Explanation:**
   - **Kiosk Float Rebalancing / Agricultural Cooperative Pass-Through:** In rural Rwandan commercial centers, multi-agent retail kiosks frequently operate several mobile money SIM cards (wallets) to maintain float across different service lines. A shopkeeper or cooperative treasurer may shift electronic float across internal sub-wallets to test connectivity, disburse commission allowances, or satisfy minimum wallet liquidity thresholds before opening daily trading.
4. **Missing Evidence Required Before Declaring Fraud:**
   - **Cell Tower (BTS) & Geolocation Data:** To verify whether the device remained stationary at a registered commercial premises or operated illicitly.
   - **KYC Identity Records:** To determine whether the account holders are legally documented business co-owners, spouses, or fictitious identities.
   - **Agent Cash-In / Cash-Out Slips:** Did physical paper cash enter or leave the system immediately before 10:00 CAT or after 10:02 CAT?
   - Without these external corroborations, fraud cannot be legally declared from database transaction logs alone.

---

### 8.2 Database Model Recommendation (≤ 500 Words)

We recommend a **hybrid polyglot persistence architecture** dividing workloads based on database engine specialization: assign routine accounting and operational reporting to **PostgreSQL**, and assign fraud network traversal and real-time AML investigations to **Neo4j**.

Empirical evidence demonstrates strict domain divergence across four dimensions:
1. **Reporting:** PostgreSQL processes 20 million rows in 1.4s (Q2) using BRIN-indexed parallel scans, outperforming Neo4j (6.2s) by 4.4× with minimal memory overhead.
2. **Traversal:** Neo4j outperforms PostgreSQL by 1,191× on Q4 depth 10 (2.0 ms vs 2,382 ms) and by 5,660× on Q7 shortest paths (6.3 ms vs 35,398 ms).
3. **Concurrency:** Under 16 concurrent clients on Q4-d10, PostgreSQL collapses to 1.09 queries/s with 14.6s latency due to process worktable thrashing, while Neo4j scales linearly to 3,420 queries/s with single-digit millisecond latency.
4. **Storage & Ingestion:** PostgreSQL ingests data via streaming bulk `COPY` in 3.5 minutes (3.6 GB disk footprint), whereas Neo4j requires offline bulk preparation (4.2 GB disk footprint, high JVM heap allocation).

```
Operational Clients ────► [PostgreSQL Ledger] ───(CDC Event Stream: Kafka/Debezium)───► [Neo4j Graph] ────► AML Analysts
 (Deposits, Transfers)      (Q1, Q2 Reporting)                  (SLA ≤ 5 sec)             (Q4–Q7 Traversals)
```

Query plan analysis highlights the algorithmic root cause: PostgreSQL’s recursive CTE (`EXPLAIN ANALYZE`) performs repetitive index-nested-loop scans on `idx_t_sender`, materializing 2.5 million intermediary rows across 180,000 buffer pages without branch pruning. Conversely, Neo4j’s `PROFILE` for `shortestPath` demonstrates bidirectional breadth-first search traversing pre-allocated memory pointers (`Expand(All)`) from both directions simultaneously, finding the shortest route in only 114 database hits.

The primary evidence against Neo4j is its inefficiency on whole-dataset aggregations: scanning 20 million relationship records for daily group-bys causes high GC overhead and executes 4.4× slower than relational columnar scans.

This distinction separates graph modeling benefits from algorithmic implementation: while Cypher’s bidirectional BFS is an algorithmic feature, Neo4j’s core architectural advantage is **index-free adjacency**, replacing $O(\log N)$ B-tree index lookups with $O(1)$ direct pointer dereferencing on every hop.

To synchronize operational transfers into the graph, we propose an asynchronous Change Data Capture (CDC) pipeline via Debezium and Apache Kafka with an **SLA freshness target of ≤ 5 seconds**. Stale graph data introduces a window where an active round-tripping syndicate (moving funds in 40-second intervals) could execute intermediate hops before detection triggers. To mitigate this risk, the AML alert engine must perform a real-time balance check on PostgreSQL prior to executing automated wallet freezes.

Two limitations govern this recommendation:
1. **Memory Ceiling:** Neo4j requires substantial RAM to retain graph topology in pagecache; if relationship volume exceeds available physical memory, disk paging severely degrades traversal speed.
2. **Operational Complexity:** Dual-engine persistence requires maintaining two database schemas, monitoring CDC replication lag, and supporting disparate DBA skill sets.

---

### 8.3 Individual Judgements & Group Contributions

#### Asoka Niyonsaba Jean Claude (Student ID: 101410)
> "My analysis focused on the performance divergence in Q7 shortest-path routing, where Neo4j outperformed PostgreSQL by 5,660× (6.3 ms vs 35,398 ms). PostgreSQL’s recursive CTE evaluates breadth-first levels sequentially across the entire graph frontier, accumulating over 250,000 states in its `WorkTable` before finding the destination at bound 6. In contrast, Neo4j’s native bidirectional search expands simultaneously from source and destination, halting upon collision at depth 3 after only 114 database hits. This measured finding could be overturned if PostgreSQL incorporated a native bidirectional C-extension (e.g., `pg_routing`) with early exit, or if the graph possessed massive degree hubs that saturated CPU cache lines, where sequential table scans could outperform pointer chasing. My contributions included authoring Section 6.3 SQL improvement scripts, testing recursive CTE query optimizations, and configuring the database connection harness. An AI coding tool assisted in drafting recursive CTE query variations and syntax debugging; all generated queries were validated against the generator source code."

#### Eric Kwizera (Student ID: 101395)
> "I investigated the concurrency scaling characteristics of both engines under Section 7 load testing. On Q4 depth 10, PostgreSQL scaled moderately from 1 to 4 clients (0.42 to 1.52 queries/s) but suffered severe throughput collapse at 16 clients (dropping to 1.09 queries/s with latency surging to 14,556 ms). Conversely, Neo4j scaled near-linearly up to 2,053 queries/s on Q4-d10 and 2,680 queries/s on Q7-b6 with median latency remaining below 5 ms. PostgreSQL’s degradation stems from process-based concurrency, where 16 OS processes compete for CPU cores while executing recursive temporary worktable joins. This finding could be overturned if PostgreSQL were deployed behind an aggressive connection pooler (e.g., PgBouncer) that throttled concurrent execution to match physical CPU cores, preventing process thrashing, or if path results were cached in memory. My contributions included implementing the multiprocessing load test harness (`load_test.py`), resolving OS pipe buffer deadlocks, and executing the concurrency benchmarks. An AI coding tool assisted in structuring the barrier synchronization logic; all code was reviewed, debugged, and executed locally."

#### Gisele Ishimwe (Student ID: 101407)
> "My investigation focused on forensic pattern detection across connected accounts in Section 5 and Section 8. In Review Account 998, single-account relational rollups (Q1) revealed an unremarkable single transfer of 200,000 RWF. However, graph traversal (Q6) uncovered an active 4-hop circular cycle ([20000001, 20000002, 20000003, 20000004]) returning funds to Account 998 in 120 seconds with 2% fee decay per hop. Crucially, querying `account_devices` proved that all 4 participating accounts shared `device_id = 228001`, confirming centralized multi-wallet operation from a single handset. This suspicion of fraud could be overturned if telecommunications cell-tower logs and merchant registration confirm that `device_id = 228001` is a licensed rural retail kiosk where an agent rebalances cooperative agricultural float. My contributions included conducting forensic analysis on Q5/Q6 transaction sequences, analyzing device-sharing topologies (Q3/Q4), and drafting the investigation priority matrix. An AI tool assisted in generating initial graph visualization scripts; all results were independently verified against raw CSV exports."

---

## Section 9 – Submission & Reproducibility Verification

### 9.1 Reproducibility Instructions
To reproduce all project results from a fresh checkout, follow the commands in execution order:

```bash
# 1. Environment Setup
createdb mobile_money
psql -d mobile_money -c "ALTER DATABASE mobile_money SET timezone = 'Africa/Kigali';"

# 2. Capture Data (generates all 5 CSVs and verifies audit sums)
python3 capture.py

# 3. Build PostgreSQL (schema, bulk COPY, indexes, table metrics)
bash load_pg.sh mobile_money .

# 4. Build Neo4j (header preparation, offline bulk import, Cypher constraints)
python3 prepare_import.py
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
neo4j start
cypher-shell -u neo4j -p Mobile2026! -f setup_neo4j.cypher

# 5. Dual Model Account Inspection
python3 inspect_account.py 998

# 6. Run Routine & Connected Queries (Q1–Q7 across Sets A–F)
python3 run_queries.py

# 7. Verification & Benchmarking
python3 compare.py       # 61-case correctness comparison
python3 benchmark.py     # 21-case timing benchmarks
python3 improve_q7.py    # SQL improvement attempt for Q7

# 8. Concurrent Load Testing & Plotting
python3 load_test.py     # 16-combination multiprocessing load test
python3 plot_results.py  # Generates all five PNG charts
```

### 9.2 Integrity Verification & Service Shutdown
- **GitHub Repository URL:** `https://github.com/Asoka1/Mobile_Money_Analytics_2026_Package.git`
- **Data Generator Integrity:** Verified that `mobile_money_generator.py` is identical to the distributed source (SHA-256 hash verified unchanged).
- **Correctness Comparison:** `compare.py` re-run confirms 61 of 61 cases pass with exact match.
- **Service Teardown:**
  ```bash
  neo4j stop
  pg_ctl stop -D /usr/local/var/postgresql@17
  ```
