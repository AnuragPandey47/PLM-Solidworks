#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect(r'D:\Anurag\PLM_VAULT\db.sqlite')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print("Tables in database:")
for table in tables:
    print(f"  - {table}")
conn.close()
