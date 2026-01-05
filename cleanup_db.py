#!/usr/bin/env python3
"""Clean up database entries for deleted projects."""

import sqlite3
from pathlib import Path

# Database path
vault_root = Path("D:\\Anurag\\PLM_VAULT")
db_path = vault_root / "db.sqlite"

if not db_path.exists():
    print(f"Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all projects from database
cursor.execute("SELECT project_id, name, vault_path FROM projects")
projects = cursor.fetchall()

print(f"Found {len(projects)} projects in database:")
for proj_id, name, vault_path in projects:
    folder_path = Path(vault_path)
    exists = folder_path.exists()
    status = "✓ EXISTS" if exists else "✗ DELETED"
    print(f"  {name:20s} ({status}) - {vault_path}")

# Find and delete orphaned projects
deleted_count = 0
for proj_id, name, vault_path in projects:
    folder_path = Path(vault_path)
    if not folder_path.exists():
        print(f"\nRemoving orphaned entry: {name}")
        
        # Delete from all related tables
        cursor.execute("DELETE FROM access_log WHERE project_id = ?", (proj_id,))
        cursor.execute("DELETE FROM file_locks WHERE file_id IN (SELECT file_id FROM files WHERE project_id = ?)", (proj_id,))
        cursor.execute("DELETE FROM assembly_relationships WHERE file_id IN (SELECT file_id FROM files WHERE project_id = ?)", (proj_id,))
        cursor.execute("DELETE FROM version_transitions WHERE version_id IN (SELECT version_id FROM versions WHERE file_id IN (SELECT file_id FROM files WHERE project_id = ?))", (proj_id,))
        cursor.execute("DELETE FROM versions WHERE file_id IN (SELECT file_id FROM files WHERE project_id = ?)", (proj_id,))
        cursor.execute("DELETE FROM files WHERE project_id = ?", (proj_id,))
        cursor.execute("DELETE FROM projects WHERE project_id = ?", (proj_id,))
        deleted_count += 1
        print(f"  ✓ Deleted {name} from database")

conn.commit()
conn.close()

print(f"\n✅ Cleanup complete! Removed {deleted_count} orphaned project(s)")
