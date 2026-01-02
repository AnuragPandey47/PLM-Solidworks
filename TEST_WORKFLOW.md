# PLM System - Complete Testing Workflow

**Last Updated:** January 2, 2026  
**Status:** Ready for Testing  
**Test Scope:** Database, CLI Tool, GUI, Versioning, Locks, Audit Log

---

## Quick Start Testing

Run this in PowerShell from `e:\PLM_SOLIDWORKS`:

```powershell
# 1. Check environment
python check_env.py

# 2. Initialize vault (if needed)
python SETUP.py

# 3. Launch GUI
python plm_gui.py
```

Or use CLI for manual testing:

```powershell
# Import and test CLI directly
cd e:\PLM_SOLIDWORKS
python -c "from cli_tool.plm import PLMCLITool; cli = PLMCLITool(r'e:\PLM_VAULT'); print(cli.cmd_project_list())"
```

---

## Phase 1: Environment & Setup (5 minutes)

### 1.1 Verify Python Environment

**Command:**
```powershell
python check_env.py
```

**Expected Output:**
```
✓ Python 3.9+ installed
✓ Required packages present (sqlite3, tkinter, logging)
✓ Windows 10/11 detected
✓ PLM vault path available: e:\PLM_VAULT
```

**Pass Criteria:**
- All checks pass ✓
- No missing packages
- Vault path accessible

---

### 1.2 Initialize Vault Structure

**Command:**
```powershell
python SETUP.py
```

**Expected Output:**
```
✓ Vault directory created: e:\PLM_VAULT
✓ Database initialized: e:\PLM_VAULT\plm.sqlite
✓ Directories created: Projects, Assemblies, Archive
✓ 8 tables created: projects, files, versions, etc.
✓ Initial views created
```

**Pass Criteria:**
- Vault structure created
- SQLite database initialized
- All 8 tables present
- No errors in output

**Verify Manually:**
```powershell
# Check directory structure
ls e:\PLM_VAULT -Recurse | head -20

# Check database tables
sqlite3 e:\PLM_VAULT\plm.sqlite ".tables"
```

---

## Phase 2: CLI Tool Testing (15 minutes)

### 2.1 Project Management

**Test: Create Project**
```powershell
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
result = cli.cmd_project_create('TestProject', 'Test Owner', 'Testing PLM system')
print(result)
"
```

**Expected Output:**
```
Created project: TestProject (PLM-001)
```

**Test: List Projects**
```powershell
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
result = cli.cmd_project_list()
print(result)
"
```

**Expected Output:**
```
Projects (1):
├─ TestProject (PLM-001)
  Owner: Test Owner
  Created: 2026-01-02
```

**Test: Project Info**
```powershell
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
result = cli.cmd_project_info(1)
print(result)
"
```

**Expected Output:**
```
Project: TestProject
ID: 1, PLM-ID: PLM-001
Owner: Test Owner
Description: Testing PLM system
Created: 2026-01-02
Status: Active
```

---

### 2.2 File Management

**Test: Add File to Project**
```powershell
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
# First copy a test file
import shutil
import os
os.makedirs(r'e:\PLM_VAULT\Projects\PLM-001', exist_ok=True)
open(r'e:\PLM_VAULT\Projects\PLM-001\TestPart.SLDPRT', 'w').close()

result = cli.cmd_file_list(1)
print(result)
"
```

**Expected Output:**
```
Files in TestProject (0 registered):
(Create files via SolidWorks or manually add to vault)
```

---

### 2.3 Lock Management

**Test: Acquire Lock**
```powershell
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
result = cli.cmd_lock_list()
print(result)
"
```

**Expected Output:**
```
Active Locks (0):
(No locks currently held)
```

---

### 2.4 Vault Status

**Test: Check Vault**
```powershell
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
result = cli.cmd_vault_status()
print(result)
"
```

**Expected Output:**
```
Vault Status:
├─ Database: e:\PLM_VAULT\plm.sqlite (OK)
├─ Projects: 1 active
├─ Files: 0 registered
├─ Versions: 0 created
├─ Active Locks: 0
└─ Access Log: 0 entries
```

---

## Phase 3: Database Layer Testing (15 minutes)

### 3.1 Direct Database Operations

**Test: Database Connection**
```powershell
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
print('✓ Database connected')
print(f'✓ SQLite version: {db.get_sqlite_version()}')
"
```

**Expected Output:**
```
✓ Database connected
✓ SQLite version: 3.45.0
```

---

### 3.2 CRUD Operations

**Test: Create & Retrieve Project**
```powershell
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')

# Create
proj_id = db.create_project('EngineersProject', 'John Smith', 'Mechanical design')
print(f'✓ Created project ID: {proj_id}')

# Retrieve
proj = db.get_project(proj_id)
print(f'✓ Retrieved: {proj[\"name\"]}, PLM-ID: {proj[\"plm_id\"]}')

# List
all_proj = db.list_projects()
print(f'✓ Total projects: {len(all_proj)}')
"
```

**Expected Output:**
```
✓ Created project ID: 2
✓ Retrieved: EngineersProject, PLM-ID: PLM-002
✓ Total projects: 2
```

---

### 3.3 Version Operations

**Test: Create & List Versions**
```powershell
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')

# Create file first
file_id = db.add_file(1, 'TestPart', '.SLDPRT', 'John Smith', r'e:\PLM_VAULT\Projects\PLM-001')
print(f'✓ Created file ID: {file_id}')

# Create version
ver_id = db.create_version(file_id, r'e:\PLM_VAULT\Projects\PLM-001\TestPart.SLDPRT', change_note='Initial design')
print(f'✓ Created version ID: {ver_id}')

# List versions
versions = db.list_file_versions(file_id)
print(f'✓ File versions: {len(versions)}')
print(f'  v{versions[0][\"version_number\"]:03d} - {versions[0][\"lifecycle_state\"]}')
"
```

**Expected Output:**
```
✓ Created file ID: 1
✓ Created version ID: 1
✓ File versions: 1
  v001 - In-Work
```

---

### 3.4 Lock Operations

**Test: Acquire & Release Lock**
```powershell
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')

# Acquire lock
lock_id = db.acquire_lock(1, 'John Smith', 'Edit')
print(f'✓ Lock acquired ID: {lock_id}')

# Check active locks
locks = db.get_active_locks()
print(f'✓ Active locks: {len(locks)}')
print(f'  File {locks[0][\"file_id\"]} locked by {locks[0][\"locked_by\"]}')

# Release lock
db.release_lock(1, 'John Smith')
print(f'✓ Lock released')

# Verify
locks = db.get_active_locks()
print(f'✓ Active locks after release: {len(locks)}')
"
```

**Expected Output:**
```
✓ Lock acquired ID: 1
✓ Active locks: 1
  File 1 locked by John Smith
✓ Lock released
✓ Active locks after release: 0
```

---

### 3.5 Freeze Version

**Test: Freeze & Check State**
```powershell
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')

# Create another version first
file_id = 1  # Using existing file
db.create_version(file_id, r'e:\PLM_VAULT\Projects\PLM-001\TestPart.SLDPRT', change_note='Rev 2')
print('✓ Created v002')

# Freeze version
result = db.freeze_version(file_id, 2, 'John Smith')
print(f'✓ Freeze successful: {result}')

# Check version state
versions = db.list_file_versions(file_id)
for v in versions:
    print(f'  v{v[\"version_number\"]:03d} - {v[\"lifecycle_state\"]}')
"
```

**Expected Output:**
```
✓ Created v002
✓ Freeze successful: True
  v001 - In-Work
  v002 - Released
```

---

### 3.6 Audit Log

**Test: Check Audit Trail**
```powershell
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')

# Get recent audit entries
logs = db.get_audit_trail(limit=10)
print(f'✓ Audit entries: {len(logs)}')
for log in logs[-3:]:
    print(f'  {log[\"timestamp\"]} - {log[\"user\"]}: {log[\"action\"]}')
"
```

**Expected Output:**
```
✓ Audit entries: 8
  2026-01-02 10:15:23 - John Smith: create_project
  2026-01-02 10:15:24 - John Smith: add_file
  2026-01-02 10:15:25 - John Smith: freeze_version
```

---

## Phase 4: GUI Testing (20 minutes)

### 4.1 Launch GUI

**Command:**
```powershell
python plm_gui.py
```

**Expected:**
- Window opens (1200x700)
- Title bar: "PLM System - Desktop Manager"
- 5 tabs visible: Projects, Files, Versions, Locks, Audit Log
- Status bar shows: "Connected as: [Your Username]"

---

### 4.2 Projects Tab

**Test 1: View Projects**
- Tab opens with project list
- Shows: PLM-001 TestProject, PLM-002 EngineersProject
- Columns: Project Name, PLM ID, Owner, Created, Active

**Test 2: Create Project**
- Click "Create Project" button
- Enter: Name="GearBox", Description="Transmission design"
- Click "Create"
- Project appears in list as PLM-003

**Test 3: Refresh**
- Click "Refresh"
- List updates without lag

---

### 4.3 Files Tab

**Test 1: Select Project**
- Click "Files" tab
- Project dropdown shows: TestProject, EngineersProject, GearBox
- Select "TestProject"
- Files list populates (should show TestPart.SLDPRT if created)

**Test 2: Lock/Unlock File**
- Select a file from list
- Click "Acquire Lock"
- Message: "Lock acquired (24 hours)"
- Locked By column shows your username
- Click "Release Lock"
- Locked By column clears

---

### 4.4 Versions Tab

**Test 1: Select File**
- Click "Versions" tab
- File dropdown shows files from selected project
- Select "TestPart.SLDPRT"
- Version list shows: v001 (In-Work), v002 (Released)

**Test 2: Create Version**
- Click "Create Version" button
- Enter change note: "Fixed bore diameter"
- Click "Create"
- Message: "Version created"
- List updates with v003 (In-Work)

**Test 3: Freeze Version**
- Select v003 from list
- Click "Freeze Version"
- Confirm dialog: "Freeze version v003? (Read-Only)"
- Click "Yes"
- Message: "Version v003 frozen"
- v003 state changes to "Released"

---

### 4.5 Locks Tab

**Test 1: View Active Locks**
- Click "Locks" tab
- Shows any current locks
- Columns: ID, File Name, Locked By, Acquired At, Expires At

**Test 2: Acquire Lock from GUI**
- Go back to Files tab
- Select TestPart.SLDPRT
- Click "Acquire Lock"
- Return to Locks tab
- TestPart.SLDPRT appears in lock list
- Expires 24 hours from now

**Test 3: Clean Expired Locks**
- Click "Clean Expired" button
- Message: "Expired locks cleaned"
- No errors

---

### 4.6 Audit Log Tab

**Test 1: View Log**
- Click "Audit Log" tab
- Shows all actions in reverse chronological order
- Columns: ID, Timestamp, User, Action, Details

**Test 2: Filter by Limit**
- Change "Limit" dropdown to different values (10, 20, 50, 100, 200)
- Click "Refresh"
- Log updates to show selected number of entries

**Test 3: Log Accuracy**
- All previous operations should appear:
  - create_project
  - add_file
  - create_version
  - freeze_version
  - acquire_lock
  - release_lock

---

## Phase 5: Versioning Workflow Testing (15 minutes)

### 5.1 Complete User Workflow

**Scenario: Engineer modifies a part**

```powershell
# 1. Acquire lock
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
print(cli.cmd_lock_list())  # Should be empty
"

# 2. Acquire lock for file
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
lock_id = db.acquire_lock(1, 'John Smith', 'Edit')
print(f'✓ Lock acquired: {lock_id}')
"

# 3. Verify lock active
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
print(cli.cmd_lock_list())  # Should show 1 lock
"

# 4. Create version (after editing file locally)
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
ver_id = db.create_version(1, r'e:\PLM_VAULT\Projects\PLM-001\TestPart.SLDPRT', 
                           change_note='Added threads to shaft')
print(f'✓ Version created: {ver_id}')
"

# 5. List versions
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
print(cli.cmd_version_list(1))  # Show all versions for file 1
"

# 6. Release lock
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
db.release_lock(1, 'John Smith')
print('✓ Lock released')
"

# 7. Freeze version (for release)
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
print(cli.cmd_version_freeze(1, 3, 'John Smith'))
"

# 8. Verify final state
python -c "
from cli_tool.plm import PLMCLITool
cli = PLMCLITool(r'e:\PLM_VAULT')
print('=== Final State ===')
print(cli.cmd_version_list(1))
print(cli.cmd_lock_list())
"
```

**Expected Sequence:**
1. ✓ Lock acquired
2. ✓ Lock is active
3. ✓ Version created
4. ✓ Version appears in list (In-Work)
5. ✓ Lock released
6. ✓ Version frozen
7. ✓ Version state changed to Released, Lock released

---

### 5.2 Multi-User Scenario

**Scenario: Lock prevents concurrent edits**

```powershell
# User A acquires lock
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
lock_id = db.acquire_lock(1, 'Alice', 'Edit')
print(f'Alice acquired lock: {lock_id}')
"

# User B tries to acquire same lock
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
try:
    lock_id = db.acquire_lock(1, 'Bob', 'Edit')
    print(f'Bob acquired lock: {lock_id}')
except Exception as e:
    print(f'✓ Bob blocked: {e}')
"

# User A releases lock
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
db.release_lock(1, 'Alice')
print('Alice released lock')
"

# User B now succeeds
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
lock_id = db.acquire_lock(1, 'Bob', 'Edit')
print(f'✓ Bob acquired lock: {lock_id}')
db.release_lock(1, 'Bob')
"
```

**Expected:**
- Alice's lock succeeds
- Bob's lock fails (file in use)
- After Alice releases, Bob succeeds

---

## Phase 6: Error Handling Testing (10 minutes)

### 6.1 Invalid Input

**Test: Invalid Project ID**
```powershell
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
result = db.get_project(999)
print(f'Result: {result}')  # Should be None
"
```

**Expected:** Returns `None` gracefully

---

### 6.2 Lock Timeout Handling

**Test: Clean Stale Locks**
```powershell
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')

# Create old lock (simulate expired)
import sqlite3
conn = sqlite3.connect(r'e:\PLM_VAULT\plm.sqlite')
cur = conn.cursor()
cur.execute(\"INSERT INTO file_locks (file_id, locked_by, reason, locked_at, expires_at) VALUES (1, 'OldUser', 'Edit', datetime('now', '-25 hours'), datetime('now', '-1 hour'))\")
conn.commit()
conn.close()

# Clean stale locks
db.clean_stale_locks()
print('✓ Stale locks cleaned')

# Verify
locks = db.get_active_locks()
print(f'Remaining locks: {len(locks)}')
"
```

**Expected:** Stale lock removed, only valid locks remain

---

## Phase 7: Data Persistence Testing (5 minutes)

### 7.1 Verify Data Survives Restart

**Test: Close & Reopen**

```powershell
# 1. Check data before close
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
projects = db.list_projects()
print(f'Projects before: {len(projects)}')
for p in projects:
    print(f'  - {p[\"name\"]}')
"

# 2. Close connection (program exit)
# 3. Reopen GUI or CLI
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
projects = db.list_projects()
print(f'Projects after: {len(projects)}')
for p in projects:
    print(f'  - {p[\"name\"]}')
"
```

**Expected:** Same data present, no loss

---

## Phase 8: Performance Testing (10 minutes)

### 8.1 Large Dataset

**Test: Add 100 Projects**

```powershell
python -c "
from database.db import PLMDatabase
import time

db = PLMDatabase(r'e:\PLM_VAULT')
start = time.time()

for i in range(100):
    db.create_project(f'Project_{i:03d}', 'TestUser', f'Test project {i}')

elapsed = time.time() - start
print(f'✓ 100 projects created in {elapsed:.2f}s')
print(f'  Rate: {100/elapsed:.0f} projects/sec')

# Verify
projects = db.list_projects()
print(f'✓ Total projects: {len(projects)}')
"
```

**Expected:** 
- Creates in < 2 seconds
- List returns all projects quickly

---

### 8.2 GUI Responsiveness

**Test: Load GUI with 100 Projects**

```powershell
python plm_gui.py
```

**Expected:**
- Projects tab loads all 100+ entries quickly
- No freezing or lag
- Scrolling is smooth

---

## Test Results Summary

Create a test log file: `TEST_RESULTS.txt`

```
PLM SYSTEM - TEST RESULTS
=========================
Date: 2026-01-02
Tester: [Your Name]
Build: v0.1.0

PHASE 1: ENVIRONMENT & SETUP
├─ [PASS] Python 3.9+ check
├─ [PASS] Vault initialization
└─ [PASS] Database creation

PHASE 2: CLI TOOL
├─ [PASS] Project create/list/info
├─ [PASS] File management
├─ [PASS] Lock operations
├─ [PASS] Vault status
└─ [PASS] Audit logging

PHASE 3: DATABASE
├─ [PASS] Connection & version
├─ [PASS] CRUD operations
├─ [PASS] Version management
├─ [PASS] Lock lifecycle
├─ [PASS] Freeze version
└─ [PASS] Audit trail

PHASE 4: GUI
├─ [PASS] Projects tab
├─ [PASS] Files tab
├─ [PASS] Versions tab
├─ [PASS] Locks tab
└─ [PASS] Audit log tab

PHASE 5: VERSIONING WORKFLOW
├─ [PASS] Complete workflow
├─ [PASS] Multi-user locks
└─ [PASS] State transitions

PHASE 6: ERROR HANDLING
├─ [PASS] Invalid inputs
└─ [PASS] Lock timeouts

PHASE 7: PERSISTENCE
└─ [PASS] Data survives restart

PHASE 8: PERFORMANCE
├─ [PASS] 100+ projects
└─ [PASS] GUI responsiveness

OVERALL: [PASS] ✓ READY FOR PRODUCTION
```

---

## Troubleshooting

### GUI Won't Start
```powershell
# Check tkinter installed
python -c "import tkinter; print('OK')"

# Check database
sqlite3 e:\PLM_VAULT\plm.sqlite ".tables"
```

### Lock Not Released
```powershell
python -c "
from database.db import PLMDatabase
db = PLMDatabase(r'e:\PLM_VAULT')
db.clean_stale_locks()
print('Cleaned expired locks')
"
```

### Database Locked Error
```powershell
# Close all connections first
# Restart PowerShell
# Try again
```

### Version Not Created
```powershell
# Verify file exists
ls e:\PLM_VAULT\Projects\

# Check database for file
sqlite3 e:\PLM_VAULT\plm.sqlite "SELECT * FROM files;"
```

---

## Next Steps

After all tests pass:
1. ✓ Run full workflow with SolidWorks (Phase 2.0)
2. ✓ Deploy to team shares
3. ✓ Create SolidWorks Add-in installer
4. ✓ Setup PostgreSQL backend (Phase 3.0)
