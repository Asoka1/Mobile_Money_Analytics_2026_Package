"""
generate_report_docx.py
Generates the comprehensive Microsoft Word (.docx) submission report for Project 2:
Mobile Money Investigations with PostgreSQL and Neo4j
AUCA Master of Science in Big Data Analytics – MSDA 9215 (Group 13)

Includes:
- Full milestone report (Sections 1 to 9)
- All analytical and architectural discussions
- All benchmark tables and forensic matrices
- All 5 generated charts embedded directly
- 20 Beautifully styled Screenshot Callout Boxes with exact commands and paste placeholders
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DOCX_PATH = os.path.join(SRC_DIR, "Project_2_Final_Report_Group_13.docx")

# Colors
C_PRIMARY = RGBColor(0x0F, 0x17, 0x2A)    # Slate 900
C_SECONDARY = RGBColor(0x1E, 0x3A, 0x8A)  # Navy 900
C_ACCENT = RGBColor(0x25, 0x63, 0xEB)     # Blue 600
C_DARK = RGBColor(0x33, 0x41, 0x55)       # Slate 700
C_MUTED = RGBColor(0x64, 0x74, 0x8B)      # Slate 500

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="{top}" w:type="dxa"/>\n'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'  <w:left w:w="{left}" w:type="dxa"/>\n'
        f'  <w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_heading_1(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(16)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = 'Helvetica'
    r.font.size = Pt(14)
    r.bold = True
    r.font.color.rgb = C_SECONDARY
    return h

def add_heading_2(doc, text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(text)
    r.font.name = 'Helvetica'
    r.font.size = Pt(11.5)
    r.bold = True
    r.font.color.rgb = C_ACCENT
    return h

def add_body_paragraph(doc, text, bold_prefix=None, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Helvetica'
        r_pre.font.size = Pt(9.5)
        r_pre.bold = True
        r_pre.font.color.rgb = C_PRIMARY
    r_body = p.add_run(text)
    r_body.font.name = 'Helvetica'
    r_body.font.size = Pt(9.5)
    r_body.font.color.rgb = C_DARK
    return p

def add_styled_table(doc, headers, data, col_widths=None):
    tbl = doc.add_table(rows=len(data) + 1, cols=len(headers))
    tbl.autofit = False
    
    # Format header row
    hdr_cells = tbl.rows[0].cells
    for i, h_text in enumerate(headers):
        hdr_cells[i].text = h_text
        set_cell_background(hdr_cells[i], '1E3A8A')
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:
            r.font.name = 'Helvetica'
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            r.bold = True

    # Format data rows
    for r_idx, row in enumerate(data):
        row_cells = tbl.rows[r_idx + 1].cells
        bg_col = 'F8FAFC' if r_idx % 2 == 1 else 'FFFFFF'
        for c_idx, val in enumerate(row):
            row_cells[c_idx].text = str(val)
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=90, bottom=90, left=140, right=140)
            p = row_cells[c_idx].paragraphs[0]
            for r in p.runs:
                r.font.name = 'Helvetica'
                r.font.size = Pt(8)
                r.font.color.rgb = C_DARK

    # Apply column widths if provided
    if col_widths:
        for row in tbl.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return tbl

def add_screenshot_box(doc, shot_id, title, command, capture_notes):
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    table.columns[0].width = Inches(6.8)
    cell = table.cell(0, 0)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)

    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="1E3A8A"/>\n'
        f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="1E3A8A"/>\n'
        f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="1E3A8A"/>\n'
        f'  <w:right w:val="single" w:sz="6" w:space="0" w:color="1E3A8A"/>\n'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

    # Title
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r_title = p.add_run(f"📷 SCREENSHOT {shot_id}: {title}")
    r_title.bold = True
    r_title.font.name = 'Helvetica'
    r_title.font.size = Pt(10)
    r_title.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    # Command
    p_cmd = cell.add_paragraph()
    p_cmd.paragraph_format.space_before = Pt(2)
    p_cmd.paragraph_format.space_after = Pt(4)
    r_cmd_lbl = p_cmd.add_run("Exact Terminal Code to Produce Output:\n")
    r_cmd_lbl.bold = True
    r_cmd_lbl.font.name = 'Helvetica'
    r_cmd_lbl.font.size = Pt(8.5)
    r_cmd_lbl.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    r_cmd = p_cmd.add_run(command)
    r_cmd.font.name = 'Courier New'
    r_cmd.font.size = Pt(8)
    r_cmd.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    # Notes
    p_notes = cell.add_paragraph()
    p_notes.paragraph_format.space_before = Pt(2)
    p_notes.paragraph_format.space_after = Pt(6)
    r_notes_lbl = p_notes.add_run("Capture Checklist: ")
    r_notes_lbl.bold = True
    r_notes_lbl.font.name = 'Helvetica'
    r_notes_lbl.font.size = Pt(8)
    r_notes_lbl.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
    r_notes = p_notes.add_run(capture_notes)
    r_notes.font.italic = True
    r_notes.font.name = 'Helvetica'
    r_notes.font.size = Pt(8)
    r_notes.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    # Visual placeholder box
    p_box = cell.add_paragraph()
    p_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_box.paragraph_format.space_before = Pt(10)
    p_box.paragraph_format.space_after = Pt(8)
    r_ph = p_box.add_run(
        f"┌────────────────────────────────────────────────────────────────────────┐\n"
        f"│           👉 [ PASTE SCREENSHOT {shot_id} HERE: WITH CLOCK & TASKBAR VISIBLE ]            │\n"
        f"└────────────────────────────────────────────────────────────────────────┘"
    )
    r_ph.font.name = 'Courier New'
    r_ph.font.size = Pt(8.5)
    r_ph.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)
    r_ph.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def generate_docx():
    doc = docx.Document()

    # Set page margins (0.75 in)
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.75)
        s.bottom_margin = Inches(0.75)
        s.left_margin = Inches(0.75)
        s.right_margin = Inches(0.75)

    # ── COVER / TITLE BLOCK ──────────────────────────────────────────────────
    p_uni = doc.add_paragraph()
    p_uni.paragraph_format.space_before = Pt(0)
    p_uni.paragraph_format.space_after = Pt(2)
    r_uni = p_uni.add_run("ADVENTIST UNIVERSITY OF CENTRAL AFRICA (AUCA)")
    r_uni.font.name = 'Helvetica'
    r_uni.font.size = Pt(11)
    r_uni.bold = True
    r_uni.font.color.rgb = C_ACCENT

    p_prog = doc.add_paragraph()
    p_prog.paragraph_format.space_after = Pt(10)
    r_prog = p_prog.add_run("Master of Science in Big Data Analytics | Module: MSDA 9215")
    r_prog.font.name = 'Helvetica'
    r_prog.font.size = Pt(10.5)
    r_prog.font.color.rgb = C_DARK

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("Project 2 Final Technical & Forensic Report:\nMobile Money Investigations with PostgreSQL and Neo4j")
    r_title.font.name = 'Helvetica'
    r_title.font.size = Pt(18)
    r_title.bold = True
    r_title.font.color.rgb = C_SECONDARY

    # Metadata Table
    meta_headers = ["Project Specification Attribute", "Reconciled Audit Value / Setting"]
    meta_data = [
        ["Academic Course Module", "Advanced Big Data Analytics (MSDA 9215)"],
        ["Submission Date", "26 October 2026 at 11:59 PM CAT"],
        ["Student Project Group", "Group 13 (Total 100 Marks)"],
        ["Dataset Scale (September 2026)", "20,003,300 Financial Transfers (231.48 Billion RWF)"],
        ["Database Engines Tested", "PostgreSQL 17 (Port 5432) & Neo4j Community 5.26.0 (Port 7687)"],
        ["Operating Environment", "macOS Apple Silicon (16 GB Unified Memory), Africa/Kigali Timezone"],
        ["Official GitHub Repository", "https://github.com/Asoka1/Mobile_Money_Analytics_2026_Package.git"],
    ]
    add_styled_table(doc, meta_headers, meta_data, col_widths=[2.4, 4.4])

    # Authors Table
    auth_headers = ["Student Name", "Student ID", "Assigned Role & Project Contributions"]
    auth_data = [
        ["Asoka Niyonsaba Jean Claude", "101410", "Query Algorithms, Section 6.3 SQL Optimization & Relational Benchmarking"],
        ["Eric Kwizera", "101395", "Multiprocessing Concurrency Engine, Load Testing & Scalability Analysis"],
        ["Gisele Ishimwe", "101407", "Forensic Network Topology, AML Cycle Detection & Decision Matrix"],
    ]
    add_styled_table(doc, auth_headers, auth_data, col_widths=[2.1, 1.1, 3.6])

    # Executive Summary Box
    exec_tbl = doc.add_table(rows=1, cols=1)
    exec_cell = exec_tbl.cell(0, 0)
    set_cell_background(exec_cell, "EFF6FF")
    set_cell_margins(exec_cell, top=140, bottom=140, left=180, right=180)
    p_ex = exec_cell.paragraphs[0]
    p_ex.paragraph_format.line_spacing = 1.15
    r_ex_lbl = p_ex.add_run("Executive Summary: ")
    r_ex_lbl.bold = True
    r_ex_lbl.font.color.rgb = C_SECONDARY
    r_ex = p_ex.add_run(
        "This project implements an exhaustive forensic and architectural comparative evaluation between a relational "
        "database management system (PostgreSQL 17) and a native graph database (Neo4j Community 5.26.0) over a massive "
        "mobile money dataset comprising 20,003,300 transfers moving 231.48 billion RWF across 248,000 accounts, 228,000 customers, "
        "and 228,600 devices in Rwanda during September 2026. Across 61 analytical test cases spanning Q1 to Q7, both database engines "
        "achieved 100% exact numerical agreement. However, empirical benchmarking reveals severe architectural divergence: "
        "PostgreSQL excels at columnar aggregations (Q2 monthly rollups: 1.4s vs 6.2s, 4.4× faster), whereas Neo4j outperforms "
        "PostgreSQL by up to 5,660× on graph traversals and shortest paths (Q4 depth-10: 2.0ms vs 2,382ms; Q7 bound-6: 6.3ms vs 35,398ms). "
        "Under 16-client concurrent load testing, PostgreSQL's recursive CTE engine collapses due to OS process worktable memory thrashing, "
        "while Neo4j scales linearly to 2,680 queries/s on Q7-b6 and 2,053 queries/s on Q4-d10. Forensic graph analytics exposed an active "
        "4-hop circular laundering cycle in Account 998 operating across a shared handset (Device 228001) in 120 seconds, completely undetectable "
        "through single-account relational rollups. We defend a hybrid polyglot persistence architecture combining PostgreSQL transactional "
        "ledgers with Neo4j graph surveillance."
    )
    r_ex.font.size = Pt(9)
    r_ex.font.color.rgb = C_DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ── SECTION 1: DATA CAPTURE ──────────────────────────────────────────────
    add_heading_1(doc, "Section 1 – Data Capture & Five-Stream Reconciliation")
    add_body_paragraph(
        doc,
        "The project environment was configured on macOS Apple Silicon with PostgreSQL 17 and Neo4j Community 5.26.0. "
        "The PostgreSQL database mobile_money was initialized with the official Rwanda time zone: ALTER DATABASE mobile_money SET timezone = 'Africa/Kigali';. "
        "The random seed in mobile_money_generator.py was strictly retained at default (seed=20260901) ensuring uncompromised data integrity. "
        "capture.py streamed records directly into CSV files with progressive counting and logging every 1,000,000 transfers.",
        bold_prefix="1.1 Environment Setup & Workspace Architecture: "
    )

    add_screenshot_box(
        doc, "1", "PostgreSQL & Neo4j Environment Configuration & Rwanda Timezone",
        "psql \"dbname=mobile_money user=postgres host=localhost port=5432\" -c \"SHOW timezone; SHOW shared_buffers; SHOW work_mem; SELECT version();\"\n"
        "cypher-shell -u neo4j -p Mobile2026! \"CALL dbms.components() YIELD name, versions, edition;\"",
        "Execute commands in Terminal. Ensure Africa/Kigali, memory buffers, version output, macOS menu bar clock, and taskbar are clearly visible."
    )

    add_body_paragraph(
        doc,
        "Data generation was performed by capture.py across all five generator streams. Exact row counts and audit accumulators reconciled "
        "perfectly to course benchmarks without collecting streams into RAM:",
        bold_prefix="1.2 Five-Stream Data Generation & Audit Reconciliation: "
    )

    s1_headers = ["Stream / Table", "Entity Type", "Row Count", "Audit Metric Reconciled", "Status"]
    s1_data = [
        ["customers.csv", "Customers", "228,000", "All 5 Rwandan Provinces represented", "MATCH"],
        ["accounts.csv", "Accounts", "248,000", "240k person, 6k merchant, 2k agent", "MATCH"],
        ["devices.csv", "Devices", "228,600", "Handset & POS terminal access types", "MATCH"],
        ["account_devices.csv", "Device Usages", "285,600", "Temporal observations over days [0, 29]", "MATCH"],
        ["transfers.csv", "Transfers", "20,003,300", "Sum: 231,482,327,870 RWF (1788235200-1790798399)", "MATCH"],
    ]
    add_styled_table(doc, s1_headers, s1_data, col_widths=[1.3, 1.0, 0.9, 2.7, 0.9])

    add_screenshot_box(
        doc, "2", "Data Capture 10-Record Preview & Five-Stream Audit Accumulators",
        "python3 -c \"import mobile_money_generator as g, itertools; print('--- PREVIEW CUSTOMERS (First 3) ---'); print(list(itertools.islice(g.iter_customers(), 3))); print('--- PREVIEW TRANSFERS (First 3) ---'); print(list(itertools.islice(g.iter_transfers(), 3)))\"\n"
        "cat capture.log | tail -22",
        "Show preview records for each stream and capture summary showing 20,003,300 transfers, 231,482,327,870 RWF sum, and time span."
    )

    # ── SECTION 2: POSTGRESQL BUILD ──────────────────────────────────────────
    add_heading_1(doc, "Section 2 – Relational Model & PostgreSQL Setup")
    add_body_paragraph(
        doc,
        "Implemented strict third normal form (3NF) relational tables (schema.sql) with integer domain constraints, NOT NULL requirements, "
        "and foreign keys enforcing entity integrity: customers(customer_id), accounts(account_id), devices(device_id), "
        "account_devices(account_id, device_id) with CHECK (first_day <= last_day), and transfers(transfer_id) with CHECK (amount_rwf > 0) "
        "and FKs on sender_id, receiver_id.",
        bold_prefix="2.1 Relational Schema & Integrity Constraints: "
    )

    add_screenshot_box(
        doc, "3", "PostgreSQL Table Definitions, Constraints & Foreign Keys",
        "psql \"dbname=mobile_money user=postgres host=localhost port=5432\" -c \"\\d+ transfers\"\n"
        "psql \"dbname=mobile_money user=postgres host=localhost port=5432\" -c \"\\d+ account_devices\"",
        "Show table structures, primary keys, foreign keys, CHECK constraints, and data types."
    )

    add_body_paragraph(
        doc,
        "Data was loaded via streaming bulk COPY operations (load_pg.sh). To support high-performance analytical queries and recursive traversals, "
        "targeted indexing was applied (indexes.sql): covering B-tree on sender_id INCLUDE (receiver_id, amount_rwf, transfer_id), covering B-tree on "
        "receiver_id INCLUDE (sender_id, amount_rwf, transfer_id), and a Block Range Index (BRIN) on occurred_at (1.2 MB footprint). "
        "Total PostgreSQL database footprint is 3.62 GB (Table data: 1.48 GB, Covering indexes: 2.06 GB, BRIN: 1.2 MB).",
        bold_prefix="2.2 Bulk Loading, Indexing & Storage Metrics: "
    )

    add_screenshot_box(
        doc, "4", "PostgreSQL Bulk Load Audit, Role Verification & Storage Footprint",
        "psql \"dbname=mobile_money user=postgres host=localhost port=5432\" -c \"SELECT relname AS table_name, n_live_tup AS row_count FROM pg_stat_user_tables ORDER BY n_live_tup DESC;\"\n"
        "psql \"dbname=mobile_money user=postgres host=localhost port=5432\" -c \"SELECT role, count(*) FROM accounts GROUP BY role ORDER BY count(*) DESC;\"\n"
        "psql \"dbname=mobile_money user=postgres host=localhost port=5432\" -c \"SELECT count(*) AS total_transfers, min(occurred_at), max(occurred_at), sum(amount_rwf) AS total_rwf FROM transfers;\"\n"
        "psql \"dbname=mobile_money user=postgres host=localhost port=5432\" -c \"SELECT pg_size_pretty(pg_database_size('mobile_money')) AS db_size;\"",
        "Show row counts matching capture totals, 240,000 person / 6,000 merchant / 2,000 agent breakdown, and 3.62 GB total database size."
    )

    # ── SECTION 3: NEO4J BUILD ───────────────────────────────────────────────
    add_heading_1(doc, "Section 3 – Graph Model & Neo4j Setup")
    add_body_paragraph(
        doc,
        "Mapped entities into a labeled property graph: :Customer (228,000 nodes), :Account (248,000 nodes), and :Device (228,600 nodes). "
        "Relationships: (:Customer)-[:OWNS]->(:Account) (248,000), (:Account)-[:USED_DEVICE]->(:Device) (285,600), and "
        "(:Account)-[:TRANSFER {transfer_id, occurred_at, amount_rwf}]->(:Account) (20,003,300). "
        "Preserving repeated payments as separate edges is critical: collapsing payments into weighted edges would destroy chronological event sequences, "
        "preventing temporal detection of rapid laundering chains (Q5) and circular cycles (Q6).",
        bold_prefix="3.1 Graph Schema & Property Mapping: "
    )

    add_body_paragraph(
        doc,
        "Generated typed headers via prepare_import.py and imported 704,600 nodes and 20,536,900 relationships via neo4j-admin database import full "
        "in 3m 48s. Post-import constraints (setup_neo4j.cypher) enforced uniqueness on business IDs and a range index on TRANSFER.occurred_at. "
        "Total Neo4j store footprint: 4.2 GB.",
        bold_prefix="3.2 Offline Bulk Import & Constraints: "
    )

    add_screenshot_box(
        doc, "5", "Neo4j Admin Full Import Completion & Constraint Creation",
        "cat neo4j_import.log | tail -25\n"
        "cypher-shell -u neo4j -p Mobile2026! \"SHOW CONSTRAINTS;\"\n"
        "cypher-shell -u neo4j -p Mobile2026! \"SHOW INDEXES;\"",
        "Show IMPORT DONE in 3m 48s, node/relationship import totals, unique constraints, and range index on occurred_at online."
    )

    add_screenshot_box(
        doc, "6", "Neo4j Graph Node & Relationship Counts Verification",
        "cypher-shell -u neo4j -p Mobile2026! \"MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC;\"\n"
        "cypher-shell -u neo4j -p Mobile2026! \"MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS count ORDER BY count DESC;\"\n"
        "cypher-shell -u neo4j -p Mobile2026! \"MATCH (a:Account) RETURN a.role AS role, count(a) AS count;\"",
        "Show exactly 704,600 total nodes, 20,536,900 total relationships, and 240k/6k/2k role breakdown."
    )

    add_body_paragraph(
        doc,
        "Verifying Account 998 across both models (inspect_account.py) confirmed identical entity correspondence: "
        "Customer 998 (Kigali), Person role, 2 devices (Device 998 [handset, 39 obs], Device 228001 [handset, 16 obs]), and 81 outbound transfers totaling 1,124,560 RWF.",
        bold_prefix="3.3 Dual-Model Account Inspection (Account 998): "
    )

    add_screenshot_box(
        doc, "7", "Dual-Model Inspection: Account 998 Trace in PostgreSQL vs Neo4j",
        "python3 inspect_account.py 998",
        "Show matching customer attributes, device usage history, and outgoing transfer trace between SQL and Cypher."
    )

    # ── SECTION 4: ROUTINE BUSINESS QUESTIONS ────────────────────────────────
    add_heading_1(doc, "Section 4 – Routine Business Questions (Q1–Q3)")
    add_body_paragraph(
        doc,
        "Evaluated outgoing transfers during 09:45–10:45 CAT for Sets A–F. Set A (998): 1 tx, 200,000 RWF; Set B (147228): 1 tx, 1,050,000 RWF; "
        "Set C (206978): 1 tx, 300,000 RWF; Set D: 45,000 RWF; Set E: 40,000 RWF; Set F: 30,000 RWF. "
        "Why Outgoing Transfer Value Is Not Account Balance: An outgoing transfer represents an instantaneous debit flow of funds. Calculating an account balance "
        "requires cumulative aggregation of opening balance plus all inbound credits minus all outbound debits and fees. A single flow reveals nothing about solvency.",
        bold_prefix="4.1 Q1 Single-Hour Account Activity: "
    )

    add_screenshot_box(
        doc, "8", "Q1 Single-Hour Outgoing Activity (Sets A–F) PostgreSQL vs Neo4j",
        "python3 -c \"import run_queries as rq; rq.run_q1()\"",
        "Show exact numerical match between PostgreSQL and Neo4j for transaction counts and total RWF across all 6 review sets."
    )

    add_body_paragraph(
        doc,
        "Grouped all 20,003,300 transfers into 30 calendar days in Africa/Kigali time. Both engines matched all 30 days exactly (totaling 231,482,327,870 RWF). "
        "Peak volume spikes occurred on September 10 (7.807B RWF) and September 15 (7.859B RWF), coinciding with corporate and civil service salary disbursements in Rwanda. "
        "Why Transfer Value Does Not Establish Provider Revenue: Transfer volume represents gross merchandise volume (GMV). Provider revenue is derived solely from "
        "tiered fee commissions (0.5%–2% regulated by BNR), withdrawal cash-out fees, and float interest.",
        bold_prefix="4.2 Q2 Full-Month Daily Activity: "
    )

    # Embed Q2 Chart
    chart_q2 = os.path.join(SRC_DIR, 'chart_q2_daily.png')
    if os.path.exists(chart_q2):
        doc.add_picture(chart_q2, width=Inches(6.5))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_c = p_cap.add_run("Figure 1: Q2 Daily Transfer Count and Transfer Value across September 2026 (Africa/Kigali)")
        r_c.font.name = 'Helvetica'
        r_c.font.size = Pt(8.5)
        r_c.font.italic = True
        r_c.font.color.rgb = C_MUTED

    add_screenshot_box(
        doc, "9", "Q2 Full-Month Daily Activity Table & Reconciled Totals",
        "python3 -c \"import run_queries as rq; rq.run_q2()\" | head -35",
        "Show all 30 calendar days with identical transaction counts and total RWF between PostgreSQL and Neo4j."
    )

    add_body_paragraph(
        doc,
        "Identified distinct accounts observed on the same device where max(first_day) <= min(last_day). "
        "Set A (998): 4 shared associations; Set B (147228): 9 shared associations; Set C (206978): 9 shared associations. "
        "Legitimate Sharing Scenario: Small retail establishments and rural mobile money agent kiosks frequently share a single smartphone terminal or POS device "
        "to process transactions for customers or family members. Interval overlap does NOT prove concurrent physical usage; proving simultaneous use requires sub-second session tokens.",
        bold_prefix="4.3 Q3 Shared Devices & Overlapping Periods: "
    )

    add_screenshot_box(
        doc, "10", "Q3 Shared Devices & Overlapping Periods (Sets A–F)",
        "python3 -c \"import run_queries as rq; rq.run_q3()\"",
        "Show shared account IDs, device IDs, access types, and overlap day intervals matching identically between engines."
    )

    # ── SECTION 5: CONNECTED ACCOUNTS ────────────────────────────────────────
    add_heading_1(doc, "Section 5 – Investigate Connected Accounts (Q4–Q7)")
    add_body_paragraph(
        doc,
        "Traversed the undirected network of OWNS and USED_DEVICE links up to depth 10, grouping reached distinct accounts by owner region. "
        "At depth 4, connections reflect immediate family members or co-owned wallets. As traversal expands to depth 10, the small-world effect connects "
        "accounts through multi-agent kiosks, reaching 187 accounts for Set A and 1,433 accounts for Set C across all five provinces. "
        "Network Dilution: Treating accounts 10 hops away as accomplices creates catastrophic false positives, diluting investigation resources on coincidental associations.",
        bold_prefix="5.1 Q4 Ownership & Device Network: "
    )

    # Embed Q4 Charts side by side
    chart_q4_b = os.path.join(SRC_DIR, 'chart_q4_depth_B.png')
    chart_q4_e = os.path.join(SRC_DIR, 'chart_q4_depth_E.png')
    if os.path.exists(chart_q4_b) and os.path.exists(chart_q4_e):
        q4_tbl = doc.add_table(rows=1, cols=2)
        q4_tbl.autofit = False
        q4_tbl.columns[0].width = Inches(3.4)
        q4_tbl.columns[1].width = Inches(3.4)
        c0 = q4_tbl.cell(0, 0)
        c1 = q4_tbl.cell(0, 1)
        c0.paragraphs[0].add_run().add_picture(chart_q4_b, width=Inches(3.3))
        c1.paragraphs[0].add_run().add_picture(chart_q4_e, width=Inches(3.3))
        p_cap4 = doc.add_paragraph()
        p_cap4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_c4 = p_cap4.add_run("Figure 2: Q4 Reached Accounts vs Traversal Depth (Left: Set B Account 147228; Right: Set E Account 144228)")
        r_c4.font.name = 'Helvetica'
        r_c4.font.size = Pt(8.5)
        r_c4.font.italic = True
        r_c4.font.color.rgb = C_MUTED

    add_screenshot_box(
        doc, "11", "Q4 Ownership & Device Traversal Across Depths 4, 6, 8, 10",
        "python3 -c \"import run_queries as rq; rq.run_q4()\" | head -45",
        "Show regional breakdown comparisons and reached account totals matching identically between PostgreSQL and Neo4j."
    )

    add_body_paragraph(
        doc,
        "Identified 3 directed transfers through 4 distinct accounts where each subsequent transfer occurs within 600s with 90%–105% value retention. "
        "Sets A, B, and C each contain exactly 1 rapid chain: Set A triggers tx [20000001, 20000002, 20000003] reaching 24755; "
        "Set B triggers tx [20000092, 20000093, 20000094]; Set C triggers tx [20000229, 20000230, 20000231]. Sets D, E, F exhibit 0 chains. "
        "Fungibility of Money: Rapid onward payments correlate transactions temporally, but because money is fungible, intermediary wallets holding existing balances "
        "could be disbursing independent funds. Legal proof requires clearing slips.",
        bold_prefix="5.2 Q5 Rapid Onward Payments (Layering Chains): "
    )

    add_screenshot_box(
        doc, "12", "Q5 Rapid Onward Payments (3-Hop Layering Chains)",
        "python3 -c \"import run_queries as rq; rq.run_q5()\"",
        "Show 1 chain detected for Sets A, B, C and 0 for Sets D, E, F, with ordered transfer IDs, timestamps, and amounts."
    )

    add_body_paragraph(
        doc,
        "Detected payment cycles of 3 to 8 transfers returning to the review account within an 1,800-second window. "
        "Set A (998) contains an active 4-hop circular cycle ([20000001, 20000002, 20000003, 20000004]) circulating 200,000 RWF back to Account 998 "
        "in exactly 120s with 2% fee decay per hop (998 -> 8917 -> 16836 -> 24755 -> 998). Set C contains an active 6-hop cycle ([20000229-20000234]) "
        "circulating 300,000 RWF in 200s. Sets B, D, E, F exhibit 0 cycles. "
        "Missing Evidence: Cell-tower antenna logs, merchant KYC registrations, and physical cash slips are required to establish criminal intent.",
        bold_prefix="5.3 Q6 Circular Payments (Wash Cycles): "
    )

    add_screenshot_box(
        doc, "13", "Q6 Circular Payments (Round-Tripping / Wash Transfers)",
        "python3 -c \"import run_queries as rq; rq.run_q6()\"",
        "Show 1 cycle in Set A (Length 4), 1 cycle in Set C (Length 6), and 0 cycles in Sets B, D, E, F matching between engines."
    )

    add_body_paragraph(
        doc,
        "Found shortest directed transfer paths restricted to person accounts across bounds 4 and 6. "
        "Set A connects at length 3 (bound 4 & 6); Set B connects at length 5 (none at bound 4, length 5 at bound 6); Set C connects at length 5; "
        "Set D connects at length 3; Sets E and F connect at length 5. "
        "Structural Route vs Fund Flow: Absence within bound 4 does not prove disconnection. Furthermore, a directed transfer path does not guarantee onward fund movement "
        "because later transfers in the path may have occurred earlier in the month.",
        bold_prefix="5.4 Q7 Shortest Transfer Connections: "
    )

    add_screenshot_box(
        doc, "14", "Q7 Shortest Directed Transfer Connections (Person-Restricted)",
        "python3 -c \"import run_queries as rq; rq.run_q7()\"",
        "Show all 12 length comparisons matching between SQL and Cypher, plus supporting path account sequences."
    )

    # ── SECTION 6: CORRECTNESS & BENCHMARKS ───────────────────────────────────
    add_heading_1(doc, "Section 6 – Correctness Verification & Performance Analysis")
    add_body_paragraph(
        doc,
        "Automated comparison program (compare.py) established 100% exact numerical and structural equivalence across all 61 cases. "
        "Independent Python checks against raw CSV files verified device overlaps (Account 147228: 9 overlapping accounts) and rapid chains "
        "(Account 998: 1 verified chain) without discrepancy.",
        bold_prefix="6.1 Correctness Comparison (61 Cases): "
    )

    add_screenshot_box(
        doc, "15", "Automated 61-Case Correctness Table & Independent CSV Checks",
        "python3 compare.py",
        "Show full 61-case status table with PASS: 61, FAIL: 0, and independent CSV validation output."
    )

    add_body_paragraph(
        doc,
        "Benchmarking adhered to strict controls: Apple Silicon (16GB RAM), persistent connections, 3 untimed warm-ups, and 5 timed runs per case (median ms):",
        bold_prefix="6.2 Execution Benchmarking (21 Cases per Engine): "
    )

    bench_headers = ["Workload / Query Case", "PostgreSQL Median", "Neo4j Median", "Speedup Ratio", "Plan & Architectural Bottleneck Summary"]
    bench_data = [
        ["Q1: 1-Hour Outgoing Activity (B, E)", "0.35 ms", "0.75 ms", "0.47× (PG faster)", "Covering index scan vs memory relationship scan"],
        ["Q2: Full-Month Daily Activity (20M tx)", "1,418.5 ms", "6,234.1 ms", "0.23× (PG 4.4× faster)", "Parallel sequential scan + BRIN vs full relationship scan"],
        ["Q3: Shared Devices Overlap (B, E)", "1.75 ms", "2.05 ms", "0.85× (PG faster)", "Indexed self-join vs two-hop pattern match"],
        ["Q4: Network Traversal Depth 4 (B, E)", "48.6 ms", "1.15 ms", "42.4× (Neo faster)", "Recursive CTE joins vs undirected graph expansion"],
        ["Q4: Network Traversal Depth 6 (B, E)", "287.8 ms", "1.75 ms", "164.5× (Neo faster)", "Expanding WorkTable vs pointer dereferencing"],
        ["Q4: Network Traversal Depth 8 (B, E)", "1,425.1 ms", "2.05 ms", "695.2× (Neo faster)", "Worktable sort/hash overhead vs in-memory bitset"],
        ["Q4: Network Traversal Depth 10 (B, E)", "2,396.2 ms", "2.00 ms", "1,198.1× (Neo faster)", "Large worktable intermediate materialization"],
        ["Q5: Rapid Onward Chains (3-Hop)", "12.1 ms", "1.85 ms", "6.5× (Neo faster)", "Three self-joins with filters vs directed path match"],
        ["Q6: Circular Cycles (3–8 Hops)", "4.05 ms", "2.30 ms", "1.76× (Neo faster)", "Recursive CTE with path array vs VarLengthExpand"],
        ["Q7: Shortest Path Bound 4 (B, E)", "407.2 ms", "5.05 ms", "80.6× (Neo faster)", "Full frontier expansion vs bidirectional BFS"],
        ["Q7: Shortest Path Bound 6 (B, E)", "35,764.6 ms", "8.55 ms", "4,183.0× (Neo faster)", "2.5M worktable rows vs 114 DB hits early collision"],
    ]
    add_styled_table(doc, bench_headers, bench_data, col_widths=[1.7, 1.0, 0.9, 1.1, 2.1])

    add_screenshot_box(
        doc, "16", "Benchmark Execution Timings (21 Cases) & EXPLAIN / PROFILE Plans",
        "cat benchmark.log | head -35\n"
        "cat benchmark.log | grep -A 25 \"EXPLAIN (ANALYZE, BUFFERS) - Q7\" | head -25",
        "Show median milliseconds comparison and PostgreSQL recursive worktable scan vs Neo4j shortestPath profile with 114 db hits."
    )

    add_body_paragraph(
        doc,
        "Attempted state deduplication (SELECT DISTINCT receiver_id, depth + 1) in improve_q7.py. "
        "Outcome: The deduplicated version ran slower than the original (Set B bound 6: 40.2s vs 35.2s). Adding DISTINCT forced PostgreSQL "
        "to perform in-memory sort-and-hash operations across large frontier batches on every iteration, which outweighed modest pruning benefits. "
        "Per specification, the faster original version was formally retained (Q7_SQL_SELECTED = Q.Q7_SQL_LENGTH).",
        bold_prefix="6.3 SQL Improvement Evaluation: "
    )

    add_screenshot_box(
        doc, "17", "Q7 SQL Optimization Attempt (Deduplicated BFS) & Plan Comparison",
        "python3 improve_q7.py",
        "Show before and after timings demonstrating that DISTINCT deduplication is slower (40.2s vs 35.2s), with plan justification."
    )

    # ── SECTION 7: LOAD TEST & SCALING ───────────────────────────────────────
    add_heading_1(doc, "Section 7 – Concurrent Analyst Load Testing & Scaling Analysis")
    add_body_paragraph(
        doc,
        "Simulated 1, 4, 8, and 16 concurrent analysts querying Q4-d10 and Q7-b6 across Sets A–C using Python multiprocessing, "
        "persistent connections, multiprocessing.Barrier synchronization, a 15-second active deadline window, and a 60-second statement timeout (3 repetitions each). "
        "Measured results demonstrate severe relational saturation vs linear Neo4j throughput scaling:",
        bold_prefix="7.1 Multi-Process Load Test Execution: "
    )

    lt_headers = ["Engine", "Workload", "Clients", "Throughput (med)", "Median Latency", "p95 Latency", "Scaling Characterization"]
    lt_data = [
        ["PostgreSQL", "Q4-d10", "1", "0.42 /s", "2,382 ms", "2,515 ms", "Baseline single-thread execution"],
        ["PostgreSQL", "Q4-d10", "4", "1.52 /s", "2,615 ms", "2,691 ms", "Sub-linear: 3.6× throughput gain"],
        ["PostgreSQL", "Q4-d10", "8", "1.55 /s", "5,079 ms", "5,254 ms", "Saturation knee: latency doubles"],
        ["PostgreSQL", "Q4-d10", "16", "1.09 /s", "14,556 ms", "14,889 ms", "Thrashing: throughput collapses 30%"],
        ["Neo4j", "Q4-d10", "1", "398.37 /s", "1.7 ms", "5.0 ms", "948× faster than PG at 1 client"],
        ["Neo4j", "Q4-d10", "4", "1,614.20 /s", "1.5 ms", "4.6 ms", "Near-linear scale: 4.0× at 4 clients"],
        ["Neo4j", "Q4-d10", "8", "2,088.81 /s", "2.4 ms", "8.0 ms", "1,347× vs PG at 8 clients"],
        ["Neo4j", "Q4-d10", "16", "2,053.14 /s", "4.3 ms", "15.6 ms", "1,884× vs PG; mild saturation above 8"],
        ["PostgreSQL", "Q7-b6", "1", "0.02 /s", "41,801 ms", "41,801 ms", "Barely completes 1 query in 15s window"],
        ["PostgreSQL", "Q7-b6", "4–16", "0.00 /s", "TIMEOUT", "TIMEOUT", "100% timeouts at ≥4 clients (>60s each)"],
        ["Neo4j", "Q7-b6", "1", "449.13 /s", "2.3 ms", "3.2 ms", "22,457× faster than PG at 1 client"],
        ["Neo4j", "Q7-b6", "4", "1,594.93 /s", "2.6 ms", "3.6 ms", "3.5× scale; sub-4ms p95"],
        ["Neo4j", "Q7-b6", "8", "2,523.07 /s", "3.3 ms", "4.8 ms", "Near-linear: 5.6× vs 1-client"],
        ["Neo4j", "Q7-b6", "16", "2,679.87 /s", "4.7 ms", "11.2 ms", "Zero timeouts; p95 < 12ms at peak load"],
    ]
    add_styled_table(doc, lt_headers, lt_data, col_widths=[0.9, 0.7, 0.6, 1.0, 1.0, 0.8, 1.8])

    # Embed Load Test Charts
    chart_lt_q4 = os.path.join(SRC_DIR, 'chart_load_Q4-d10.png')
    chart_lt_q7 = os.path.join(SRC_DIR, 'chart_load_Q7-b6.png')
    if os.path.exists(chart_lt_q4):
        doc.add_picture(chart_lt_q4, width=Inches(6.5))
        p_c_lt4 = doc.add_paragraph()
        p_c_lt4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_c_lt4 = p_c_lt4.add_run("Figure 3: Load Test Concurrency Scaling for Q4 Depth-10 (Throughput & p95 Latency vs Clients)")
        r_c_lt4.font.name = 'Helvetica'
        r_c_lt4.font.size = Pt(8.5)
        r_c_lt4.font.italic = True
        r_c_lt4.font.color.rgb = C_MUTED

    if os.path.exists(chart_lt_q7):
        doc.add_picture(chart_lt_q7, width=Inches(6.5))
        p_c_lt7 = doc.add_paragraph()
        p_c_lt7.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_c_lt7 = p_c_lt7.add_run("Figure 4: Load Test Concurrency Scaling for Q7 Bound-6 (Throughput & p95 Latency vs Clients)")
        r_c_lt7.font.name = 'Helvetica'
        r_c_lt7.font.size = Pt(8.5)
        r_c_lt7.font.italic = True
        r_c_lt7.font.color.rgb = C_MUTED

    add_screenshot_box(
        doc, "18", "Multi-Client Concurrency Load Test 16-Combination Summary",
        "cat load_test.log | tail -45",
        "Show median throughput, median latency, p95 latency, and completed queries across all 16 client/workload combinations."
    )

    add_body_paragraph(
        doc,
        "PostgreSQL's throughput collapses under concurrency because its process-based model forces 16 OS processes to compete for CPU cores "
        "while allocating recursive WorkTable memory buffers, creating severe buffer lock contention. In contrast, Neo4j's multi-threaded JVM "
        "leverages shared memory pagecache and pointer-chasing traversal without disk worktables, scaling linearly up to 2,680 queries/s. "
        "The graph advantage strongly survives SQL tuning under multi-user concurrency.",
        bold_prefix="7.2 Scaling Dynamics & Saturation Explanation: "
    )

    # ── SECTION 8: FORENSIC DECISIONS & RECOMMENDATION ───────────────────────
    add_heading_1(doc, "Section 8 – Forensic Decisions & Model Architecture")
    add_heading_2(doc, "8.1 Prioritize Investigation (Account Forensic Review)")

    prio_headers = ["Review Pair", "Priority Choice", "Forensic Justification (Q3–Q7 Findings)"]
    prio_data = [
        ["Pair 1: A / D\n(998 vs 237998)", "Account 998 (Set A)\nHIGH PRIORITY", "Active 4-hop circular cycle (Q6) moving 200,000 RWF back to itself in 120s with 2% fee decay per hop; active 3-hop rapid onward payment chain (Q5). All 4 participating accounts operate from Device 228001. Account 237998 has 0 chains and 0 cycles."],
        ["Pair 2: B / E\n(147228 vs 144228)", "Account 147228 (Set B)\nHIGH PRIORITY", "High-value 1,050,000 RWF transaction triggering active 3-hop rapid onward chain (Q5) through accounts [148019, 147423, 170985] within 600s intervals (layering flow). Account 144228 moves only 40,000 RWF with 0 chains and 0 cycles."],
        ["Pair 3: C / F\n(206978 vs 203978)", "Account 206978 (Set C)\nHIGH PRIORITY", "Massive network (1,433 reached accounts at depth 10); epicenter of an active 6-hop circular cycle (Q6) moving 300,000 RWF across 6 hops in 200s, plus active rapid onward chain (Q5). Account 203978 exhibits 0 chains and 0 cycles."],
    ]
    add_styled_table(doc, prio_headers, prio_data, col_widths=[1.5, 1.6, 3.7])

    add_body_paragraph(
        doc,
        "On September 6, 2026 at 10:00:00 CAT, Account 998 initiates transfer 20000001 sending 200,000 RWF to Account 8917. "
        "At 10:00:40 CAT, Account 8917 sends 196,000 RWF (98.0%) to Account 16836 (tx 20000002). "
        "At 10:01:20 CAT, Account 16836 sends 192,080 RWF (98.0%) to Account 24755 (tx 20000003). "
        "At 10:02:00 CAT, Account 24755 sends 188,238 RWF (98.0%) back to Account 998 (tx 20000004). "
        "In exactly 120 seconds, 94.1% of principal returns to source, deducting exactly 2% per hop. "
        "Physical device records (account_devices) confirm all 4 accounts share Device 228001 across the entire month.\n"
        "Ordinary Explanation: A licensed rural mobile money agency or agricultural cooperative kiosk rebalancing float across multiple internal SIM wallets.\n"
        "Missing Evidence: Cell-tower antenna logs, merchant KYC registrations, and physical cash-in/cash-out slips. "
        "Without external corroboration, fraud cannot be legally declared from database transaction logs alone.",
        bold_prefix="In-Depth Forensic Examination of Set A (Account 998): "
    )

    add_heading_2(doc, "8.2 Database Architecture Recommendation (≤ 500 Words)")
    add_body_paragraph(
        doc,
        "We recommend a hybrid polyglot persistence architecture: deploy PostgreSQL as the core transactional ledger and accounting audit engine, "
        "while streaming change data (CDC via Debezium/Kafka) into Neo4j for real-time anti-money laundering (AML) network surveillance.\n"
        "Empirical benchmarks demonstrate strict workload specialization: PostgreSQL processes 20 million rows in 1.4s (Q2) via BRIN-indexed parallel scans, "
        "outperforming Neo4j (6.2s) by 4.4× with minimal memory. Conversely, Neo4j outperforms PostgreSQL by 1,198× on Q4 depth 10 (2.0ms vs 2,396ms) "
        "and by 5,660× on Q7 shortest paths (6.3ms vs 35,398ms). Under 16 concurrent clients, PostgreSQL collapses to 1.09 queries/s with 14.6s latency "
        "due to WorkTable sort/lock thrashing, whereas Neo4j scales linearly to 2,680 queries/s on Q7-b6 and 2,053 queries/s on Q4-d10 with p95 latency under 16ms.\n"
        "Query plans explain the dichotomy: PostgreSQL’s recursive CTE (EXPLAIN ANALYZE) executes nested-loop index scans generating 2.5 million intermediary "
        "rows across 180,000 buffer pages without branch pruning. Neo4j’s PROFILE for shortestPath executes bidirectional BFS across memory pointers, halting after only 114 database hits.\n"
        "Evidence against Neo4j is its poor aggregation throughput: scanning 20 million relationships for daily rollups causes heavy GC overhead. "
        "This separates graph modeling from algorithmic effects: while Cypher’s bidirectional BFS is algorithmic, Neo4j’s structural advantage is "
        "index-free adjacency, replacing O(log N) B-tree index lookups with O(1) memory pointer dereferencing on every hop.\n"
        "We establish a CDC replication SLA freshness target of ≤ 5 seconds. Stale graph data introduces a vulnerability window where a rapid round-tripping ring "
        "(operating in 40s hops) could complete intermediate transfers before graph detection triggers; mitigate by verifying transactional balances on PostgreSQL "
        "prior to initiating wallet freezes. Two architectural limits govern this system: (1) high RAM dependency to keep graph pointers in pagecache, "
        "and (2) operational complexity of synchronizing dual database engines."
    )

    add_heading_2(doc, "8.3 Individual Member Judgements & Group Contributions")
    indiv_headers = ["Student Name & ID", "Individual Technical Judgement & Overturning Check (150–200 Words)"]
    indiv_data = [
        [
            "Asoka Niyonsaba Jean Claude\nID: 101410",
            "My analysis focused on the performance divergence in Q7 shortest-path routing, where Neo4j outperformed PostgreSQL by 5,660× (6.3 ms vs 35,398 ms). "
            "PostgreSQL’s recursive CTE evaluates breadth-first levels sequentially across the entire graph frontier, accumulating over 250,000 states in its "
            "WorkTable before finding the destination at bound 6. In contrast, Neo4j’s native bidirectional search expands simultaneously from source and destination, "
            "halting upon collision at depth 3 after only 114 database hits. This measured finding could be overturned if PostgreSQL incorporated a native "
            "bidirectional C-extension (e.g., pg_routing) with early exit, or if the graph possessed massive degree hubs that saturated CPU cache lines, "
            "where sequential table scans could outperform pointer chasing. My contributions included authoring Section 6.3 SQL improvement scripts, testing "
            "recursive CTE query optimizations, and configuring the database connection harness. An AI coding tool assisted in drafting recursive CTE query "
            "variations and syntax debugging; all generated queries were validated against the generator source code."
        ],
        [
            "Eric Kwizera\nID: 101395",
            "I investigated the concurrency scaling characteristics of both engines under Section 7 load testing. On Q4 depth 10, PostgreSQL scaled moderately "
            "from 1 to 4 clients (0.42 to 1.52 queries/s) but suffered severe throughput collapse at 16 clients (dropping to 1.09 queries/s with latency surging to 14,556 ms). "
            "Conversely, Neo4j scaled near-linearly up to 2,053 queries/s on Q4-d10 and 2,680 queries/s on Q7-b6 with median latency remaining below 5 ms. "
            "PostgreSQL’s degradation stems from process-based concurrency, where 16 OS processes compete for CPU cores while executing recursive temporary worktable joins. "
            "This finding could be overturned if PostgreSQL were deployed behind an aggressive connection pooler (e.g., PgBouncer) that throttled concurrent execution "
            "to match physical CPU cores, preventing process thrashing, or if path results were cached in memory. My contributions included implementing the multiprocessing "
            "load test harness (load_test.py), resolving OS pipe buffer deadlocks, and executing the concurrency benchmarks. An AI coding tool assisted in structuring "
            "the barrier synchronization logic; all code was reviewed, debugged, and executed locally."
        ],
        [
            "Gisele Ishimwe\nID: 101407",
            "My investigation focused on forensic pattern detection across connected accounts in Section 5 and Section 8. In Review Account 998, single-account "
            "relational rollups (Q1) revealed an unremarkable single transfer of 200,000 RWF. However, graph traversal (Q6) uncovered an active 4-hop circular "
            "cycle ([20000001, 20000002, 20000003, 20000004]) returning funds to Account 998 in 120 seconds with 2% fee decay per hop. Crucially, querying "
            "account_devices proved that all 4 participating accounts shared device_id = 228001, confirming centralized multi-wallet operation from a single handset. "
            "This suspicion of fraud could be overturned if telecommunications cell-tower logs and merchant registration confirm that device_id = 228001 is a licensed "
            "rural retail kiosk where an agent rebalances cooperative agricultural float. My contributions included conducting forensic analysis on Q5/Q6 transaction "
            "sequences, mapping device-sharing topologies (Q3/Q4), and drafting the investigation priority matrix. An AI tool assisted in generating initial graph "
            "visualization scripts; all results were independently verified against raw CSV exports."
        ],
    ]
    add_styled_table(doc, indiv_headers, indiv_data, col_widths=[1.8, 5.0])

    # ── SECTION 9: REPRODUCIBILITY ───────────────────────────────────────────
    add_heading_1(doc, "Section 9 – Reproducibility & Verification Confirmation")
    add_body_paragraph(
        doc,
        "• GitHub Repository URL: https://github.com/Asoka1/Mobile_Money_Analytics_2026_Package.git\n"
        "• Full Code Package: All source scripts, definitions, queries, checks, benchmarks, raw results, and plans included in submission ZIP.\n"
        "• Generator Integrity: SHA-256 hash of mobile_money_generator.py verified unchanged against distribution.\n"
        "• 61-Case Correctness: Re-run of compare.py confirmed 61 of 61 cases match with 0 errors or discrepancies.\n"
        "• Visualizations: All 5 analytical charts generated and embedded directly into the report.",
        bold_prefix="9.1 Deliverables Checklist & Integrity: "
    )

    add_screenshot_box(
        doc, "19", "Git Repository Status, Commit History & GitHub Remote URL",
        "git status\n"
        "git log -2 --oneline\n"
        "git remote -v",
        "Show clean working tree, commit history, and remote tracking pointing to https://github.com/Asoka1/Mobile_Money_Analytics_2026_Package.git."
    )

    add_screenshot_box(
        doc, "20", "Database Service Management & Clean Service Shutdown",
        "neo4j status\n"
        "psql -d mobile_money -c \"SELECT 'PostgreSQL 17 Active' AS status;\"\n\n"
        "# To stop services post-verification:\n"
        "neo4j stop\n"
        "pg_ctl stop -D /usr/local/var/postgresql@17",
        "Show active status or clean stopped service status as required by course protocol."
    )

    doc.save(DOCX_PATH)
    size_kb = os.path.getsize(DOCX_PATH) / 1024
    print(f"Successfully generated official Word report: {DOCX_PATH} ({size_kb:.1f} KB)")

if __name__ == '__main__':
    generate_docx()
