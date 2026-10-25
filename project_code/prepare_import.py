"""
prepare_import.py  –  Section 3.2  Prepare Neo4j typed-header CSVs and run import
Reads source CSVs and writes Neo4j admin import copies with proper type headers.
Source CSVs are left unchanged.
"""

import csv
import os
import sys
import subprocess
import shutil
import time

# ── paths ────────────────────────────────────────────────────────────────────
SRC_DIR    = os.path.dirname(os.path.abspath(__file__))   # where source CSVs live
IMPORT_DIR = os.path.join(SRC_DIR, 'neo4j_import')        # temporary import copies

os.makedirs(IMPORT_DIR, exist_ok=True)

# ── helper: rewrite a CSV with a new header row ──────────────────────────────
def rewrite_with_header(src_file, dst_file, new_header):
    """Copy src_file to dst_file replacing the original header with new_header."""
    with (open(src_file,  'r', newline='') as src,
          open(dst_file,  'w', newline='') as dst):
        src.readline()                   # skip original header
        dst.write(','.join(new_header) + '\n')
        shutil.copyfileobj(src, dst, length=1024*1024)
    print(f"  written: {os.path.basename(dst_file)}")

# ─────────────────────────────────────────────────────────────────────────────
# NODE files
# Each ID column uses :ID(<GroupName>) to keep Customer/Account/Device
# ID spaces separate so Neo4j does not conflate e.g. customer 7 with account 7.
# ─────────────────────────────────────────────────────────────────────────────

print("=== Creating Neo4j import CSVs ===\n")

# customers.csv  →  neo4j_customers.csv
# customer_id:ID(Customer), region:string
rewrite_with_header(
    os.path.join(SRC_DIR,    'customers.csv'),
    os.path.join(IMPORT_DIR, 'neo4j_customers.csv'),
    ['customer_id:ID(Customer)', 'region:string'],
)

# devices.csv  →  neo4j_devices.csv
# device_id:ID(Device), access_type:string
rewrite_with_header(
    os.path.join(SRC_DIR,    'devices.csv'),
    os.path.join(IMPORT_DIR, 'neo4j_devices.csv'),
    ['device_id:ID(Device)', 'access_type:string'],
)

# accounts.csv  →  neo4j_accounts.csv
# account_id:ID(Account), :IGNORE (customer_id goes into owns.csv), role:string
rewrite_with_header(
    os.path.join(SRC_DIR,    'accounts.csv'),
    os.path.join(IMPORT_DIR, 'neo4j_accounts.csv'),
    ['account_id:ID(Account)', ':IGNORE', 'role:string'],
)

# ─────────────────────────────────────────────────────────────────────────────
# RELATIONSHIP files
# ─────────────────────────────────────────────────────────────────────────────

# owns.csv  – Customer -OWNS-> Account
# Derived from accounts.csv columns (customer_id, account_id) only
owns_path = os.path.join(IMPORT_DIR, 'neo4j_owns.csv')
with (open(os.path.join(SRC_DIR, 'accounts.csv'), 'r', newline='') as src,
      open(owns_path, 'w', newline='') as dst):
    reader = csv.DictReader(src)
    writer = csv.writer(dst)
    writer.writerow([':START_ID(Customer)', ':END_ID(Account)'])
    for row in reader:
        writer.writerow([row['customer_id'], row['account_id']])
print(f"  written: neo4j_owns.csv")

# account_devices.csv  →  neo4j_used_device.csv
# Account -USED_DEVICE-> Device  with three observation properties
rewrite_with_header(
    os.path.join(SRC_DIR,    'account_devices.csv'),
    os.path.join(IMPORT_DIR, 'neo4j_used_device.csv'),
    [':START_ID(Account)', ':END_ID(Device)',
     'first_day:int', 'last_day:int', 'observations:int'],
)

# transfers.csv  →  neo4j_transfers.csv
# Account -TRANSFER-> Account  with three event properties
rewrite_with_header(
    os.path.join(SRC_DIR,    'transfers.csv'),
    os.path.join(IMPORT_DIR, 'neo4j_transfers.csv'),
    ['transfer_id:long', ':START_ID(Account)', ':END_ID(Account)',
     'occurred_at:long', 'amount_rwf:long'],
)

print("\n=== Import file preparation complete ===")
print(f"Import directory: {IMPORT_DIR}")

# ─────────────────────────────────────────────────────────────────────────────
# Print the neo4j-admin import command (to be run manually with DB stopped)
# ─────────────────────────────────────────────────────────────────────────────
D = IMPORT_DIR
cmd = (
    f"neo4j-admin database import full neo4j \\\n"
    f"  --id-type=integer \\\n"
    f"  --nodes=Customer={D}/neo4j_customers.csv \\\n"
    f"  --nodes=Account={D}/neo4j_accounts.csv \\\n"
    f"  --nodes=Device={D}/neo4j_devices.csv \\\n"
    f"  --relationships=OWNS={D}/neo4j_owns.csv \\\n"
    f"  --relationships=USED_DEVICE={D}/neo4j_used_device.csv \\\n"
    f"  --relationships=TRANSFER={D}/neo4j_transfers.csv \\\n"
    f"  --overwrite-destination=true"
)

print("\n=== Run this command (Neo4j must be STOPPED first) ===")
print(cmd)
print("\nAfter import, START Neo4j and run setup_neo4j.cypher to create")
print("constraints and indexes.")
