#!/usr/bin/env python3
"""Quick test of PLM system"""

import sys
import os
from pathlib import Path

# Set vault path
vault_path = os.getenv("PLM_VAULT_PATH", r"D:\Anurag\PLM_VAULT")
print(f"Vault path: {vault_path}\n")

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cli-tool'))

# Test 1: Database connection
print("✅ TEST 1: Database Connection")
from database.db import PLMDatabase
try:
    db = PLMDatabase(vault_path)
    print(f"   ✓ Connected to {vault_path}\n")
except Exception as e:
    print(f"   ✗ Error: {e}\n")
    sys.exit(1)

# Test 2: List existing projects
print("✅ TEST 2: List Existing Projects")
try:
    projects = db.list_projects()
    print(f"   ✓ Found {len(projects)} project(s)")
    for p in projects:
        print(f"     - {p['name']} (PLM-{p['plm_id']})")
    print()
except Exception as e:
    print(f"   ✗ Error: {e}\n")
    sys.exit(1)

# Test 3: Check database tables
print("✅ TEST 3: Database Tables")
try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print(f"   ✓ Found {len(tables)} tables:")
    for t in tables:
        print(f"     - {t[0]}")
    print()
except Exception as e:
    print(f"   ✗ Error: {e}\n")
    sys.exit(1)

print("=" * 60)
print("✅ ALL TESTS PASSED - System is ready!")
print("=" * 60)
print("\nNext steps:")
print("1. Set vault path: set PLM_VAULT_PATH=D:\\Anurag\\PLM_VAULT")
print("2. Run GUI:        python plm_gui.py")
print("3. Test CLI:       See TEST_WORKFLOW.md for full testing guide")

