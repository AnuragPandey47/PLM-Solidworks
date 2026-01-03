#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check database state and fix PLM ID issue"""

import sqlite3
import os

vault_path = os.getenv("PLM_VAULT_PATH", r"D:\Anurag\PLM_VAULT")
db_path = os.path.join(vault_path, "db.sqlite")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all projects
cur.execute('SELECT project_id, name, plm_id FROM projects')
projects = cur.fetchall()
print('EXISTING PROJECTS:')
for p in projects:
    print(f'  ID: {p[0]}, Name: {p[1]}, PLM-ID: {p[2]}')

# Get sequence
cur.execute("SELECT name, seq FROM sqlite_sequence WHERE name='projects'")
seq = cur.fetchone()
print(f'\nPROJECT SEQUENCE COUNTER: {seq}')

# Check if we need to fix
if projects and seq:
    max_id = max(p[0] for p in projects)
    current_seq = seq[1]
    if current_seq <= max_id:
        print(f'\n⚠️  PROBLEM: Sequence ({current_seq}) <= Max ID ({max_id})')
        print(f'Fixing by setting sequence to {max_id + 10}...')
        cur.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'projects'", (max_id + 10,))
        conn.commit()
        print('✅ FIXED!')
    else:
        print('\n✅ Sequence is OK')
else:
    print('\n⚠️  No projects or no sequence record')

conn.close()
