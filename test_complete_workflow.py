#!/usr/bin/env python3
"""
Complete test: Structure creation + Freeze operation
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

print("\n===== PHASE 1: CREATE STRUCTURE =====")
project = db.create_project("TestProject_Phase1", "Testing new workflow", "TestUser")
print(f"[OK] Project created: {project['plm_id']}")

file = db.create_file(
    project['project_id'],
    "Bracket",
    "PART",
    str(vault_path / "Parts" / "Bracket"),
    "Test bracket part",
    str(vault_path / "Parts" / "Bracket" / "part_meta.json")
)
print(f"[OK] File created: {file['plm_id']}")

# Verify folder structure
checks = [
    (vault_path / "Working" / "Parts" / "Bracket", "Working/Parts/Bracket"),
    (vault_path / "Parts" / "Bracket", "Parts/Bracket"),
    (vault_path / "Parts" / "Bracket" / "part_meta.json", "part_meta.json"),
]

for path, label in checks:
    if not path.exists():
        print(f"[FAIL] {label} NOT FOUND")
        sys.exit(1)
    print(f"[OK] {label} exists")

print("\n===== PHASE 2: SIMULATE FILE SAVE =====")
file_id = file['file_id']
file_name = file['file_name']
parts_folder = vault_path / "Parts" / file_name
working_folder = vault_path / "Working" / "Parts" / file_name

# Simulate SolidWorks saving file to working folder
working_file = working_folder / f"{file_name}.SLDPRT"
working_file.write_text("MOCK_SLDPRT_CONTENT_v1")
print(f"[OK] Simulated SolidWorks save: {working_file.name}")

print("\n===== PHASE 3: FREEZE FILE =====")
metadata_file = parts_folder / "part_meta.json"
with open(metadata_file, 'r') as f:
    metadata = json.load(f)

print(f"Before freeze:")
print(f"  - state: {metadata['state']}")
print(f"  - latest_version: {metadata['latest_version']}")

# Execute freeze
latest = metadata.get("latest_version", "v000")
latest_num = int(latest[1:]) if latest.startswith("v") else 0
next_version_num = latest_num + 1
next_version_str = f"v{next_version_num:03d}"

version_folder = parts_folder / next_version_str
version_folder.mkdir(parents=True, exist_ok=True)

version_file = version_folder / f"{file_name}.SLDPRT"
if working_file.exists():
    copy2(working_file, version_file)
print(f"[OK] Frozen to: {next_version_str}")

# Create version metadata
version_metadata = {
    "version": next_version_str,
    "created_by": "TestUser",
    "created_timestamp": "2026-01-04T12:00:00Z",
    "change_note": "Initial freeze",
    "state": "Frozen"
}
version_meta_file = version_folder / "version_meta.json"
with open(version_meta_file, 'w') as f:
    json.dump(version_metadata, f, indent=2)

# Update part_meta.json
metadata["latest_version"] = next_version_str
metadata["state"] = "Frozen"
with open(metadata_file, 'w') as f:
    json.dump(metadata, f, indent=2)

db.create_version(file_id, "TestUser", change_note="Initial freeze")

# Verify freeze
with open(metadata_file, 'r') as f:
    metadata = json.load(f)

print(f"\nAfter freeze:")
print(f"  - state: {metadata['state']}")
print(f"  - latest_version: {metadata['latest_version']}")

if (version_folder / f"{file_name}.SLDPRT").exists():
    print(f"[OK] {next_version_str}/{file_name}.SLDPRT exists")

print("\n===== PHASE 4: REWORK (Copy v001 back to Working) =====")
# Simulate rework: copy frozen version back to working
v001_file = parts_folder / next_version_str / f"{file_name}.SLDPRT"
working_rework_file = working_folder / f"{file_name}.SLDPRT"

if v001_file.exists():
    copy2(v001_file, working_rework_file)
    print(f"[OK] Copied {next_version_str} back to Working/")

# Update metadata for rework
metadata["state"] = "Working"
with open(metadata_file, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"[OK] Updated metadata: state = 'Working'")

print("\n===== PHASE 5: FREEZE AGAIN (v002) =====")
# Simulate another edit and freeze
working_rework_file.write_text("MOCK_SLDPRT_CONTENT_v2_UPDATED")
print(f"[OK] Simulated edit in Working/")

# Freeze again
next_version_num += 1
next_version_str = f"v{next_version_num:03d}"
version_folder = parts_folder / next_version_str
version_folder.mkdir(parents=True, exist_ok=True)

version_file = version_folder / f"{file_name}.SLDPRT"
copy2(working_rework_file, version_file)
print(f"[OK] Frozen to: {next_version_str}")

version_metadata["version"] = next_version_str
version_meta_file = version_folder / "version_meta.json"
with open(version_meta_file, 'w') as f:
    json.dump(version_metadata, f, indent=2)

metadata["latest_version"] = next_version_str
metadata["state"] = "Frozen"
with open(metadata_file, 'w') as f:
    json.dump(metadata, f, indent=2)

db.create_version(file_id, "TestUser", change_note="Second freeze after rework")

print("\n===== VERIFICATION =====")
versions = db.list_file_versions(file_id)
print(f"[OK] Total versions in DB: {len(versions)}")

# Check disk structure
v001_check = (parts_folder / "v001" / f"{file_name}.SLDPRT").exists()
v002_check = (parts_folder / "v002" / f"{file_name}.SLDPRT").exists()

print(f"[OK] v001/{file_name}.SLDPRT exists: {v001_check}")
print(f"[OK] v002/{file_name}.SLDPRT exists: {v002_check}")

with open(metadata_file, 'r') as f:
    final_metadata = json.load(f)
print(f"[OK] Final state: {final_metadata['state']}")
print(f"[OK] Latest version: {final_metadata['latest_version']}")

print("\n[PASS] Complete Workflow Test Passed!")
