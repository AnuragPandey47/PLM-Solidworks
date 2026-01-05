#!/usr/bin/env python3
"""
Test corrected structure: all folders per-project
"""
import sys
import os
import json
from pathlib import Path
from shutil import copy2

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from database.db import PLMDatabase

vault_path = Path("D:/Anurag/PLM_VAULT")
db = PLMDatabase(str(vault_path))

print("\n===== CORRECTED STRUCTURE TEST =====")
print("Expected: Projects/ProjectName/Working/Parts/ + Projects/ProjectName/Parts/\n")

# Create project
project = db.create_project("MotorAssembly", "TestUser", "Motor assembly project")
print(f"[OK] Project created: {project['plm_id']}")
project_vault = Path(project['vault_path'])
print(f"     Project vault path: {project_vault}")

# Create file
file = db.create_file(
    project['project_id'],
    "MotorBlock",
    "PART",
    str(project_vault / "Parts" / "MotorBlock"),
    "Motor block PART",
    str(project_vault / "Parts" / "MotorBlock" / "part_meta.json")
)
print(f"[OK] File created: {file['plm_id']}")

# Verify correct structure
checks = [
    (project_vault / "Working" / "Parts" / "MotorBlock", "Working/Parts/MotorBlock"),
    (project_vault / "Parts" / "MotorBlock", "Parts/MotorBlock"),
    (project_vault / "Parts" / "MotorBlock" / "part_meta.json", "part_meta.json"),
]

print("\nVerifying per-project structure:")
all_ok = True
for path, label in checks:
    exists = path.exists()
    status = "[OK]" if exists else "[FAIL]"
    print(f"{status} {label}: {path}")
    if not exists:
        all_ok = False

if not all_ok:
    print("\n[FAIL] Structure verification failed!")
    sys.exit(1)

print("\n[PASS] Corrected per-project structure working!")
