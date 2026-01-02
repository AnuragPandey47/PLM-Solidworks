# Versioning Model - Corrected (January 2, 2026)

## What Was Changed

**Previous (Wrong):**
- Each save → new version (v001, v002, v003...)
- Too many versions, versioning bloat
- Confusing for engineers
- Like saving "final_final_v2_FINAL.sldprt"

**Now (Correct):**
- Regular saves → NO new version (local updates only)
- Explicit "Create Version" button → creates v001, v002, v003
- Explicit "Freeze Version" button → locks version read-only
- Clean, intentional versioning
- Like professional PLM systems (SOLIDWORKS PDM, Vault, Perforce)

---

## User Workflow

### Step 1: Start Editing
```
Click "Acquire Lock" button
    └─ Prevents others from editing
    └─ Lock expires in 24 hours
```

### Step 2: Edit & Save Freely
```
Edit file in SolidWorks
    │
    ├─ Save (Ctrl+S) → updates local working file
    ├─ Save (Ctrl+S) → updates local working file
    ├─ Save (Ctrl+S) → updates local working file
    │
    └─ NO versions created yet (just saving locally)
```

### Step 3: Create Version (Explicit)
```
When ready, click "Create Version" button
    └─ Copies current working file to vault
    └─ Creates v001 (or v002, v003... if editing existing file)
    └─ Adds change note (optional): "Completed initial design"
    └─ Version enters "In-Work" state
    └─ User keeps lock, can continue editing
```

### Step 4: Freeze Version (Lock In)
```
When ready to finalize, click "Freeze Version" button
    └─ Marks version as "Released" (read-only)
    └─ Version becomes immutable
    └─ Lock automatically released
    └─ Others can now open version but cannot edit
```

### Step 5: Next Iteration
```
Next person clicks "Acquire Lock"
    └─ Can create v002 from v001
    └─ Repeat steps 2-4
```

---

## Database Changes

Added new method to `database/db.py`:

```python
def freeze_version(self, file_id: int, version_number: int, user: str) -> bool:
    """Freeze version (make read-only) and release lock
    
    Actions:
    1. Check lock ownership (only lock holder can freeze)
    2. Update version state to 'Released'
    3. Log freeze action
    4. Release lock (auto-cleanup)
    
    Returns: True if successful
    """
```

---

## Button Changes Needed in Add-in

**SolidWorks Toolbar Buttons:**

| Button | Action | When to Use |
|--------|--------|-------------|
| **Acquire Lock** | Prevent others from editing | Start of work session |
| **Create Version** | Copy working file to vault as new version | After iterations, before review |
| **Freeze Version** | Lock in version as read-only | When design finalized |
| **Release Lock** | Manually release (auto-happens at freeze) | If changed mind |

---

## CLI Commands

```bash
# Acquire lock
python plm.py lock acquire --file "BracketBase_Part"

# Create version (after local edits)
python plm.py file checkin --file "BracketBase_Part" --note "Initial design complete"

# Freeze version (lock it in)
python plm.py version freeze --file "BracketBase_Part" --version 2

# Check status
python plm.py file status --file "BracketBase_Part"
# Output: v002 (Released) - frozen by john, you can create v003
```

---

## Example Real Workflow

**Day 1, 10:00 AM - Engineer John starts design**
```
1. Click "Acquire Lock"
   ✓ Lock acquired (expires 10:00 AM tomorrow)

2. Create bracket design in SolidWorks
   Save, save, save...

3. Click "Create Version"
   ✓ v001 created in vault (In-Work)

4. Continue editing locally
   More saves...

5. Click "Create Version" again
   ✓ v002 created in vault (In-Work)
```

**Day 2, 3:00 PM - John finalizes design**
```
6. Click "Freeze Version" (freeze v002)
   ✓ v002 locked (Released/Read-Only)
   ✓ Lock automatically released
   ✓ Message: "Version frozen. Others can now create v003"
```

**Day 2, 4:00 PM - Engineer Sarah continues work**
```
7. Click "Acquire Lock"
   ✓ Lock acquired (no one has it)

8. Open v002 as reference or copy
   Edit, make improvements

9. Click "Create Version"
   ✓ v003 created in vault (In-Work)

10. More edits, then freeze v003
    ✓ v003 locked (Released/Read-Only)
    ✓ Ready for manufacturing or next phase
```

---

## Benefits of This Model

✅ **No bloat** - Only meaningful versions (v001, v002, v003)
✅ **User control** - Engineer decides when to create/freeze
✅ **Clear intent** - Version = milestone, not every keystroke
✅ **Lock safety** - Only one person editing, others can read
✅ **Read-only enforcement** - Frozen versions can't be modified
✅ **Professional** - Like real PLM systems
✅ **Easy recovery** - Old versions always available

---

## Files Updated

1. **VERSIONING_ALGORITHM_V2.md** - New complete specification (replaces old)
2. **database/db.py** - Added `freeze_version()` method
3. **This file** - Quick reference guide

---

## Next Steps for Implementation

1. Update SolidWorks Add-in (C#) with new buttons
2. Update CLI tool (Python) with freeze command
3. Test workflow with new model
4. Update team documentation
5. Retire old VERSIONING_ALGORITHM.md (keep for reference only)

---

**Status:** ✅ Model corrected, database updated, ready for implementation
