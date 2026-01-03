#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug PLM ID issue"""

import sqlite3
import os

vault_path = os.getenv("PLM_VAULT_PATH", r"D:\Anurag\PLM_VAULT")
db_path = os.path.join(vault_path, "db.sqlite")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("=== PROJECT PLM IDs ===")
cur.execute("SELECT name, plm_id FROM projects")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== FILE PLM IDs ===")
cur.execute("SELECT file_name, plm_id FROM files")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== Testing PLM ID Generation ===")
# Simulate what _get_next_plm_id does for PRJ
cur.execute("SELECT MAX(CAST(SUBSTR(plm_id, -3) AS INTEGER)) FROM projects WHERE plm_id LIKE 'PRJ-%'")
proj_max = cur.fetchone()[0] or 0
print(f"Max PROJECT PLM ID number: {proj_max}")

cur.execute("SELECT MAX(CAST(SUBSTR(plm_id, -3) AS INTEGER)) FROM files WHERE plm_id LIKE 'PRJ-%'")
file_max = cur.fetchone()[0] or 0
print(f"Max FILE PLM ID number (PRJ): {file_max}")

next_num = max(proj_max, file_max) + 1
new_plm_id = f"PLM-PRJ-{next_num:03d}"
print(f"Next PLM ID would be: {new_plm_id}")

# Check if it already exists
cur.execute("SELECT COUNT(*) FROM projects WHERE plm_id = ?", (new_plm_id,))
exists_proj = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM files WHERE plm_id = ?", (new_plm_id,))
exists_file = cur.fetchone()[0]

if exists_proj or exists_file:
    print(f"❌ PROBLEM: {new_plm_id} ALREADY EXISTS!")
else:
    print(f"✅ {new_plm_id} is available")

conn.close()
