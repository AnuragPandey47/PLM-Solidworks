# PLM Software for SolidWorks - System Architecture

**Version:** 1.0 MVP Design  
**Date:** January 2026  
**Scope:** Lightweight PLM for small teams & prototypes

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ENGINEER WORKFLOW                               │
│  User opens SolidWorks → Opens part → Adds metadata → Saves       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
        ┌───────────▼──────────────┐    ┌──────▼─────────────┐
        │  SolidWorks Add-in (C#)  │    │   CLI Tool (Py)   │
        │  ─────────────────────   │    │  ──────────────   │
        │  • Event listeners       │    │  • Create project │
        │  • UI panels             │    │  • List versions  │
        │  • Metadata capture      │    │  • Promote state  │
        │  • Version control       │    │  • No SWKS req'd  │
        └───────────┬──────────────┘    └──────┬────────────┘
                    │                          │
                    └──────────────┬───────────┘
                                   │
                         ┌─────────▼──────────┐
                         │  Local Vault       │
                         │  (Filesystem)      │
                         │  ──────────────    │
                         │  PLM_VAULT/        │
                         │  ├── Projects/     │
                         │  ├── Metadata DB   │
                         │  └── Locks/        │
                         └─────────┬──────────┘
                                   │
                    ┌──────────────┴─────────────┐
                    │                            │
        ┌───────────▼──────────────┐  ┌─────────▼────────────┐
        │  SQLite Database         │  │  File Storage        │
        │  ──────────────────────  │  │  ────────────────   │
        │  • Projects              │  │  • Immutable v001   │
        │  • Files                 │  │  • Immutable v002   │
        │  • Versions              │  │  • metadata.json    │
        │  • Assemblies            │  │  • .lock files      │
        │  • Access logs           │  └──────────────────────┘
        └──────────────────────────┘
```

---

## 2. Architecture Components

### 2.1 SolidWorks Add-in (C# / .NET Framework)

**Purpose:** Engineer-centric interface inside SolidWorks

**Responsibilities:**
- Hook into SWKS events (Save, SaveAs, Open, Close)
- Enforce project selection before save
- Capture metadata (properties, configurations)
- Maintain version numbering
- Enforce read-only state for released files
- Display version history & status

**Event Flow:**

```
Engineer clicks [Save] in SolidWorks
         │
         ▼
Add-in intercepts Save event
         │
    ┌────┴────┐
    │          │
    ▼          ▼
Is file      No → Show project picker
in vault?        │
    │            ▼
    Yes      Store mapping (file → project)
    │
    ▼
Read SWKS properties (author, date, etc.)
    │
    ▼
Generate version (v001, v002, etc.)
    │
    ▼
Check file lock status
    │
    ├─ Locked by other user? → Prevent save
    │
    ├─ File released? → Read-only (prevent save)
    │
    └─ Available? → Proceed
         │
         ▼
     Copy to vault: Projects/ProjectName/CAD/PartName/vXXX/
         │
         ▼
     Create metadata.json with author, timestamp, change note
         │
         ▼
     Update SQLite: Files, Versions, Assemblies tables
         │
         ▼
     Release lock after save
         │
         ▼
     Update status in UI: "v003 - Checked In"
```

**UI Components:**
- **Project Selector Panel:** Dropdown to select/create project
- **Version History Sidebar:** List with timestamps, authors, lifecycle state
- **Check-out Button:** Lock file for editing
- **Check-in Button:** Save & increment version
- **Status Bar:** Shows current version, state, lock holder

### 2.2 Local Vault (Filesystem)

**Purpose:** Immutable, versioned storage for CAD files

**Structure:**
```
PLM_VAULT/
├── config.json                      # Vault-level settings
├── db.sqlite                        # Metadata database
├── Projects/
│   ├── ProjectA/
│   │   ├── metadata.json            # Project info
│   │   ├── CAD/
│   │   │   ├── Bracket_Assembly/
│   │   │   │   ├── v001/
│   │   │   │   │   ├── Bracket_Assembly.SLDASM
│   │   │   │   │   ├── metadata.json
│   │   │   │   │   └── references.json  # Assembly dependency tree
│   │   │   │   ├── v002/
│   │   │   │   │   ├── Bracket_Assembly.SLDASM
│   │   │   │   │   ├── metadata.json
│   │   │   │   │   └── references.json
│   │   │   │   └── v003/
│   │   │   │
│   │   │   ├── BracketBase_Part/
│   │   │   │   ├── v001/
│   │   │   │   ├── v002/
│   │   │   │   └── metadata.json
│   │   │   │
│   │   │   └── BracketCover_Part/
│   │   │       ├── v001/
│   │   │       └── metadata.json
│   │   │
│   │   └── Drawings/
│   │       └── Bracket_Assembly_Drawing/
│   │           ├── v001/
│   │           │   ├── Bracket_Assembly_Drawing.SLDDRW
│   │           │   └── metadata.json
│   │           └── v002/
│   │
│   └── ProjectB/
│
├── Locks/
│   ├── ProjectA_Bracket_Assembly.lock
│   └── ProjectA_BracketBase_Part.lock
│
└── Logs/
    └── access_log.json
```

**File Rules:**
1. **Never overwrite** existing files → Always create new version directory
2. **Immutable versions** → v001, v002, v003 are read-only
3. **Metadata per version** → metadata.json alongside CAD file
4. **Assembly references** → Store PLM IDs, not hardcoded paths
5. **Unique IDs** → Each part has UUID for cross-project reference

**metadata.json Structure:**
```json
{
  "plm_id": "PLM-PAR-001",
  "file_name": "BracketBase_Part",
  "version": 1,
  "revision": "A",
  "author": "john.smith",
  "created_timestamp": "2026-01-15T14:32:00Z",
  "modified_timestamp": "2026-01-15T14:32:00Z",
  "change_note": "Initial design based on spec-001",
  "lifecycle_state": "In-Work",
  "locked_by": null,
  "lock_timestamp": null,
  "custom_properties": {
    "Material": "Aluminum 6061",
    "Weight": "250g",
    "Configuration": "Default"
  },
  "checksum": "sha256:abc123...",
  "parent_assembly": "PLM-ASM-001",
  "checked_out_count": 0
}
```

---

## 3. Database Schema (SQLite → PostgreSQL)

### 3.1 Core Tables

```sql
-- Projects
CREATE TABLE projects (
  project_id INTEGER PRIMARY KEY AUTOINCREMENT,
  plm_id TEXT UNIQUE NOT NULL,           -- PLM-PRJ-001
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  owner TEXT NOT NULL,                   -- Windows username
  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  vault_path TEXT NOT NULL,              -- E:\PLM_VAULT\Projects\ProjectA
  is_active BOOLEAN DEFAULT 1
);

-- Files (CAD files)
CREATE TABLE files (
  file_id INTEGER PRIMARY KEY AUTOINCREMENT,
  plm_id TEXT UNIQUE NOT NULL,           -- PLM-PAR-001
  project_id INTEGER NOT NULL,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,               -- PART, ASSEMBLY, DRAWING
  description TEXT,
  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  modified_date TIMESTAMP,
  current_version INTEGER DEFAULT 1,
  lifecycle_state TEXT DEFAULT 'In-Work', -- In-Work, Released, Obsolete
  locked_by TEXT,                        -- Windows username
  lock_timestamp TIMESTAMP,
  vault_path TEXT,                       -- E:\PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part
  is_active BOOLEAN DEFAULT 1,
  FOREIGN KEY (project_id) REFERENCES projects(project_id),
  INDEX idx_project_file (project_id, file_name),
  INDEX idx_plm_id (plm_id)
);

-- Versions
CREATE TABLE versions (
  version_id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_id INTEGER NOT NULL,
  version_number INTEGER NOT NULL,
  revision_letter TEXT,                  -- A, B, C, etc.
  author TEXT NOT NULL,
  created_timestamp TIMESTAMP,
  change_note TEXT,
  lifecycle_state TEXT,                  -- In-Work, Released, Obsolete
  file_path TEXT NOT NULL,               -- v001\BracketBase_Part.SLDPRT
  checksum TEXT,                         -- SHA256 for integrity
  custom_properties JSON,                -- Serialized metadata
  is_locked BOOLEAN DEFAULT 0,
  FOREIGN KEY (file_id) REFERENCES files(file_id),
  UNIQUE (file_id, version_number),
  INDEX idx_file_version (file_id, version_number)
);

-- Assemblies (parent-child relationships)
CREATE TABLE assembly_relationships (
  relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
  assembly_file_id INTEGER NOT NULL,     -- Parent (assembly)
  component_file_id INTEGER NOT NULL,    -- Child (part)
  component_version INTEGER NOT NULL,    -- Which version is used
  instance_count INTEGER DEFAULT 1,      -- How many times used
  added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (assembly_file_id) REFERENCES files(file_id),
  FOREIGN KEY (component_file_id) REFERENCES files(file_id),
  INDEX idx_assembly (assembly_file_id),
  INDEX idx_component (component_file_id)
);

-- Access Control & Locks
CREATE TABLE file_locks (
  lock_id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_id INTEGER NOT NULL,
  locked_by TEXT NOT NULL,              -- Windows username
  lock_timestamp TIMESTAMP,
  lock_release_timestamp TIMESTAMP,
  lock_reason TEXT,                     -- 'Edit', 'Review', etc.
  session_id TEXT,                      -- Unique session identifier
  FOREIGN KEY (file_id) REFERENCES files(file_id),
  INDEX idx_active_locks (file_id, lock_release_timestamp)
);

-- Version Promotion Log (lifecycle changes)
CREATE TABLE version_transitions (
  transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_id INTEGER NOT NULL,
  version_id INTEGER NOT NULL,
  from_state TEXT,
  to_state TEXT,
  promoted_by TEXT,
  promotion_timestamp TIMESTAMP,
  promotion_note TEXT,
  FOREIGN KEY (file_id) REFERENCES files(file_id),
  FOREIGN KEY (version_id) REFERENCES versions(version_id)
);

-- Access Log
CREATE TABLE access_log (
  log_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user TEXT NOT NULL,
  action TEXT NOT NULL,                 -- OPEN, SAVE, PROMOTE, DELETE
  file_id INTEGER,
  project_id INTEGER,
  action_timestamp TIMESTAMP,
  details JSON,
  FOREIGN KEY (file_id) REFERENCES files(file_id),
  FOREIGN KEY (project_id) REFERENCES projects(project_id),
  INDEX idx_user_timestamp (user, action_timestamp)
);
```

### 3.2 Key Design Decisions

| Decision | Why |
|----------|-----|
| **Immutable versions** | No data loss, full history, rollback capability |
| **PLM IDs (PLM-PAR-001)** | Assembly refs stay valid across directory moves |
| **JSON custom properties** | Flexibility for SWKS metadata, no schema rigidity |
| **Checksums (SHA256)** | Detect file corruption, verify vault integrity |
| **Timestamps UTC** | Timezone-independent, multi-region ready |
| **Session IDs for locks** | Detect stale locks, prevent accidental conflicts |

### 3.3 Migration to PostgreSQL

**MVP (SQLite):**
- Single machine, direct file access
- Fast for small teams (<50 projects)
- No server infrastructure

**v1 → PostgreSQL:**
```python
# Migration strategy (not implemented yet)
1. Export SQLite schema
2. Create PostgreSQL tables (same structure)
3. Use pg_load_data() for bulk insert
4. Validate checksums & row counts
5. Update connection strings in all components
6. Run parallel validation for 24 hours
7. Cutover with roll-back plan
```

---

## 4. Versioning Algorithm

### 4.1 Version Increment Logic

```
First Save:
  v001 (version=1, revision='')

Subsequent Saves by Same Author:
  v001 → v002 → v003 → ... (version++)

Lifecycle Promotion:
  v003 → v003 + revision='A' (In-Work → Released)
  v003A → v003B (Released → Revised)

Major Redesign (Manual):
  User selects "New Major Version"
  → Creates v004 (resets revision to '')

Obsolete:
  v005 → marked obsolete (no changes, historical only)
```

**Database Impact:**
```
Version v003:
  version_number=3
  revision_letter=''
  lifecycle_state='In-Work'

After promotion to Released:
  version_number=3
  revision_letter='A'
  lifecycle_state='Released'
```

---

## 5. SolidWorks Add-in Event Flow

### 5.1 Event Interception Strategy

```csharp
// Hook into SWKS API events
SolidWorksApp.OnSaveDocument       → CaptureMetadata() → CheckLock() → Save()
SolidWorksApp.OnOpenDocument       → CheckReadOnly() → ShowVersionHistory()
SolidWorksApp.OnCloseDocument      → ReleaseLock()
SolidWorksApp.OnUnload             → CleanupSessions()
```

### 5.2 Detailed Save Flow

```
1. User clicks "Save" in SolidWorks
   ├─ SWKS API fires: ModelDoc2.OnSaveDocument
   │
2. Add-in intercepts event
   ├─ Get current file path: "C:\Users\john\Desktop\Part1.SLDPRT"
   │
3. Check if file in vault
   ├─ Query DB: SELECT * FROM files WHERE vault_path LIKE '%Part1%'
   ├─ If NOT found:
   │  └─ Show UI: "Select project for this file"
   │     ├─ User picks "ProjectA"
   │     ├─ Create file record in DB
   │     └─ Set file_id
   │
4. Check lock status
   ├─ Query DB: SELECT locked_by FROM files WHERE file_id = ?
   ├─ If locked AND locked_by != current_user:
   │  └─ BLOCK SAVE: "Locked by john.smith since 14:30"
   │
5. Read SWKS properties
   ├─ Get custom properties (Material, Weight, etc.)
   ├─ Get configurations
   ├─ Get current author (Windows user)
   │
6. Get next version number
   ├─ Query: SELECT MAX(version_number) FROM versions WHERE file_id = ?
   ├─ next_version = MAX + 1 (or 1 if first save)
   │
7. Create vault directory
   ├─ Create: PLM_VAULT\Projects\ProjectA\CAD\Part1\v003\
   │
8. Copy file to vault
   ├─ Copy: Part1.SLDPRT → vault\v003\Part1.SLDPRT
   │
9. Generate metadata.json
   ├─ Write JSON with author, timestamp, properties
   │
10. Update database
    ├─ INSERT INTO versions (file_id, version_number, author, created_timestamp, ...)
    ├─ UPDATE files SET current_version = 3
    │
11. Update working file
    ├─ Keep local copy open (user continues editing)
    ├─ Local copy = read-write (for editing)
    ├─ Vault copy = immutable (archive)
    │
12. Acquire lock (if auto-checkout enabled)
    ├─ Set locked_by = current_user in files table
    │
13. Update UI Status Bar
    ├─ Show: "v003 - In-Work - Checked out to john.smith"
    │
14. Log action
    ├─ INSERT INTO access_log (user, action='SAVE', file_id, ...)
```

---

## 6. File Locking & Access Control

### 6.1 Lock States

```
STATE 1: Available
  ├─ Any user can check-out
  ├─ Multiple users can READ-ONLY
  └─ locked_by = NULL

STATE 2: Checked-Out (Edit Lock)
  ├─ Single user: READ-WRITE
  ├─ Other users: READ-ONLY (greyed out UI)
  └─ locked_by = 'john.smith'

STATE 3: Released (Lifecycle Lock)
  ├─ All users: READ-ONLY
  ├─ No check-out allowed
  └─ Changes require new major version

STATE 4: Obsolete
  ├─ All users: READ-ONLY (historical)
  ├─ Cannot be selected for new assemblies
  └─ Visible for traceability
```

### 6.2 Lock Acquisition

```csharp
// When user clicks "Check-Out" button in Add-in UI
public void CheckoutFile(int fileId)
{
    var existingLock = db.GetActiveLock(fileId);
    
    if (existingLock != null && existingLock.LockedBy != CurrentUser)
    {
        ShowError($"Locked by {existingLock.LockedBy} since {existingLock.LockTime}");
        return;
    }
    
    // Create lock with session ID
    var sessionId = Guid.NewGuid().ToString();
    db.CreateLock(fileId, CurrentUser, sessionId);
    
    // Make local SWKS file read-write
    MakeFileReadWrite(currentFilePath);
    
    UpdateUI("Checked-Out");
}
```

### 6.3 Stale Lock Detection

```
Lock acquired: 2026-01-15 14:00:00 (john.smith)
Current time:  2026-01-16 10:00:00 (20 hours later)

Background task runs every 30 minutes:
  ├─ Query: SELECT * FROM file_locks WHERE lock_release_timestamp IS NULL
  ├─ If (current_time - lock_timestamp) > 24 hours:
  │  ├─ Check if session is active (heartbeat)
  │  ├─ If no heartbeat: Release stale lock
  │  └─ Log: "Stale lock released for BracketBase_Part"
```

---

## 7. Lifecycle Management

### 7.1 Lifecycle States

```
┌──────────────┐
│  In-Work     │  ← Default for new files
│  (Editable)  │  ← Multiple saves allowed
└──────┬───────┘   ← locked_by can be anyone
       │
       │ [Promote to Released]
       ▼
┌──────────────┐
│  Released    │  ← No changes allowed
│  (Read-Only) │  ← Creates v003A
└──────┬───────┘   ← Next save = new major version
       │
       │ [Obsolete for new assemblies]
       ▼
┌──────────────┐
│  Obsolete    │  ← Historical only
│  (Archive)   │  ← Cannot be used in new assemblies
└──────────────┘   ← Available for reference
```

### 7.2 Promotion Flow

**In-Work → Released:**
```
Engineer clicks: "Promote to Released"
  ├─ Validates current version is stable
  ├─ Adds revision letter 'A' to v003 → v003A
  ├─ Sets lifecycle_state = 'Released'
  ├─ Updates database
  ├─ Next save creates new major version (v004)
  └─ UI shows "v003A - RELEASED (Read-Only)"
```

**Lock behavior after Release:**
```
Before Release:
  • User can edit file
  • User-driven versions: Explicit "Create Version" creates v001, v002, v003
  • Regular saves update local file without creating versions

After Release to v003A:
  • User cannot edit current file
  • SWKS file becomes read-only (enforced by Add-in)
  • If user wants to edit: Create new major version (v004)
    ├─ This is a separate branch
    ├─ User gets a new, editable copy
    └─ v003A remains unchanged
```

---

## 8. Assembly Reference Management

### 8.1 The Challenge

**Problem:** Assemblies hardcode file paths → Files move → Assembly breaks

**Solution:** Store PLM IDs instead of paths

### 8.2 Assembly Metadata

Each assembly file stores `references.json`:

```json
{
  "assembly_plm_id": "PLM-ASM-001",
  "assembly_name": "Bracket_Assembly",
  "assembly_version": 2,
  "created_date": "2026-01-10T10:00:00Z",
  "components": [
    {
      "instance_name": "BracketBase_Part-1",
      "component_plm_id": "PLM-PAR-001",
      "component_version": 3,
      "component_file_name": "BracketBase_Part.SLDPRT",
      "quantity": 1,
      "insertion_state": "Configured",
      "suppressed": false
    },
    {
      "instance_name": "BracketCover_Part-1",
      "component_plm_id": "PLM-PAR-002",
      "component_version": 1,
      "component_file_name": "BracketCover_Part.SLDPRT",
      "quantity": 1,
      "insertion_state": "Resolved",
      "suppressed": false
    }
  ]
}
```

### 8.3 Assembly Save Flow

```
Engineer saves assembly (Bracket_Assembly.SLDASM)
  ├─ Add-in extracts component references from SWKS
  ├─ For each component:
  │  ├─ Get file_id from local mapping
  │  ├─ Read plm_id from child's metadata.json
  │  ├─ Store (plm_id, version_used)
  │
  ├─ Generate references.json with PLM IDs
  ├─ Insert into assembly_relationships table:
  │  ├─ assembly_file_id (Bracket_Assembly)
  │  ├─ component_file_id (BracketBase_Part)
  │  ├─ component_version (3)
  │
  ├─ Save assembly to vault
  └─ Store references.json alongside assembly
```

### 8.4 Assembly Resolution (Open)

```
Engineer opens assembly: "Bracket_Assembly.SLDASM"
  ├─ Add-in reads references.json
  ├─ For each component:
  │  ├─ Lookup PLM ID in database
  │  ├─ Get vault path: PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part\v003\
  │  ├─ SWKS loads component from vault path
  │  └─ Status: "Loaded from vault (v003)"
  │
  └─ Assembly fully resolved, ready for editing
```

---

## 9. Security Model

### 9.1 Authentication

```
MVP: Windows user (no login required)
  ├─ Read from: Environment.UserName
  ├─ No password needed (same machine)
  └─ Audit: Always track user in access_log

v1+: Optional password + role-based access
  ├─ Roles: Owner, Editor, Viewer
  ├─ File permissions: {Owner, Editor, Viewer}
  └─ Database: users, roles, permissions tables
```

### 9.2 File Permissions

```
File State: Released (v003A)
  ├─ Owner: Can promote to Obsolete
  ├─ Editor: Can view only (read-only in SWKS)
  ├─ Viewer: Can view only (read-only in SWKS)

File State: In-Work (v003)
  ├─ Checked-out to john.smith:
  │  ├─ john.smith: READ-WRITE (can edit)
  │  ├─ Others: READ-ONLY (grey out UI, prevent save)
  │
  ├─ Not checked-out:
     └─ Any user: Can check-out → becomes editor
```

### 9.3 Preventing Accidental Overwrite

```
Engineer A: Editing Part1.SLDPRT (checked-out)
Engineer B: Tries to save Part1.SLDPRT
  ├─ Add-in queries: SELECT locked_by FROM files WHERE plm_id = ?
  ├─ Returns: "john.smith"
  ├─ Add-in shows: "BLOCKED: Part1 locked by john.smith"
  ├─ Options:
  │  ├─ Wait for john to check-in
  │  ├─ Request john to release lock (via Slack/email)
  │  └─ Create new branch/version
  │
  └─ Engineer B cannot overwrite john's work
```

---

## 10. Data Flow Diagrams

### 10.1 Complete System Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       USER WORKFLOW                                 │
│  Engineer → SolidWorks → Add-in → Vault → Database → CLI Tool      │
└─────────────────────────────────────────────────────────────────────┘

SAVE OPERATION:
  User file: "C:\Users\john\Desktop\Part1.SLDPRT"
       │ (Engineer clicks Save)
       ▼
  SolidWorks App (SWKS API Event)
       │
       ▼
  Add-in Event Handler (OnSaveDocument)
       │
       ├─ Get file metadata from SWKS (properties, config)
       ├─ Check project assignment (DB query)
       ├─ Check lock status (DB query)
       ├─ Check lifecycle state (DB query)
       │
       ▼
  Lock Manager
       │
       ├─ Is file locked by another user?
       │  └─ If yes: Show error → Block save
       │
       ├─ Is file Released?
       │  └─ If yes: Show error → Block save
       │
       └─ Lock acquired: Create session lock
            │
            ▼
       Version Manager
            │
            ├─ Query: SELECT MAX(version_number) FROM versions
            ├─ Next version = 3
            └─ Create vault directory: Projects\ProjectA\CAD\Part1\v003\
                 │
                 ▼
            File Copy Manager
                 │
                 ├─ Copy Part1.SLDPRT → vault\v003\Part1.SLDPRT
                 ├─ Generate metadata.json
                 └─ Generate checksum (SHA256)
                      │
                      ▼
                 Database Writer
                      │
                      ├─ INSERT INTO versions (file_id, version_number, author, ...)
                      ├─ UPDATE files SET current_version = 3
                      ├─ UPDATE file_locks SET locked_by = 'john.smith'
                      └─ INSERT INTO access_log (action='SAVE', ...)
                           │
                           ▼
                      UI Update
                           │
                           ├─ Status: "v003 - In-Work - Checked out to john.smith"
                           ├─ Version history refreshed
                           └─ Save completes successfully


OPEN OPERATION:
  Vault file: "PLM_VAULT\Projects\ProjectA\CAD\Part1\v003\Part1.SLDPRT"
       │
       ▼
  Engineer double-clicks file in File Explorer
  (Or uses "Open from Vault" button in Add-in)
       │
       ▼
  Add-in intercepts file open
       │
       ├─ Lookup file metadata: SELECT * FROM files WHERE vault_path = ?
       ├─ Read metadata.json
       ├─ Check lifecycle_state:
       │  ├─ If Released: Make working copy READ-ONLY
       │  └─ If In-Work: Make working copy READ-WRITE
       │
       ├─ Check if already locked:
       │  ├─ If locked by current_user: Resume editing (keep lock)
       │  └─ If locked by other_user: Open as READ-ONLY, show who has it
       │
       ├─ Extract assembly references (if assembly):
       │  ├─ Read references.json
       │  ├─ For each component (by PLM ID):
       │  │  ├─ Query: SELECT vault_path FROM files WHERE plm_id = ?
       │  │  ├─ Get version_used from references.json
       │  │  ├─ Construct full path: vault\vXXX\component.sldprt
       │  │  └─ Update SWKS assembly reference
       │  │
       │  └─ SWKS opens assembly with resolved references
       │
       └─ Update UI:
            ├─ Show version history
            ├─ Show component tree with versions
            └─ Status: "v003 - In-Work - Available for checkout"


PROMOTE OPERATION:
  Engineer selects: "Promote to Released"
       │
       ▼
  Add-in UI: "Confirm promotion of Part1 v003 → v003A"
       │
       ▼
  Engineer clicks "Confirm"
       │
       ├─ Validate version is stable (final save > 5 min ago)
       ├─ Set lifecycle_state = 'Released'
       ├─ Set revision_letter = 'A'
       │
       ▼
  Database Update
       │
       ├─ UPDATE versions SET lifecycle_state = 'Released', revision_letter = 'A'
       ├─ UPDATE files SET lifecycle_state = 'Released'
       ├─ INSERT INTO version_transitions (from_state, to_state, promoted_by)
       ├─ INSERT INTO access_log (action='PROMOTE')
       │
       ▼
  Working Copy Update
       │
       ├─ Set current working file to READ-ONLY (via SWKS API)
       ├─ Disable Save button
       └─ Show UI: "v003A - RELEASED - No edits allowed"
```

---

## 11. Failure Cases & Mitigation

| Failure | Impact | Mitigation |
|---------|--------|-----------|
| **Network/disk full** | Cannot save to vault | Queue saves, retry with backoff, warn user |
| **Stale lock held** | File stuck → No edits | Auto-release after 24h, manual unlock (admin) |
| **SWKS crashes mid-save** | Partial file in vault | Checksum validation, cleanup script |
| **Assembly component deleted** | Broken reference | Mark as "Orphaned", show warning in UI |
| **Concurrent saves** | Race condition | Database lock (SQLite: implicit), transaction rollback |
| **File moved outside PLM** | DB out of sync | Periodic vault scan, detect orphaned files |
| **Vault corruption** | Data loss | Checksum mismatch → Alert, restore from backup |
| **User forgets to check-in** | Lock held forever | Timeout + email notification |

---

## 12. Component Responsibilities

| Component | Responsibility | Tech | Failure Point |
|-----------|-----------------|------|--------------|
| **SolidWorks Add-in** | Event interception, UI, metadata capture | C# .NET | SWKS API changes, UI hang |
| **Vault Manager** | Directory structure, file copy, immutability | Python + Filesystem | Disk full, permissions error |
| **Database Layer** | ACID transactions, locking, queries | SQLite + ORM | Deadlock, corruption |
| **Lock Manager** | Acquisition, release, timeout | Python + DB | Stale locks, race conditions |
| **Version Manager** | Increment logic, lifecycle transitions | Python | Duplicate versions |
| **Assembly Resolver** | Reference mapping, vault path resolution | Python + SWKS API | Circular dependencies |
| **CLI Tool** | Non-SWKS operations (project create, promote) | Python | File I/O errors |
| **FastAPI Backend** | (Phase 2) Metadata API, search, multi-user | Python FastAPI | Network outage, DB connection pool |

---

## 13. Development Roadmap

### **MVP (v0.1) - Single Machine, Filesystem Vault**
- ✅ Vault directory structure
- ✅ SQLite database schema
- ✅ SolidWorks Add-in event handlers
- ✅ Basic version increment
- ✅ File locking (single machine)
- ✅ Metadata capture
- ⚪ CLI tool (basic)
- **Timeline:** 6-8 weeks

### **v0.5 - Assembly Support & CLI**
- ✅ Assembly reference management (PLM IDs)
- ✅ Lifecycle promotion (In-Work → Released → Obsolete)
- ✅ CLI tool (create project, list versions, promote)
- ✅ Access logging & audit trail
- ⚪ Role-based access control (basic)
- **Timeline:** 4 weeks

### **v1.0 - Production Ready (Single Machine)**
- ✅ Backup/restore utilities
- ✅ Vault integrity checks (checksums)
- ✅ Performance optimization (indexed queries)
- ✅ Error handling & recovery
- ✅ Comprehensive documentation
- ✅ User training & onboarding
- **Timeline:** 4 weeks

### **v1.5 - LAN Sharing (Optional)**
- ⚪ Network vault (mapped drive)
- ⚪ Conflict detection (same file edited on 2 machines)
- ⚪ Async file sync
- **Timeline:** 6 weeks

### **v2.0 - FastAPI Backend + PostgreSQL**
- ⚪ REST API for metadata
- ⚪ PostgreSQL migration
- ⚪ Multi-user sync
- ⚪ Advanced search & filtering
- ⚪ Web dashboard (optional)
- **Timeline:** 8 weeks

---

## 14. Next Steps

1. **Create vault directory structure** (manual + code generator)
2. **Implement SQLite schema** (database initialization script)
3. **Build SolidWorks Add-in foundation** (C# project, event handlers)
4. **Build CLI tool** (Python: create, list, promote operations)
5. **Implement file versioning & locking** (core business logic)
6. **Test with sample assemblies** (validation)
7. **Deploy FastAPI backend** (Phase 2)

