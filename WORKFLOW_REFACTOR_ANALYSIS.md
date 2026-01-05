# PLM Workflow Refactoring Analysis

## 🎯 Objective
Restructure PLM workflow to cleanly support: **Working → Freeze → Rework → Release** (for individual files) and **Assembly Release** (for assemblies) without ambiguity or data corruption.

---

## 📊 Current Implementation vs New Workflow

### Current Problems (What Breaks Today)

| Issue | Current Behavior | New Requirement | Impact |
|-------|------------------|-----------------|--------|
| **No Freeze State** | `create_version()` just increments version_number | Must lock working copy, make v0XX immutable | Assembly doesn't know if file is locked |
| **File Structure Confusion** | Creates `v001/`, `v002/` but also has `working/` | Clear: `Working/` + `Parts/PartName/v001/` hierarchy | GUI shows both, unclear which is editable |
| **No "Rework" Concept** | If you want to edit after creating v001, you just edit v001 | Must copy v001 back to Working, unlock | Files are immutable - can't edit |
| **Release ≠ Version** | `promote_version()` exists but only updates `lifecycle_state` field | Release is separate from Freeze, applies to existing version | Assembly can't reference specific released version |
| **Metadata Inconsistency** | No `part_meta.json` in file structure, metadata only in DB | Must have `part_meta.json` with `latest_version`, `released_version`, `state` | Part history unclear on disk |
| **Assembly References** | `assembly_relationships` stores version_number, ambiguous which folder | Must store full path to frozen version (e.g., `Parts/PartName/v001/`) | Assemblies can't guarantee reference to correct version |
| **Lock State Wrong Place** | Lock is on `files` table, not on version | Working copy is locked by Freeze; frozen versions are always locked | GUI can't tell if version is frozen |
| **Auto-Create on Save** | No mechanism (C# add-in copies to working/) | Should auto-update working/, NOT create new version | Working/ should be mutable playground |
| **Metadata Fields Missing** | Only `lifecycle_state` in DB | Need `latest_version`, `released_version`, `state` in file table or JSON | Can't quickly find released version |

---

## 🔧 Minimal Refactoring Plan

### Phase 1: Folder Structure (No DB Changes Required)

**Current Structure:**
```
Project/
├── FileName/
│   ├── working/
│   ├── v001/
│   └── v002/
```

**New Structure (RESTRUCTURE PATHS ONLY):**
```
Project/
├── Working/
│   ├── Parts/
│   │   ├── Bracket.SLDPRT
│   │   └── Housing.SLDPRT
│   ├── Assemblies/
│   │   └── Assembly1.SLDASM
│   └── Drawings/
│
├── Parts/
│   ├── Bracket/
│   │   ├── v001/
│   │   │   ├── Bracket.SLDPRT
│   │   │   └── part_meta.json
│   │   ├── v002/
│   │   │   ├── Bracket.SLDPRT
│   │   │   └── part_meta.json
│   │   └── part_meta.json  [latest, released]
│   └── Housing/
│       └── v001/
│
├── Assemblies/
│   ├── Assembly1/
│   │   ├── v001/
│   │   │   ├── Assembly1.SLDASM
│   │   │   └── assembly_meta.json
│   │   └── assembly_meta.json
```

**Migration Task:** Update `create_file()` to write to `Working/Parts/` and `Parts/PartName/v001/`

---

### Phase 2: Add Metadata JSON (Minimal DB Extension)

**Add field to `files` table:**
```sql
ALTER TABLE files ADD COLUMN metadata_file_path TEXT;
```

**Create `part_meta.json` in each part folder:**
```json
{
  "latest_version": "v002",
  "released_version": "v001",
  "state": "Working"
}
```

**File states (NEW):**
- `"Working"` → editable, no freeze yet
- `"Frozen"` → immutable snapshot created, working copy locked
- `"Released"` → approved frozen version, referenced by assemblies

**Update `promote_version()` logic:**
- `Release` operation: update `metadata_file_path` to point released_version
- Update `files.lifecycle_state` only on Release, NOT on Freeze

---

### Phase 3: Split Version Creation into Freeze + Release (DB Logic)

**Current Method:** `create_version()` = increment number + log entry

**New Methods:**

#### `freeze_file(file_id, user, note)`
- ✅ Copies `Working/Parts/PartName/*` → `Parts/PartName/vNNN/`
- ✅ Creates `part_meta.json` in `Parts/PartName/vNNN/`
- ✅ Sets version `lifecycle_state = "Frozen"`
- ✅ Locks working copy (set `files.locked_by = user`)
- ✅ Increments `latest_version` in `part_meta.json`
- ✅ Creates audit log entry
- ❌ Does NOT set `released_version` (that's Release's job)

#### `rework_file(file_id, user, note)`
- ✅ Copies `Parts/PartName/vNNN/*` → `Working/Parts/PartName/`
- ✅ Unlocks working copy (clear `files.locked_by`)
- ✅ Updates `part_meta.json: state = "Working"`
- ❌ Does NOT delete or modify old versions

#### `release_file(file_id, version_number, user, note)`
- ✅ Updates `part_meta.json: released_version = vNNN`
- ✅ Sets version `lifecycle_state = "Released"`
- ✅ Updates `files.lifecycle_state = "Released"`
- ✅ Creates transition log entry
- ❌ Does NOT create new version, copy files, or change working copy

#### `release_assembly(file_id, version_number, user, note)`
- ✅ Rewrite assembly references: `Working/` → `Parts/PartName/vReleased/`
- ✅ Copy assembly to `Assemblies/AssemblyName/vNNN/`
- ✅ Update `assembly_meta.json`
- ✅ Validate all referenced parts are Released
- ✅ Create audit entry
- ⚠️ Complex - must handle references

---

### Phase 4: Update C# Add-In (File Save Behavior)

**Current:** On SolidWorks save, copies file to `working/` folder

**New:** 
- Copy file to `Working/Parts/PartName/` (not `working/`)
- Update `part_meta.json: state = "Working"`
- Do NOT create version

**No changes to event handlers, just path updates**

---

### Phase 5: Update Python GUI

#### `create_file()` method
- Create `Working/Parts/PartName/` folder (NOT old `v001/` structure)
- Create initial `part_meta.json` with `latest_version = "v000"` (no versions yet)
- Create empty metadata record in DB

#### `create_version()` method (RENAME to `freeze_file()`)
- Call `db.freeze_file(file_id, user, note)` instead of `create_version()`
- Update button label: "Create Version" → "Freeze Version"

#### New `rework_file()` method
- Call `db.rework_file(file_id, user, note)`
- Button: "Rework" (only enabled if file is Frozen)

#### New `release_file()` method
- Show dialog: "Select version to release" (from list of Frozen versions)
- Call `db.release_file(file_id, version_number, user, note)`
- Button: "Release" (only enabled if file has Frozen versions)

#### Versions tab (RESTRUCTURE)
- Show list of Frozen + Released versions only
- Show `part_meta.json` fields: latest, released, state
- Color code: Working (green), Frozen (yellow), Released (blue)
- Disable editing on Released versions

---

## 📋 Data Migration Strategy

### If Database Exists:
1. Run migration script to add `metadata_file_path` column
2. Scan all files on disk
3. Generate `part_meta.json` for each file folder with actual versions
4. Populate `metadata_file_path` in DB pointing to file's meta JSON
5. Backfill `state` field based on folder structure

### If Starting Fresh (Recommended):
- Delete old `db.sqlite`
- Run `SETUP.py` with NEW schema
- Old `v001/`, `v002/` folders can remain as historical archive

---

## ✅ Validation Checklist

After refactor, verify:

- [ ] File created → `Working/Parts/PartName/` exists, empty
- [ ] part_meta.json created with `state: "Working"`
- [ ] Freeze → `Parts/PartName/v001/` created, working copy locked
- [ ] part_meta.json updated: `latest_version: "v001"`, `state: "Frozen"`
- [ ] Rework v001 → `Working/Parts/PartName/` populated, locked_by cleared
- [ ] Can freeze again → `Parts/PartName/v002/` created
- [ ] Release v001 → `released_version: "v001"` in part_meta.json
- [ ] Assembly references v001 correctly: `Parts/Bracket/v001/Bracket.SLDPRT`
- [ ] Assembly Release fails if parts are not Released
- [ ] No "unfreeze" option visible in GUI
- [ ] No version created on save from SolidWorks

---

## 📝 Backward Compatibility

**Current projects with old folder structure:**
- Can coexist alongside new structure
- Old versioning still works for reading
- New files use new structure only
- Migration script can convert old to new incrementally

---

## 🎯 Implementation Priority

1. **CRITICAL**: Folder structure change (Phase 1) - no DB schema change
2. **CRITICAL**: Add metadata JSON (Phase 2) - minimal schema addition
3. **HIGH**: Split freeze/release logic (Phase 3) - new DB methods
4. **HIGH**: Update GUI buttons and labels (Phase 5) - user-facing
5. **MEDIUM**: Update C# add-in paths (Phase 4) - automatic sync
6. **LOW**: Assembly release validation (Phase 3 extended) - complex logic

---

## 🔍 Files to Modify

| File | Change | Complexity |
|------|--------|------------|
| `database/db.py` | Add `freeze_file()`, `rework_file()`, `release_file()`, `release_assembly()` | High |
| `plm_gui.py` | Rename `create_version()` → `freeze_file()`, add Rework/Release buttons | Medium |
| `PLMAddInMain.cs` | Update paths: `working/` → `Working/Parts/PartName/` | Low |
| `SETUP.py` | Create new folder structure on init | Low |
| `DATABASE_SCHEMA.md` | Document new state transitions and metadata fields | Low |

---

## 🚀 Next Steps

1. **Run this analysis with user**
2. **Confirm structure change is acceptable**
3. **Create migration script for existing DB**
4. **Implement Phase 1 (folder structure)**
5. **Test file creation in new structure**
6. **Implement Phase 2-3 (freeze/release logic)**
7. **Update GUI (Phase 5)**
8. **Test complete workflow**

