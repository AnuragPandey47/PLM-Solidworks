#!/usr/bin/env python3
"""Clear orphaned projects from database - cascade delete."""

import sqlite3
from pathlib import Path

vault_root = Path("D:\\Anurag\\PLM_VAULT")
db_path = vault_root / "db.sqlite"

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Get all projects
cursor.execute("SELECT project_id, name, vault_path FROM projects")
projects = cursor.fetchall()

print(f"Found {len(projects)} projects:")
for proj_id, name, vault_path in projects:
    exists = Path(vault_path).exists()
    status = "✓" if exists else "✗"
    print(f"  [{status}] {name}")

print("\nDeleting orphaned projects...")
deleted = []
for proj_id, name, vault_path in projects:
    if not Path(vault_path).exists():
        try:
            # Delete cascade - files first, then project
            cursor.execute("SELECT file_id FROM files WHERE project_id = ?", (proj_id,))
            file_ids = [row[0] for row in cursor.fetchall()]
            
            for file_id in file_ids:
                cursor.execute("DELETE FROM file_locks WHERE file_id = ?", (file_id,))
                cursor.execute("DELETE FROM assembly_relationships WHERE assembly_file_id = ? OR component_file_id = ?", (file_id, file_id))
                cursor.execute("DELETE FROM version_transitions WHERE version_id IN (SELECT version_id FROM versions WHERE file_id = ?)", (file_id,))
                cursor.execute("DELETE FROM versions WHERE file_id = ?", (file_id,))
            
            cursor.execute("DELETE FROM access_log WHERE project_id = ?", (proj_id,))
            cursor.execute("DELETE FROM files WHERE project_id = ?", (proj_id,))
            cursor.execute("DELETE FROM projects WHERE project_id = ?", (proj_id,))
            deleted.append(name)
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")

conn.commit()
conn.close()

if deleted:
    print(f"\n✅ Success! Deleted {len(deleted)} project(s)")
else:
    print("\n✅ Database clean")
