#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect(r'D:\Anurag\PLM_VAULT\db.sqlite')
c = conn.cursor()

tables = ['files', 'versions', 'assembly_relationships', 'file_locks', 'version_transitions', 'access_log']

for table in tables:
    print(f"\n{table}:")
    c.execute(f"PRAGMA table_info({table})")
    for row in c.fetchall():
        print(f"  {row}")

conn.close()
