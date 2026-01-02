# Versioning Algorithm & Lifecycle Management

**Purpose:** Define immutable versioning scheme, lifecycle state transitions, and revision/build numbering

---

## 1. Version Numbering Scheme

### Format: `vXXX[Revision]`

- **vXXX** = Version number (v001, v002, v003, etc.)
- **[Revision]** = Optional revision letter (A, B, C, ...)

### Examples

```
v001        Initial version (In-Work)
v002        Second design iteration (In-Work)
v003A       Released for manufacturing
v003B       Revision after production feedback (Released)
v004        Major redesign (In-Work)
```

### Version vs. Revision

| Aspect | Version | Revision |
|--------|---------|----------|
| **Trigger** | Each user save | Lifecycle promotion |
| **Mutability** | Immutable | Immutable |
| **Example** | v003 | v003A, v003B |
| **When used** | Design iteration | Engineering changes |
| **Database** | version_number | revision_letter |

---

## 2. Lifecycle State Diagram

```
┌──────────────────────────────────────────────────────────┐
│                  LIFECYCLE FLOW                          │
└──────────────────────────────────────────────────────────┘

Initial State:
┌────────────┐
│ In-Work    │ ← All new files start here
│ (Editable) │   - Multiple saves allowed
└─────┬──────┘   - Version increments: v001 → v002 → v003
      │
      │ [Promote to Released]
      │ (Engineer clicks "Release" button)
      ▼
┌────────────┐
│ Released   │ ← Production use (immutable)
│ (Read-Only)│   - No further edits allowed
│   v003A    │   - Adds revision letter
└─────┬──────┘   - Next save creates new major version (v004)
      │
      │ [Obsolete for new assemblies]
      │ (Can still reference for traceability)
      ▼
┌────────────┐
│ Obsolete   │ ← Historical archive
│ (Read-Only)│   - Cannot be used in new assemblies
│            │   - Available for reference
└────────────┘

Optional Transition: Released → Revised
┌────────────┐
│ Released   │
│   v003A    │ ← Found issue in production
└─────┬──────┘
      │ [Create revision]
      │
      ▼
   v003B (still Released, but revised)
```

---

## 3. State Machine Rules

### In-Work → Released (Promotion)

```python
def promote_to_released(file_id, version_num, user):
    """
    Preconditions:
    - User must be owner or have permission
    - Current version must be stable (final save > 5 min ago)
    - File cannot already be Released
    
    Actions:
    - Set lifecycle_state = 'Released'
    - Add revision_letter = 'A' (first release)
    - Make local copy read-only
    - Log promotion to audit trail
    - Notify team
    
    Post-conditions:
    - User cannot edit this version anymore
    - File becomes read-only in SolidWorks
    - Next save will create new major version (v004)
    """
    
    if version.lifecycle_state != "In-Work":
        raise ValueError(f"Cannot promote {version.lifecycle_state} version")
    
    if not is_stable(version):
        raise ValueError("Version not stable (final save < 5 min ago)")
    
    # Update database
    version.lifecycle_state = "Released"
    version.revision_letter = "A"
    version.save()
    
    # Update file record
    file.lifecycle_state = "Released"
    file.save()
    
    # Log action
    log_action(
        action="PROMOTE",
        file_id=file_id,
        from_state="In-Work",
        to_state="Released",
        promoted_by=user,
        timestamp=now()
    )
    
    return True
```

### Released → In-Work (New Major Version)

```python
def create_major_version(file_id, user):
    """
    User wants to edit released file → Create new major version
    
    Preconditions:
    - Current version is Released
    - User has edit permission
    
    Actions:
    - Increment major version: v003A → v004
    - Set lifecycle_state = 'In-Work'
    - Reset revision_letter = ''
    - User gets new, editable copy
    - Original v003A remains unchanged
    
    Post-conditions:
    - User can edit v004
    - v003A remains Released forever
    """
    
    current_version = get_latest_version(file_id)
    
    if current_version.lifecycle_state != "Released":
        raise ValueError("Only Released versions support major version bumps")
    
    # Create new version
    new_version_num = current_version.version_number + 1
    
    version = Version(
        file_id=file_id,
        version_number=new_version_num,
        revision_letter="",
        lifecycle_state="In-Work",
        author=user
    )
    version.save()
    
    file = get_file(file_id)
    file.current_version = new_version_num
    file.lifecycle_state = "In-Work"
    file.save()
    
    return version
```

### Released → Revised (Engineering Change)

```python
def create_revision(file_id, version_num, user, ecn_note):
    """
    Released version needs engineering change
    
    Example:
    - v003A (Released) → Issue found in production
    - Create v003B (still Released, but revised)
    
    Preconditions:
    - Current version is Released
    - User has change authorization
    
    Actions:
    - Increment revision letter: A → B → C...
    - Set lifecycle_state = 'Released' (stays released)
    - File remains read-only
    - Can be updated to reflect design change (no new major version)
    
    Post-conditions:
    - v003B is released (not in-work)
    - Users will load v003B instead of v003A
    """
    
    current = get_version(file_id, version_num)
    
    if current.lifecycle_state != "Released":
        raise ValueError("Only Released versions can be revised")
    
    # Next letter
    next_letter = chr(ord(current.revision_letter) + 1)
    
    new_revision = Version(
        file_id=file_id,
        version_number=version_num,
        revision_letter=next_letter,
        lifecycle_state="Released",
        author=user,
        change_note=f"Engineering change: {ecn_note}"
    )
    new_revision.save()
    
    log_action(
        action="REVISE",
        from_state="Released",
        to_state="Released",
        revision=next_letter,
        promoted_by=user,
        details=ecn_note
    )
    
    return new_revision
```

---

## 4. Save Flow (Versioning Algorithm)

### MVP Algorithm: Simple Increment

```
Save triggered by user in SolidWorks
    │
    ├─ Get file_id from vault mapping
    │
    ├─ Query: SELECT MAX(version_number) FROM versions WHERE file_id = ?
    │
    ├─ If result is NULL:
    │  └─ next_version = 1 (first save)
    │
    ├─ Else:
    │  └─ next_version = MAX + 1
    │
    ├─ Create directory: vault/ProjectA/CAD/Part1/v{next_version}/
    │
    ├─ Copy file to vault
    │
    ├─ Create metadata.json
    │
    ├─ INSERT into versions table:
    │     version_id=NULL (auto-increment),
    │     file_id=5,
    │     version_number={next_version},
    │     revision_letter='',
    │     author='john.smith',
    │     created_timestamp=NOW(),
    │     change_note='User input',
    │     lifecycle_state='In-Work'
    │
    └─ File saved successfully, version = v{next_version}
```

### Python Implementation

```python
def save_to_vault(file_path: str, author: str, change_note: str = "", 
                 custom_properties: dict = None) -> dict:
    """
    Core versioning algorithm
    
    Returns:
        {
            'success': True,
            'version_number': 3,
            'revision_letter': '',
            'vault_path': 'e:\PLM_VAULT\Projects\ProjectA\CAD\Part1\v003\',
            'full_path': 'e:\PLM_VAULT\Projects\ProjectA\CAD\Part1\v003\Part1.SLDPRT'
        }
    """
    
    # 1. Get file record
    file = get_file_by_path(file_path)
    if not file:
        raise FileNotFoundError(f"File not in vault: {file_path}")
    
    # 2. Check lock status
    if file['locked_by'] and file['locked_by'] != author:
        raise PermissionError(f"File locked by {file['locked_by']}")
    
    # 3. Check lifecycle
    if file['lifecycle_state'] == 'Released':
        raise ValueError("Cannot save Released version. Create new major version.")
    
    # 4. Get next version number
    db = PLMDatabase(VAULT_ROOT)
    latest = db.get_latest_version(file['file_id'])
    next_version = (latest['version_number'] if latest else 0) + 1
    
    # 5. Create vault directory
    vault_dir = os.path.join(file['vault_path'], f'v{next_version:03d}')
    os.makedirs(vault_dir, exist_ok=True)
    
    # 6. Copy file to vault
    file_name = os.path.basename(file_path)
    vault_file_path = os.path.join(vault_dir, file_name)
    shutil.copy2(file_path, vault_file_path)
    
    # 7. Calculate checksum
    checksum = calculate_sha256(vault_file_path)
    file_size = os.path.getsize(vault_file_path)
    
    # 8. Create metadata.json
    metadata = {
        'file_id': file['file_id'],
        'plm_id': file['plm_id'],
        'file_name': file['file_name'],
        'version': next_version,
        'revision': '',
        'author': author,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'change_note': change_note,
        'lifecycle_state': 'In-Work',
        'checksum': checksum,
        'file_size': file_size,
        'custom_properties': custom_properties
    }
    
    metadata_path = os.path.join(vault_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # 9. Update database
    db.create_version(
        file_id=file['file_id'],
        author=author,
        change_note=change_note,
        file_path=vault_file_path,
        file_size=file_size,
        checksum=checksum,
        custom_properties=custom_properties
    )
    
    # 10. Log action
    db.log_action(
        user=author,
        action='SAVE',
        file_id=file['file_id'],
        details={'version': next_version, 'change_note': change_note}
    )
    
    # 11. Acquire/release lock
    if not file['locked_by']:
        session_id = db.acquire_lock(file['file_id'], author, reason='Edit')
    
    return {
        'success': True,
        'version_number': next_version,
        'revision_letter': '',
        'vault_path': vault_dir,
        'full_path': vault_file_path,
        'checksum': checksum
    }
```

---

## 5. Conflict Detection & Prevention

### Scenario: Engineer A & Engineer B Both Saving

```
Time    Engineer A              Engineer B              Database State
────────────────────────────────────────────────────────────────────
T0      Open Part1 v001         (Not opened)           latest=v001
T1      Edit...                 Open Part1 v001        latest=v001
T2      Click Save              Edit...                latest=v001
        ├─ Get next version
        │  (MAX(version_num)=1)
        └─ next_version = 2
                                 Click Save
                                 ├─ Get next version
                                 │  (MAX(version_num)=1)
                                 └─ next_version = 2
T3      INSERT v002 (lock A)    ⏳ WAIT               latest=v002 (A)
T4                              INSERT v002 (lock B)   ✗ CONFLICT!
                                └─ SQLite UNIQUE
                                   constraint fails
                                   (file_id, version_number)
                                ├─ B's transaction ROLLBACK
                                └─ Show error: "Save conflict"
```

### Prevention Strategy

**UNIQUE Constraint:**
```sql
UNIQUE (file_id, version_number, revision_letter)
```

**Transaction-level lock (SQLite Implicit):**
- SQLite uses table-level locks automatically
- Only one writer at a time
- Readers wait for writers to finish

**Application-level queue:**
```python
import threading
import queue

save_queue = queue.Queue()

def enqueue_save(file_id, author, change_note):
    """Add save to queue (FIFO processing)"""
    save_queue.put({
        'file_id': file_id,
        'author': author,
        'change_note': change_note,
        'timestamp': time.time()
    })

def process_save_queue():
    """Worker thread: process saves one at a time"""
    while True:
        save_request = save_queue.get()
        try:
            save_to_vault(**save_request)
        except Exception as e:
            notify_user(f"Save failed: {e}")
        finally:
            save_queue.task_done()

# Start worker thread
worker = threading.Thread(target=process_save_queue, daemon=True)
worker.start()
```

---

## 6. Immutability Guarantees

### Once a Version is Saved, It Cannot Be Changed

```
Vault structure: (Read-only after save)
v001/
├── Part1.SLDPRT           ← Read-only (immutable)
├── metadata.json          ← Read-only (immutable)
└── checksum.txt           ← Read-only (immutable)

How to enforce:
1. File system permissions (Windows NTFS):
   ICACLS "e:\PLM_VAULT\Projects\ProjectA\CAD\Part1\v001" /grant Users:(CI)(F) /inheritance:r
   ↓
   Users can READ, but not MODIFY or DELETE

2. Checksum validation on load:
   - Read v001/Part1.SLDPRT
   - Calculate SHA256
   - Compare with metadata.json checksum
   - If mismatch → ALERT: "File corrupted!"

3. Database constraints:
   - versions table has NO UPDATE triggers
   - All changes go to new version
   - Old versions are permanent
```

---

## 7. Version Resolution in Assemblies

### When Assembly Requests Component v003, How Does It Load?

```
Assembly: Bracket_Assembly.SLDASM
  - Created: 2026-01-12 (refers to BracketBase_Part v003)
  - Current version: v002

Load assembly → Read v002/references.json:
{
  "components": [
    {
      "component_plm_id": "PLM-PAR-001",
      "component_version": 3,
      "component_file_name": "BracketBase_Part.SLDPRT"
    }
  ]
}

Resolution algorithm:
1. Get component PLM ID: "PLM-PAR-001"
2. Query database: SELECT file_id FROM files WHERE plm_id = 'PLM-PAR-001'
   → file_id = 5
3. Get vault path: SELECT vault_path FROM files WHERE file_id = 5
   → e:\PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part
4. Construct full path: 
   e:\PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part\v003\BracketBase_Part.SLDPRT
5. Load component from vault
6. If v003 is Released → Load as read-only
7. If v003 is missing → Show warning: "Component v003 not found. Use latest (v005)?"
```

---

## 8. Rollback & Recovery

### Scenario: "I need to go back to v002"

```
Current state: v005 (In-Work)
Need: v002 (older design)

Option A: Create v002-based branch
  1. Get v002 file from vault: v002/Part1.SLDPRT
  2. "Branch from v002" → User clicks button
  3. Creates new version v006 as copy of v002
  4. User edits v006
  5. User saves v007, v008...
  
Option B: Revert to v002 (replace current version)
  1. Get v002 file: v002/Part1.SLDPRT
  2. Copy to v006 (new version number, not modification)
  3. Show UI: "Reverted to v002 design"
  4. v005 remains in vault unchanged

Option C: Import v002 as reference
  1. Keep v005
  2. Load v002 alongside for comparison
  3. Engineer manually applies changes from v002 to v005

All options preserve immutability (no version is ever modified, only new versions created)
```

---

## 9. Comparison: Versioning Schemes

| Scheme | Pros | Cons | Use Case |
|--------|------|------|----------|
| **SemVer (1.2.3)** | Indicates compatibility | Complex rules | Software libraries |
| **Date-based (2026.01.15)** | Chronological | Not unique if multiple saves/day | Daily releases |
| **Sequential (v001, v002)** | Simple, immutable | No semantic info | **✅ PLM files (ours)** |
| **Git-style (abc123f)** | Unique, traceable | Unfriendly for CAD | Code repositories |

Our choice: **Sequential versioning (v001, v002, ...)** because:
1. Simple to implement & understand
2. No conflicts (unique per file)
3. Chronological (higher number = newer)
4. Works with immutable vault structure
5. Engineers are familiar with revision schemes

---

## 10. Database Queries for Versioning

```sql
-- Get next version number for a file
SELECT MAX(version_number) FROM versions WHERE file_id = 5;
-- If NULL: next = 1, else next = MAX + 1

-- Get latest version (regardless of lifecycle state)
SELECT * FROM versions 
WHERE file_id = 5 
ORDER BY version_id DESC 
LIMIT 1;

-- Get latest Released version
SELECT * FROM versions 
WHERE file_id = 5 AND lifecycle_state = 'Released'
ORDER BY version_number DESC 
LIMIT 1;

-- Get all versions of a file
SELECT version_number, revision_letter, author, created_timestamp, lifecycle_state
FROM versions
WHERE file_id = 5
ORDER BY version_number DESC;

-- Find files that haven't been released
SELECT f.file_name, f.current_version, COUNT(*) as total_versions
FROM files f
JOIN versions v ON f.file_id = v.file_id
WHERE v.lifecycle_state = 'In-Work'
GROUP BY f.file_id;

-- Get version history timeline
SELECT 
  f.file_name,
  v.version_number,
  v.revision_letter,
  v.author,
  v.created_timestamp,
  v.lifecycle_state,
  v.change_note
FROM files f
JOIN versions v ON f.file_id = v.file_id
WHERE f.plm_id = 'PLM-PAR-001'
ORDER BY v.version_number ASC, COALESCE(v.revision_letter, '') ASC;
```

---

