# PLM Software for SolidWorks - Complete Documentation

**Version:** 1.0 MVP  
**Status:** Alpha (Ready for Testing)  
**Last Updated:** January 2026

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [System Architecture](#system-architecture)
3. [Features (MVP)](#features-mvp)
4. [Installation](#installation)
5. [Usage Guide](#usage-guide)
6. [API Documentation](#api-documentation)
7. [Troubleshooting](#troubleshooting)
8. [Roadmap](#roadmap)
9. [Support](#support)

---

## 🚀 Quick Start

### Prerequisites
- Windows 10 or later
- SolidWorks 2020 or later (for Add-in)
- Python 3.9+ (for CLI & backend)
- SQLite 3.45.0+

### 5-Minute Setup

```bash
# 1. Clone or download repository to e:\PLM_SOLIDWORKS

# 2. Initialize vault
cd e:\PLM_SOLIDWORKS
python SETUP.py

# 3. Test CLI tool
python cli-tool\plm.py vault status

# 4. Install SolidWorks Add-in (See solidworks-addin/README.md)

# 5. Create sample project
python cli-tool\plm.py project create --name "MyProject" --owner "username" --description "My first PLM project"

# 6. Open SolidWorks and start using PLM!
```

---

## 🏗️ System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────┐
│     ENGINEER WORKFLOW (SolidWorks)              │
│  Open → Edit → Save → Auto-version → Close    │
└────────────────┬────────────────────────────────┘
                 │
     ┌───────────▼──────────────┐
     │  SolidWorks Add-in (C#)  │
     │  - Event hooks           │
     │  - Metadata capture      │
     │  - UI panels             │
     └───────────┬──────────────┘
                 │
     ┌───────────▼──────────────┐
     │   Local Vault            │
     │   (Filesystem + SQLite)  │
     │   - Immutable versions   │
     │   - File metadata        │
     │   - Lock management      │
     └─────────────────────────┘
```

### Three Core Modules

1. **SolidWorks Add-in (C# .NET Framework)**
   - Intercepts save/open/close events
   - Enforces check-out/check-in workflow
   - Displays version history & status
   - Prevents accidental overwrites

2. **Local Vault (Filesystem)**
   - Immutable file storage (v001, v002, v003...)
   - Metadata.json per version
   - Assembly reference tracking (by PLM ID)
   - Lock files for concurrent access

3. **SQLite Database**
   - Projects, Files, Versions tables
   - Assembly relationships (BOM)
   - File locks & lifecycle states
   - Audit trail & access logs

### Data Flow (Save Operation)

```
User clicks [Save] in SolidWorks
         ↓
Add-in intercepts SaveDocument event
         ↓
✓ Validate file has project assignment
✓ Check lock status (not locked by other user)
✓ Check lifecycle state (not Released)
         ↓
Create new version:
  - Generate version number (v001 → v002)
  - Copy file to: vault/ProjectA/CAD/Part1/v003/
  - Create metadata.json with author, timestamp, properties
  - Calculate SHA256 checksum
         ↓
Update database:
  - INSERT into versions table
  - UPDATE files.current_version
  - INSERT into access_log
         ↓
Update UI status bar:
  "v003 - In-Work - Checked out to john.smith"
```

---

## ✨ Features (MVP)

### ✅ Implemented

| Feature | Description | Status |
|---------|-------------|--------|
| **Vault Structure** | Filesystem-based, immutable versions | ✅ Complete |
| **Database Layer** | SQLite schema, CRUD operations | ✅ Complete |
| **File Versioning** | Auto-increment v001→v002→... | ✅ Complete |
| **Add-in Foundation** | Event hooks, metadata capture | ✅ Complete |
| **CLI Tool** | Project, file, version, vault operations | ✅ Complete |
| **File Locking** | Single-editor, multi-reader model | ✅ Complete |
| **Lifecycle States** | In-Work → Released → Obsolete | ✅ Complete |
| **Assembly BOM** | Component tracking & resolution | ✅ Complete |
| **Audit Trail** | User actions logged for compliance | ✅ Complete |

### ⏳ Phase 2 (v1.0+)

- ✅ Web dashboard (optional)
- ✅ FastAPI backend for distributed access
- ✅ PostgreSQL migration support
- ✅ Advanced search & filtering
- ✅ Role-based access control
- ✅ Integration with PDM/ERP systems

---

## 💻 Installation

### Step 1: Initialize Vault

```bash
# Run initialization script (creates directories & database)
cd e:\PLM_SOLIDWORKS
python SETUP.py

# Follow prompts, create sample project when asked
```

**Result:**
```
PLM_VAULT/
├── config.json
├── db.sqlite
├── Projects/
│   └── Demo/
│       ├── CAD/
│       ├── Drawings/
│       ├── Excel/
│       └── Archive/
├── Locks/
├── Logs/
└── Utils/
```

### Step 2: Install SolidWorks Add-in

**Build from Source:**
```bash
cd solidworks-addin/
# Open PLM_SolidWorks_AddIn.csproj in Visual Studio
# Build as Release
# Copy output DLL to C:\Program Files\Common Files\SolidWorks\Addins\
```

**Register Add-in (Admin required):**
```bash
regsvcs "C:\Program Files\Common Files\SolidWorks\Addins\PLM_SolidWorks_AddIn.dll"
```

**Verify:**
- Open SolidWorks
- Check Tools → Add-ins
- PLM Add-in should appear in the list
- UI panel should show in right sidebar

### Step 3: Validate CLI Tool

```bash
# Test CLI
python cli-tool\plm.py vault status

# Expected output:
# =========================
# VAULT INTEGRITY CHECK
# =========================
# Projects: 1
# Files: 0
# Versions: 0
```

---

## 📖 Usage Guide

### Using CLI Tool (No SolidWorks Required)

#### Create Project
```bash
python plm.py project create --name "ProjectA" --owner "john.smith" --description "Bracket assembly"

Output:
✓ Project created successfully
  PLM ID: PLM-PRJ-001
  Name: ProjectA
  Vault path: e:\PLM_VAULT\Projects\ProjectA
```

#### List Projects
```bash
python plm.py project list

Output:
PLM ID          Name                 Owner           Created
PLM-PRJ-001     ProjectA             john.smith      2026-01-15
PLM-PRJ-002     ProjectB             jane.doe        2026-01-16
```

#### List Files in Project
```bash
python plm.py file list --project-id 1

Output:
PLM ID          File Name                 Type        Ver  State        Lock
PLM-PAR-001     BracketBase_Part          PART        3    In-Work      john.smith
PLM-PAR-002     BracketCover_Part         PART        2    Released     -
PLM-ASM-001     Bracket_Assembly          ASSEMBLY    2    In-Work      -
```

#### List Versions of a File
```bash
python plm.py version list --file-id 1

Output:
Ver  Rev   Author          Created             State        Size      Note
1         john.smith      2026-01-10 09:00    In-Work      2000      Initial design
2         john.smith      2026-01-12 14:30    In-Work      2100      Increased thickness
3    A     john.smith      2026-01-15 16:00    Released     2100      FEA validated
```

#### Promote Version to Released
```bash
python plm.py version promote --file-id 1 --version 3 --state "Released" --user "john.smith" --note "FEA validated, ready for manufacturing"

Output:
✓ Promoted BracketBase_Part v3 → Released
  Promoted by: john.smith
  Note: FEA validated, ready for manufacturing
```

#### Show Assembly BOM
```bash
python plm.py assembly bom --id 5

Output:
Component                 PLM ID          Ver  Qty
BracketBase_Part          PLM-PAR-001     3    1
BracketCover_Part         PLM-PAR-002     2    1
Fastener_M4_Socket_Head   PLM-PAR-100     1    8

Total parts: 3, Total qty: 10
```

#### Check Vault Health
```bash
python plm.py vault status

Output:
=== VAULT INTEGRITY CHECK ===
Projects:           2
Files:              15
Versions:           42
Orphaned versions:  0
Missing checksums:  0
Stale locks:        0

✓ Vault is healthy
```

#### View Audit Trail
```bash
python plm.py vault audit --limit 20

Output:
Timestamp             User            Action       File
2026-01-15 16:00:42   john.smith      SAVE         BracketBase_Part
2026-01-15 14:32:10   jane.doe        OPEN         BracketBase_Part
2026-01-15 14:00:00   john.smith      PROMOTE      BracketBase_Part
2026-01-12 14:30:00   john.smith      SAVE         BracketBase_Part
```

### Using SolidWorks Add-in

#### First Time Setup
1. Open SolidWorks
2. Create a new part: File → New → Part
3. Save the file: File → Save
4. **Add-in prompt:** "Select project for this file"
5. Choose project from dropdown (or create new)
6. Add metadata (Material, Weight, etc.)
7. Click [Save in PLM]

**Result:**
- File saved to: `PLM_VAULT\Projects\ProjectA\CAD\PartName\v001\`
- Status shows: "v001 - In-Work - Checked out to john.smith"

#### Editing Workflow

```
Open existing file from vault:
  ↓
File opens in SolidWorks
Add-in shows: "v003 - In-Work"
Check if locked (Yes/No)
  ↓
If locked by you: Continue editing
If locked by other: Read-only mode
If not locked: Click [Check-Out]
  ↓
Edit design
  ↓
Click [Save]:
  - Auto-increment version
  - Create v004
  - Store in vault
  - Update version history panel
  ↓
When ready to release:
  - Click [Promote to Released]
  - Enter ECN/change note
  - Version becomes v003A (immutable)
  - File becomes read-only
  - Cannot edit without creating new major version
```

#### Checking Out a File
```
Open file in SolidWorks
  ↓
Click [Check-Out] button in PLM panel
  ↓
File is locked to current user
Other users see: "Locked by john.smith"
  ↓
Make edits
Click [Save] to increment version
  ↓
When done, click [Check-In]
File is released for others to edit
```

---

## 🔌 API Documentation

### Python Database API (db.py)

```python
from database.db import PLMDatabase

# Initialize
db = PLMDatabase("e:\\PLM_VAULT")

# Create project
project = db.create_project("ProjectA", "john.smith", "My project")
# Returns: {'project_id': 1, 'plm_id': 'PLM-PRJ-001', 'name': 'ProjectA', ...}

# Create file
file = db.create_file(
    project_id=1,
    file_name="BracketBase_Part",
    file_type="PART",
    vault_path="e:\\PLM_VAULT\\Projects\\ProjectA\\CAD\\BracketBase_Part"
)
# Returns: {'file_id': 5, 'plm_id': 'PLM-PAR-001', ...}

# Create version
version = db.create_version(
    file_id=5,
    author="john.smith",
    change_note="Initial design",
    file_path="e:\\PLM_VAULT\\Projects\\ProjectA\\CAD\\BracketBase_Part\\v001\\BracketBase_Part.SLDPRT",
    file_size=2847392,
    checksum="sha256:abc123...",
    custom_properties={"Material": "Aluminum 6061", "Weight": "0.250 kg"}
)
# Returns: {'version_id': 47, 'version_number': 1, ...}

# Acquire lock
session_id = db.acquire_lock(file_id=5, user="john.smith", reason="Edit")
# Returns: "550e8400-e29b-41d4-a716-446655440000"

# Release lock
db.release_lock(file_id=5, user="john.smith")

# Promote version
db.promote_version(version_id=47, new_state="Released", user="john.smith", note="FEA validated")

# Get assembly BOM
bom = db.get_assembly_bom(assembly_file_id=10)
# Returns: [{'component_name': 'BracketBase_Part', 'component_version': 3, ...}, ...]

# Log action
db.log_action(
    user="john.smith",
    action="SAVE",
    file_id=5,
    duration_ms=1250,
    details={"change_note": "Increased thickness", "version": 3}
)

# Get audit trail
logs = db.get_audit_trail(file_id=5, limit=50)
```

### CLI Commands Reference

```bash
# PROJECT
plm project create --name NAME --owner USER [--description TEXT]
plm project list
plm project info --id ID

# FILE
plm file list --project-id ID
plm file info --id ID

# VERSION
plm version list --file-id ID
plm version promote --file-id ID --version NUM --state STATE --user USER [--note TEXT]

# ASSEMBLY
plm assembly bom --id ID

# LOCK
plm lock list
plm lock clean [--max-age HOURS]

# VAULT
plm vault status
plm vault audit [--file-id ID] [--user USER] [--limit NUM]
```

---

## 🔧 Troubleshooting

### "File locked by another user"
**Problem:** Cannot save because file is locked
**Solution:**
1. Check who has it: `plm lock list`
2. Wait for them to check-in
3. Or manually release: `plm lock clean` (admin only)

### "Missing metadata.json"
**Problem:** Assembly references broken
**Solution:**
1. Validate vault: `plm vault status`
2. Check for orphaned versions
3. Restore from backup if needed

### "Stale locks detected"
**Problem:** Files locked > 24 hours
**Solution:**
```bash
# Clean stale locks (safe)
plm lock clean --max-age 24
```

### Add-in not loading in SolidWorks
**Problem:** Add-in doesn't appear in Tools → Add-ins
**Solution:**
1. Verify DLL is in: `C:\Program Files\Common Files\SolidWorks\Addins\`
2. Re-register: `regsvcs path\to\PLM_SolidWorks_AddIn.dll`
3. Restart SolidWorks
4. Check Windows Event Viewer for COM errors

### Database corruption
**Problem:** SQLite database is corrupted
**Solution:**
```bash
# Validate database
python -c "import sqlite3; sqlite3.connect('e:\\PLM_VAULT\\db.sqlite').execute('PRAGMA integrity_check')"

# Restore from backup
copy "e:\PLM_VAULT\db_backup\db_20260115_1430.sqlite" "e:\PLM_VAULT\db.sqlite"
```

---

## 📈 Roadmap

### MVP (v0.1) - Current ✅
- [x] Vault filesystem structure
- [x] SQLite database schema
- [x] File versioning (immutable)
- [x] File locking (single machine)
- [x] CLI tool
- [x] Basic Add-in foundation

### v0.5 - Assembly Support (Q1 2026)
- [ ] Assembly BOM tracking (PLM IDs)
- [ ] Lifecycle promotion (In-Work → Released)
- [ ] CLI enhancements
- [ ] Performance optimization

### v1.0 - Production Ready (Q2 2026)
- [ ] Complete Add-in UI (taskpane, dialogs)
- [ ] Backup & restore utilities
- [ ] Vault integrity checks
- [ ] Comprehensive testing
- [ ] User documentation & training

### v1.5 - LAN Support (Q3 2026)
- [ ] Network vault (mapped drive)
- [ ] Conflict detection
- [ ] Async file sync

### v2.0 - Enterprise (Q4 2026)
- [ ] FastAPI backend
- [ ] PostgreSQL database
- [ ] Web dashboard
- [ ] REST API
- [ ] Multi-site replication
- [ ] Advanced search
- [ ] Role-based access control

---

## 📞 Support

### Documentation Files
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design, data flows, component responsibilities
- **[VAULT_STRUCTURE.md](VAULT_STRUCTURE.md)** - Directory structure, file organization, metadata
- **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - SQLite schema, tables, views, queries

### Common Tasks

**Backup vault:**
```bash
# Manual backup
xcopy e:\PLM_VAULT "e:\PLM_VAULT_BACKUP_2026-01-15" /E /I /Y

# Scheduled backup (Windows Task Scheduler)
# Run daily at 2 AM
```

**Restore from backup:**
```bash
rmdir /S /Q e:\PLM_VAULT
xcopy "e:\PLM_VAULT_BACKUP_2026-01-15" e:\PLM_VAULT /E /I /Y
```

**Migrate to network location:**
```bash
# 1. Create vault on network server
\\server\PLM_VAULT

# 2. Copy local vault
xcopy e:\PLM_VAULT \\server\PLM_VAULT /E /I /Y

# 3. Update config in Add-in & CLI to point to network path

# 4. Validate: plm vault status
```

### Contact & Issues

- **GitHub Issues:** [Report bugs](https://github.com/yourrepo/issues)
- **Documentation:** See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design
- **Examples:** See [cli-tool/examples/](cli-tool/examples/) for sample workflows

---

## 📝 License

PLM Software for SolidWorks is provided as-is for engineering teams and prototyping use.

---

## 🙏 Acknowledgments

Designed for small engineering teams, startups, and rapid prototyping.  
Not intended for enterprise mass-production use (use SAP, Teamcenter for that).

---

**Happy engineering! 🚀**

