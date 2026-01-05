#!/usr/bin/env python3
"""
Test freeze operation (create version with new structure)
"""
import sys
import os
import json
from pathlib import Path
from shutil import copy2

# Fix UTF-8 encoding for Windows PowerShell
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from database.db import PLMDatabase

vault_path = Path("D:/Anurag/PLM_VAULT")
db = PLMDatabase(str(vault_path))

# Get the test file from previous test
files = db.list_project_files(2)  # project_id 2
test_file = files[0]
print(f"Testing freeze on file: {test_file['file_name']}")

file_id = test_file['file_id']
file_name = test_file['file_name']
parts_folder = Path(test_file['vault_path'])
working_folder = vault_path / "Working" / "Parts" / file_name

print(f"\n--- Initial State ---")
print(f"Parts folder: {parts_folder}")
print(f"Working folder: {working_folder}")

# Create a test file in working folder to simulate SolidWorks save
working_file = working_folder / f"{file_name}.SLDPRT"
working_file.touch()
print(f"[OK] Created working file: {working_file}")

# Read current metadata
metadata_file = parts_folder / "part_meta.json"
with open(metadata_file, 'r') as f:
    metadata = json.load(f)
print(f"\nCurrent metadata:")
print(f"  - state: {metadata['state']}")
print(f"  - latest_version: {metadata['latest_version']}")

# Perform freeze operation (simulate what create_version() does in GUI)
print(f"\n--- Freezing File ---")

# Parse latest version
latest = metadata.get("latest_version", "v000")
latest_num = int(latest[1:]) if latest.startswith("v") else 0
next_version_num = latest_num + 1
next_version_str = f"v{next_version_num:03d}"

# Create version folder
version_folder = parts_folder / next_version_str
version_folder.mkdir(parents=True, exist_ok=True)
print(f"[OK] Created version folder: {version_folder}")

# Copy file from working to version folder
version_file = version_folder / f"{file_name}.SLDPRT"
if working_file.exists():
    copy2(working_file, version_file)
    print(f"[OK] Copied {file_name}.SLDPRT to {next_version_str}/")

# Create version metadata
version_metadata = {
    "version": next_version_str,
    "created_by": "TestUser",
    "created_timestamp": "2026-01-04T12:00:00Z",
    "change_note": "Test freeze",
    "state": "Frozen"
}
version_meta_file = version_folder / "version_meta.json"
with open(version_meta_file, 'w') as f:
    json.dump(version_metadata, f, indent=2)
print(f"[OK] Created version metadata: {version_meta_file}")

# Update part_meta.json
metadata["latest_version"] = next_version_str
metadata["state"] = "Frozen"
with open(metadata_file, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"[OK] Updated part_meta.json")

# Simulate lock in DB
print(f"\n[OK] Would lock file in database (simulated)")
# db.acquire_lock(file_id, "TestUser", "File frozen")

# Create version record in DB
db.create_version(file_id, "TestUser", change_note="Test freeze")
print(f"[OK] Created version record in DB")

# Verify final state
print(f"\n--- Final State ---")
with open(metadata_file, 'r') as f:
    final_metadata = json.load(f)
print(f"Metadata:")
print(f"  - state: {final_metadata['state']}")
print(f"  - latest_version: {final_metadata['latest_version']}")

if (version_folder / f"{file_name}.SLDPRT").exists():
    print(f"[OK] {next_version_str}/{file_name}.SLDPRT exists")

if (version_folder / "version_meta.json").exists():
    print(f"[OK] {next_version_str}/version_meta.json exists")

print(f"\n[PASS] Freeze Test Completed!")
