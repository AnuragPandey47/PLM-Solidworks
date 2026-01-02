# PLM Versioning Algorithm - Corrected
## Version 2.0 - User-Driven Versioning

---

## 1. Core Principle

**Versions are created EXPLICITLY by user action, not automatically on every save.**

```
Regular Saves (No versions)     Create Version        Freeze/Lock
      ↓                              ↓                    ↓
Save, save, save...   → v001 (In-Work) → v002 (In-Work) → v002 (Released/Read-Only)
(local file updates)   User clicks      User clicks        User clicks
                    "Create Version"  "Create Version"   "Freeze Version"
```

---

## 2. User Actions & Their Effects

| User Action | Creates Version? | Makes Read-Only? | Effect |
|---|---|---|---|
| **Save File** | ❌ No | ❌ No | Updates local working file, keeps lock |
| **Create Version** | ✅ Yes (v001→v002) | ❌ No | Copies working file to vault as new version |
| **Freeze Version** | ❌ No | ✅ Yes | Locks in current version, makes read-only |
| **Acquire Lock** | ❌ No | ❌ No | Prevents others from editing |
| **Release Lock** | ❌ No | ❌ No | Allows others to acquire lock |

---

## 3. Save Flow (Regular Save - No Version Created)

```
Engineer saves in SolidWorks
    │
    ├─ Check: Is file in vault? (is file path under e:\PLM_VAULT?)
    │  └─ If NO → Regular SolidWorks save (nothing to do)
    │  └─ If YES → Continue
    │
    ├─ Check: Do I have lock?
    │  └─ Query: SELECT * FROM file_locks WHERE file_id=? AND locked_by=?
    │  └─ If NO → Error: "You must acquire lock first"
    │  └─ If YES → Continue
    │
    ├─ Update lock timestamp (keep it alive)
    │  └─ UPDATE file_locks SET locked_at=NOW()
    │
    ├─ SolidWorks saves file normally (to working directory)
    │
    └─ Message: "✓ File saved. Current version: v002"
       (No new version in vault created)
```

**Result:** Local file updated, lock held, ready for next save or version creation.

---

## 4. Create Version Flow (Explicit User Action)

```
User clicks "Create Version" button in SolidWorks menu
    │
    ├─ Dialog: "Add change note (optional):"
    │  └─ User enters: "Completed initial design, ready for review"
    │
    ├─ Check: Do I have lock?
    │  └─ If NO → Error: "Acquire lock first"
    │  └─ If YES → Continue
    │
    ├─ Get next version number
    │  └─ SELECT MAX(version_number) FROM versions WHERE file_id=?
    │  └─ Current max: 1
    │  └─ Next version: 2
    │
    ├─ Create vault directory
    │  └─ e:\PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part\v002\
    │
    ├─ Copy working file to vault
    │  └─ Copy: C:\Users\john\working\BracketBase.SLDPRT
    │       → e:\PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part\v002\BracketBase.SLDPRT
    │
    ├─ Calculate checksum (SHA256) of file
    │  └─ Checksum: abc123def456...
    │
    ├─ Create metadata.json
    │  └─ {
    │       "version_number": 2,
    │       "state": "In-Work",
    │       "author": "john",
    │       "created_at": "2026-01-02T10:30:00Z",
    │       "change_note": "Completed initial design, ready for review",
    │       "checksum": "abc123def456...",
    │       "file_size_bytes": 2048576
    │     }
    │
    ├─ Insert into database
    │  └─ INSERT INTO versions 
    │       (file_id, version_number, state, author, change_note, checksum)
    │       VALUES (1, 2, 'In-Work', 'john', '...', 'abc123...')
    │
    ├─ Log action
    │  └─ INSERT INTO access_log
    │       (user, action, file_id, details, timestamp)
    │       VALUES ('john', 'create_version', 1, '{"version": 2}', NOW())
    │
    └─ Success: "✓ Version v002 created (In-Work)"
       ✓ User can continue editing locally
       ✓ v001 is now locked in vault (immutable)
       ✓ Others can see v001 but not edit it
```

**Result:** v002 exists in vault, user holds lock, can continue editing.

---

## 5. Freeze Version Flow (Lock & Make Read-Only)

```
User clicks "Freeze Version" button to finalize/release version
    │
    ├─ Dialog: "Freeze v002 as final? This makes it read-only."
    │  └─ User confirms
    │
    ├─ Check: Do I have lock?
    │  └─ If NO → Error
    │  └─ If YES → Continue
    │
    ├─ Update version state in database
    │  └─ UPDATE versions SET state='Released' 
    │       WHERE file_id=1 AND version_number=2
    │
    ├─ Create freeze marker file
    │  └─ Create: e:\PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part\v002\.frozen
    │  └─ Contents: "Frozen by john at 2026-01-02 10:45:00 (timestamp)"
    │
    ├─ Make file read-only in SolidWorks UI
    │  └─ Disable edit buttons
    │  └─ Show: "This version is frozen (Read-Only)"
    │
    ├─ Release lock (version is now protected)
    │  └─ DELETE FROM file_locks WHERE file_id=1 AND locked_by='john'
    │
    ├─ Log action
    │  └─ INSERT INTO access_log
    │       (user, action, file_id, details, timestamp)
    │       VALUES ('john', 'freeze_version', 1, '{"version": 2}', NOW())
    │
    └─ Success: "✓ Version v002 Frozen (Released/Read-Only)"
       ✓ File is now immutable
       ✓ Others can open as reference (read-only)
       ✓ Lock automatically released
       ✓ Ready for next person to create v003
```

**Result:** v002 is frozen, read-only, immutable. Lock released. Others can now acquire lock to create v003.

---

## 6. Acquire Lock Flow

```
User wants to start editing:
    │
    ├─ Click "Acquire Lock" button
    │
    ├─ Check: Is file already locked?
    │  └─ Query: SELECT * FROM file_locks 
    │            WHERE file_id=1 AND expires_at > NOW()
    │
    │  ├─ If locked by me:
    │  │  └─ Message: "You already have lock"
    │  │  └─ Show expiration time
    │  │
    │  ├─ If locked by someone else:
    │  │  └─ Message: "Locked by sarah (expires 4:00 PM)"
    │  │  └─ ACTION: DENY access
    │  │
    │  └─ If lock expired:
    │     └─ Auto-cleanup: DELETE old lock record
    │     └─ Continue to acquire new lock
    │
    ├─ Acquire lock
    │  └─ INSERT INTO file_locks
    │       (file_id, locked_by, session_id, expires_at)
    │       VALUES (1, 'john', 'SESSION_XYZ', datetime('now', '+24 hours'))
    │
    └─ Success: "✓ Lock acquired (expires in 24 hours)"
       ✓ User can now save and create versions
       ✓ Others cannot edit this file
```

**Result:** User has exclusive lock for 24 hours. Can save and create versions.

---

## 7. Release Lock Flow

```
User explicitly releases lock:
    │
    ├─ Click "Release Lock" button
    │  OR
    ├─ Click "Freeze Version" (auto-releases)
    │
    ├─ Delete lock record
    │  └─ DELETE FROM file_locks 
    │       WHERE file_id=1 AND locked_by='john'
    │
    └─ Other users can now acquire lock
```

---

## 8. Conflict Detection & Prevention

### Scenario 1: User tries to edit while locked by someone else
```
User A clicks "Acquire Lock"
    → Database check: locked by 'sarah', expires 4:00 PM
    → System DENIES access
    → Message: "File locked by sarah. Contact her or wait until 4:00 PM"
```

### Scenario 2: User tries to edit a Frozen version
```
User B opens Frozen v002
    → Check: state='Released'
    → System opens as READ-ONLY
    → Edit buttons disabled
    → Option: "Create v003 from this version?"
```

### Scenario 3: Lock expires after 24 hours
```
User A acquired lock at 10:00 AM
24 hours later, User A still disconnected
    → System detects: expires_at < NOW()
    → Auto-delete: DELETE old lock
    → User B can now acquire lock
```

### Scenario 4: User forgets to release lock
```
User A locked file at 9:00 AM
User B wants to edit at 4:00 PM (7 hours later)
    → Check: lock expires at 10:00 AM next day
    → Message: "Locked by john (expires in 17 hours)"
    → If critical: Admin can manually delete lock (rare)
```

---

## 9. Version State Diagram

```
                ┌─────────────┐
                │   NEW FILE  │
                └──────┬──────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  Local Working Copy    │
          │ (not in vault)         │
          │ • Save many times     │
          │ • No versions yet     │
          └─────────┬──────────────┘
                    │
          [Acquire Lock button]
                    │
                    ▼
          ┌────────────────────────┐
          │   LOCKED BY YOU        │
          │ • Can save freely      │
          │ • Can create versions  │
          └─────────┬──────────────┘
                    │
          [Create Version button]
                    │
                    ▼
          ┌────────────────────────┐
          │  v001 (In-Work)        │
          │ • In vault now         │
          │ • Still editable       │
          │ • You keep lock        │
          └─────────┬──────────────┘
                    │
       ┌────────────┴────────────┐
       │                         │
       ▼ (Keep editing)     [Freeze Version]
   [Save again]                 │
       │                        ▼
       └──────► v002 (Released)
               (In-Work)        • Read-Only
                                • Immutable
                                • Lock released
                                • Others can create v003
```

---

## 10. Database Schema Updates

```sql
-- versions table (NEW columns)
CREATE TABLE versions (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    state TEXT DEFAULT 'In-Work',  -- 'In-Work', 'Released', 'Obsolete'
    author TEXT NOT NULL,
    change_note TEXT,
    checksum TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_id, version_number)
);

-- file_locks table (UPDATED)
CREATE TABLE file_locks (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL UNIQUE,
    locked_by TEXT NOT NULL,       -- Windows username
    session_id TEXT,               -- For multi-session tracking
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL, -- 24-hour expiration
    FOREIGN KEY (file_id) REFERENCES files(id)
);

-- Useful queries
SELECT * FROM versions WHERE file_id=1 ORDER BY version_number DESC;
SELECT * FROM file_locks WHERE expires_at > NOW();
UPDATE versions SET state='Released' WHERE file_id=1 AND version_number=2;
DELETE FROM file_locks WHERE expires_at < NOW();
```

---

## 11. CLI Commands

```bash
# Acquire lock
python plm.py lock acquire --file "BracketBase_Part"
# Output: ✓ Lock acquired (expires in 24 hours)

# Create version (after editing locally)
python plm.py file checkin --file "BracketBase_Part" --note "Completed design"
# Output: ✓ Version v002 created (In-Work)

# Freeze version (when ready to release)
python plm.py version freeze --file "BracketBase_Part" --version 2
# Output: ✓ Version v002 frozen (Released/Read-Only)

# List versions
python plm.py version list --file "BracketBase_Part"
# Output:
#   v001 (In-Work) - john - 2026-01-01
#   v002 (Released) - john - 2026-01-02
#   v003 (In-Work) - sarah - 2026-01-03

# Check locks
python plm.py lock list
# Output: PLM-PAR-001 locked by john (expires 10:30 AM)

# Release lock manually
python plm.py lock release --file "BracketBase_Part"
# Output: ✓ Lock released
```

---

## 12. SolidWorks Add-in UI Buttons

```
Toolbar Layout:
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Acquire  │   Save   │  Create  │  Freeze  │ Release  │
│  Lock    │  (SWKS)  │ Version  │ Version  │   Lock   │
│          │          │          │          │          │
│ Disables │ Normal   │ Copies   │ Locks    │ Unlocks  │
│ if have  │ SWKS save│ to vault │ in vault │ file     │
│ lock     │          │ as v002  │ read-only│          │
└──────────┴──────────┴──────────┴──────────┴──────────┘

Status Bar:
┌──────────────────────────────────────────────────────┐
│ Status: Locked by john (expires 2:30 PM)             │
│ Version: v002 (In-Work) - Ready to freeze            │
└──────────────────────────────────────────────────────┘
```

---

## 13. Key Benefits

✅ **No Version Bloat** - Only meaningful versions created
✅ **User Control** - Versions created when user decides
✅ **Clear Governance** - In-Work vs Released is explicit
✅ **Lock Safety** - Prevents concurrent edits with timeout
✅ **Read-Only Enforcement** - Frozen versions cannot be modified
✅ **Simple Workflow** - Save locally, create version when ready, freeze when done
✅ **Easy Rollback** - Old versions always available
✅ **Auto-Cleanup** - Expired locks automatically deleted

---

## 14. Comparison: Old vs New

| Feature | Old Model | New Model (Correct) |
|---------|-----------|-------------------|
| Trigger for version | Every save | User explicit action |
| Versions per file | Many (100s) | Few (3-10) |
| Local edits | Not supported | Full freedom |
| Read-only enforcement | Automatic | User-triggered freeze |
| Lock behavior | Auto on save | Manual acquire/release |
| User experience | Confusing (too many versions) | Clear (versions = milestones) |

---

## 15. Migration from Old Model

If you have existing code using "each save = version":
1. Add "Create Version" button instead
2. Add "Freeze Version" button instead of auto-freeze
3. Change save handler to NOT create versions
4. Add lock acquire/release buttons
5. Update documentation with new workflow

**No database changes needed** - same schema works for both models.
