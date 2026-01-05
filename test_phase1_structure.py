#!/usr/bin/env python3
"""
Test script to verify new folder structure
"""
import sys
import os
import json
from pathlib import Path

# Fix UTF-8 encoding for Windows PowerShell
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from database.db import PLMDatabase

vault_path = Path("D:/Anurag/PLM_VAULT")

if not vault_path.exists():
    print("[X] Vault not found")
    sys.exit(1)

print("[OK] Vault found at:", vault_path)

db = PLMDatabase(str(vault_path))

# Create test project
print("\n--- Creating Test Project ---")
project = db.create_project("TestProject_Phase1", "Testing new folder structure", "TestUser")
print(f"[OK] Created project: {project['name']} ({project['plm_id']})")
project_id = project['project_id']

# Create test file
print("\n--- Creating Test File ---")
file = db.create_file(
    project_id, 
    "TestPart",
    "PART",
    str(vault_path / "Parts" / "TestPart"),
    "Test PART file",
    str(vault_path / "Parts" / "TestPart" / "part_meta.json")
)
print(f"[OK] Created file: {file['file_name']} ({file['plm_id']})")

# Verify folder structure
print("\n--- Verifying Folder Structure ---")
working_folder = vault_path / "Working" / "Parts" / "TestPart"
parts_folder = vault_path / "Parts" / "TestPart"
metadata_file = parts_folder / "part_meta.json"

checks = [
    (working_folder, "Working/Parts/TestPart"),
    (parts_folder, "Parts/TestPart"),
    (metadata_file, "part_meta.json"),
]

for path, label in checks:
    if path.exists():
        print(f"[OK] {label} exists")
    else:
        print(f"[FAIL] {label} NOT FOUND")

# Verify metadata
if metadata_file.exists():
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    print(f"\n[OK] Metadata loaded:")
    print(f"  - state: {metadata.get('state')}")
    print(f"  - latest_version: {metadata.get('latest_version')}")
    print(f"  - released_version: {metadata.get('released_version')}")
else:
    print("[FAIL] Metadata file not found")

# List files for project
print("\n--- Listing Files ---")
files = db.list_project_files(project_id)
for f in files:
    print(f"  - {f['file_name']} ({f['file_type']})")
    print(f"    Vault path: {f['vault_path']}")
    print(f"    File state: {f.get('file_state', 'N/A')}")

print("\n[PASS] Phase 1 Structure Test Completed!")
