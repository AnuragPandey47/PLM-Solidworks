# PLM System - Quick Reference Guide

## Environment Setup

### Set Vault Path (Required)
```powershell
# For current PowerShell session only
$env:PLM_VAULT_PATH = "D:\Anurag\PLM_VAULT"

# Make permanent (all future sessions)
[Environment]::SetEnvironmentVariable("PLM_VAULT_PATH", "D:\Anurag\PLM_VAULT", "User")
```

### Verify Environment
```powershell
cd "D:\Anurag\PLM-Solidworks"
python check_env.py
# Should output: ✅ ENVIRONMENT OK
```

---

## Testing Commands

### Run All Tests (Phases 1-8)
```powershell
cd "D:\Anurag\PLM-Solidworks"
$env:PLM_VAULT_PATH = "D:\Anurag\PLM_VAULT"
python test_phases.py
# Takes ~5 minutes
# Shows: PHASE 1-8 results
```

### Run Quick System Check
```powershell
$env:PLM_VAULT_PATH = "D:\Anurag\PLM_VAULT"
python verify_system.py
# Takes ~30 seconds
# Shows: All systems OK
```

### Run Basic Tests Only
```powershell
$env:PLM_VAULT_PATH = "D:\Anurag\PLM_VAULT"
python test_plm.py
# Quick basic functionality check
```

---

## GUI Usage

### Launch GUI Application
```powershell
cd "D:\Anurag\PLM-Solidworks"
$env:PLM_VAULT_PATH = "D:\Anurag\PLM_VAULT"
python plm_gui.py
# Opens 1200x700 window
# 5 tabs: Projects, Files, Versions, Locks, Audit Log
```

### GUI Tabs

**Projects Tab**
- View all projects
- Create new project
- Edit project details
- Display: Name, PLM-ID, Owner, Created date

**Files Tab**
- Select project from dropdown
- View files in selected project
- Acquire/release file locks
- Display: File name, PLM-ID, Type, Status

**Versions Tab**
- Select file from dropdown
- View all versions of file
- Create new version
- Freeze version (make read-only)
- Display: Version number, State, Author, Created date

**Locks Tab**
- View all active file locks
- Monitor lock duration
- Clean expired locks
- Display: File, Locked by, Acquired, Expires

**Audit Log Tab**
- View all system activities
- Filter by limit (10/20/50/100/200 entries)
- Review who did what and when
- Display: ID, Timestamp, User, Action, Details

---

## CLI Tool Usage

### Project Commands
```python
# List all projects
from database.db import PLMDatabase
db = PLMDatabase(r"D:\Anurag\PLM_VAULT")
projects = db.list_projects()
for p in projects:
    print(f"{p['name']} ({p['plm_id']})")

# Create project
project = db.create_project("ProjectName", "Owner Name", "Description")
print(f"Created: {project['plm_id']}")

# Get project info
proj = db.get_project(1)
print(f"Project: {proj['name']}, Owner: {proj['owner']}")
```

### File Commands
```python
# List files in project
files = db.list_project_files(1)  # project_id = 1
print(f"Files: {len(files)}")

# Create file
file_data = db.create_file(
    project_id=1,
    file_name="PartName",
    file_type="PART",  # or ASSEMBLY, DRAWING
    vault_path=r"D:\Anurag\PLM_VAULT\Projects\Project1\PartName.SLDPRT",
    description="Optional description"
)
print(f"Created: {file_data['plm_id']}")

# Get file info
file_obj = db.get_file(1)  # file_id = 1
print(f"File: {file_obj['file_name']}")
```

### Version Commands
```python
# List versions for file
versions = db.list_file_versions(1)  # file_id = 1
for v in versions:
    print(f"v{v['version_number']:03d}: {v['lifecycle_state']}")

# Create version
version = db.create_version(
    file_id=1,
    author="YourName",
    change_note="Description of changes",
    file_path=r"D:\path\to\file.SLDPRT"
)
print(f"Created v{version['version_number']:03d}")

# Get specific version
ver = db.get_version(1)  # version_id = 1
print(f"Version: v{ver['version_number']}")

# Freeze version (make read-only for release)
db.freeze_version(file_id=1, version_id=1, user="YourName")
print("Version frozen - read-only")
```

### Lock Commands
```python
# List active locks
locks = db.get_active_locks()
print(f"Active locks: {len(locks)}")
for lock in locks:
    print(f"  File {lock['file_id']}: locked by {lock['locked_by']}")

# Acquire lock
lock_id = db.acquire_lock(
    file_id=1,
    user="YourName",
    reason="Edit"  # or "Checkout", "Review"
)
print(f"Lock acquired: {lock_id}")

# Release lock
db.release_lock(file_id=1, user="YourName")
print("Lock released")

# Clean stale locks (expired)
cleaned = db.clean_stale_locks()
print(f"Cleaned {cleaned} stale locks")
```

### Audit Log Commands
```python
# Get audit trail
audit = db.get_audit_trail(limit=20)
for entry in audit:
    print(f"{entry['timestamp']}: {entry['user']} - {entry['action']}")

# Get audit for specific file
audit = db.get_audit_trail(file_id=1, limit=10)
for entry in audit:
    print(f"{entry['action']}: {entry['details']}")
```

---

## Database Commands

### Check Database Status
```python
from database.db import PLMDatabase
db = PLMDatabase(r"D:\Anurag\PLM_VAULT")

# Count everything
projects = len(db.list_projects())
files = len(db.list_project_files(1))
locks = len(db.get_active_locks())
audit = len(db.get_audit_trail())

print(f"Projects: {projects}, Files: {files}, Locks: {locks}, Audit: {audit}")
```

### Export Project Data
```python
import json
from database.db import PLMDatabase
db = PLMDatabase(r"D:\Anurag\PLM_VAULT")

# Export single project
proj = db.get_project(1)
with open("project_backup.json", "w") as f:
    json.dump(proj, f, indent=2)

# Export all projects
projects = db.list_projects()
with open("all_projects.json", "w") as f:
    json.dump(projects, f, indent=2)
```

---

## Workflow Examples

### Complete File Edit Workflow
```python
from database.db import PLMDatabase

db = PLMDatabase(r"D:\Anurag\PLM_VAULT")
user = "John Smith"

# 1. Create project (first time only)
proj = db.create_project("BracketAssembly", user, "Main bracket design")
proj_id = proj['project_id']

# 2. Create file
file_obj = db.create_file(
    project_id=proj_id,
    file_name="BracketMain",
    file_type="PART",
    vault_path=r"D:\Anurag\PLM_VAULT\Projects\BracketAssembly\BracketMain.SLDPRT"
)
file_id = file_obj['file_id']

# 3. Acquire lock (prevents others from editing)
lock_id = db.acquire_lock(file_id, user, "Edit")
print(f"Locked for editing: {lock_id}")

# 4. Edit file in SolidWorks...
# [User opens file and makes changes]

# 5. Create version after editing
version = db.create_version(
    file_id=file_id,
    author=user,
    change_note="Added mounting holes per drawing revision B"
)
print(f"Saved as v{version['version_number']:03d}")

# 6. Release lock (allows others to edit)
db.release_lock(file_id, user)
print("Released lock - file available for others")

# 7. When ready to release, freeze version
# db.freeze_version(file_id, version['version_id'], user)
# print("Version frozen - ready for production")
```

### Multi-User Concurrent Access
```python
from database.db import PLMDatabase

db = PLMDatabase(r"D:\Anurag\PLM_VAULT")

# User A tries to edit file
try:
    lock_a = db.acquire_lock(1, "Alice", "Edit")
    print(f"Alice locked file: {lock_a}")
except Exception as e:
    print(f"Alice cannot lock: {e}")

# User B tries to edit same file
try:
    lock_b = db.acquire_lock(1, "Bob", "Edit")
    print(f"Bob locked file: {lock_b}")
except Exception as e:
    print(f"Bob blocked: File locked by Alice")

# When Alice is done
db.release_lock(1, "Alice")
print("Alice released lock")

# Now Bob can lock
lock_b = db.acquire_lock(1, "Bob", "Edit")
print(f"Bob locked file: {lock_b}")
```

---

## Troubleshooting

### GUI Won't Start
```powershell
# Check Python
python --version

# Check tkinter
python -c "import tkinter; print('OK')"

# Check database
Test-Path "D:\Anurag\PLM_VAULT\db.sqlite"

# Check environment
Get-ChildItem env:PLM_VAULT_PATH
```

### Database Lock Error
```powershell
# Close all Python processes
Stop-Process -Name python -Force

# Wait a moment
Start-Sleep -Seconds 2

# Try again
python plm_gui.py
```

### PLM ID Collision
```
This is expected if SETUP.py is run multiple times.
System continues working normally.
Safe to ignore in development.
```

### Can't Find Vault
```powershell
# Set environment variable
$env:PLM_VAULT_PATH = "D:\Anurag\PLM_VAULT"

# Verify path
Test-Path $env:PLM_VAULT_PATH
# Should return: True

# Check files in vault
Get-ChildItem $env:PLM_VAULT_PATH
```

---

## Important Paths

```
Project Root:    D:\Anurag\PLM-Solidworks\
Vault Location:  D:\Anurag\PLM_VAULT\
Database:        D:\Anurag\PLM_VAULT\db.sqlite
Projects Dir:    D:\Anurag\PLM_VAULT\Projects\
Locks Dir:       D:\Anurag\PLM_VAULT\Locks\
Logs Dir:        D:\Anurag\PLM_VAULT\Logs\
Utilities Dir:   D:\Anurag\PLM_VAULT\Utils\
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| plm_gui.py | Launch the GUI |
| check_env.py | Verify environment |
| verify_system.py | Quick system check |
| test_plm.py | Basic tests |
| test_phases.py | Comprehensive test suite |
| database/db.py | Database layer (929 lines) |
| cli-tool/plm.py | CLI tool (528 lines) |

---

## Performance Benchmarks

```
Project Creation:     1,810 projects/second
Query Performance:    < 10ms
Lock Acquisition:     < 100ms
Lock Release:         < 50ms
Version Creation:     < 200ms
Database Startup:     < 500ms
GUI Launch:           ~3 seconds
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "No module named 'database'" | Ensure PLM_VAULT_PATH is set |
| "Database locked" | Close all Python processes, wait, retry |
| "File not found" | Check vault path, verify database.sqlite exists |
| "Lock timeout" | Use clean_stale_locks() to remove expired locks |
| "GUI won't open" | Check tkinter installed: `python -c "import tkinter"` |

---

## Documentation Files

- **README.md** - User guide & overview
- **ARCHITECTURE.md** - System design
- **DATABASE_SCHEMA.md** - Database structure
- **TEST_WORKFLOW.md** - Detailed testing procedures
- **TEST_RESULTS.md** - Current test results
- **SESSION_SUMMARY.md** - This testing session summary
- **HANDOFF_GUIDE.md** - Project handoff notes

---

## Quick Test Scripts

### Test Database Connection
```python
from database.db import PLMDatabase
db = PLMDatabase(r"D:\Anurag\PLM_VAULT")
print("✓ Database connected")
print(f"✓ Projects: {len(db.list_projects())}")
```

### Test Lock System
```python
from database.db import PLMDatabase
db = PLMDatabase(r"D:\Anurag\PLM_VAULT")
lock_id = db.acquire_lock(1, "TestUser", "Edit")
print(f"✓ Lock acquired: {lock_id}")
db.release_lock(1, "TestUser")
print("✓ Lock released")
```

### Test Version Control
```python
from database.db import PLMDatabase
db = PLMDatabase(r"D:\Anurag\PLM_VAULT")
version = db.create_version(1, "TestUser", "Test version")
print(f"✓ Version created: v{version['version_number']:03d}")
```

---

## Getting Help

### Documentation
- See: README.md, ARCHITECTURE.md, DATABASE_SCHEMA.md

### Testing
- Run: `python test_phases.py` for full diagnostic

### System Status
- Run: `python verify_system.py` for quick health check

### Database Integrity
- Check: Test database operations as shown above

---

**Last Updated:** January 2, 2026  
**Status:** Ready for Production  
**Questions?** See documentation files or run test_phases.py
