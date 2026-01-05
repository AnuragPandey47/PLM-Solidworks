# PLM SolidWorks Macros

These VB macros provide the user interface for PLM workflow operations in SolidWorks.

## Macro Files

### 1. FreezeVersion.swp
**Purpose:** Freeze current working file as a new version  
**Usage:**
1. Open a part/assembly from `Projects/ProjectName/Working/Parts/`
2. Make changes and save
3. Run macro: Tools → Macros → Run FreezeVersion
4. Result: Creates `Parts/FileName/vNNN/` with frozen snapshot

**C# Add-in Call:**
```vb
swAddin.FreezeCurrentVersion()
```

### 2. ReleaseVersion.swp
**Purpose:** Release (approve) a frozen version  
**Usage:**
1. Open a frozen part/assembly
2. Run macro: Tools → Macros → Run ReleaseVersion
3. Result: Marks version as released and locks it

**C# Add-in Call:**
```vb
swAddin.ReleaseCurrentVersion()
```

### 3. ReworkVersion.swp
**Purpose:** Restore a frozen version for editing  
**Usage:**
1. Open any part/assembly from the project
2. Run macro: Tools → Macros → Run ReworkVersion
3. Enter version number: `v001`
4. Result: Restores version to `Working/Parts/` for editing

**C# Add-in Call:**
```vb
swAddin.ReworkFromVersion("v001")
```

## Installation

### Step 1: Copy Macro Files
```
Source: d:\Anurag\PLM-Solidworks\macros\
Destination: C:\Users\<YourUsername>\AppData\Roaming\SolidWorks\macros\
```

### Step 2: Enable Macro Security (if needed)
SolidWorks → Tools → Options → Security → Macros → Enable unsigned macros

### Step 3: Add Macro Buttons (Optional - User will do this)
1. SolidWorks → Tools → Customize
2. Commands tab → Create/Assign button to macro
3. Drag button to toolbar

## Workflow Example

```
1. GUI: Create project "MotorAssembly"
2. GUI: Create file "Bracket.SLDPRT"
3. SolidWorks: Open Bracket.SLDPRT
4. SolidWorks: Edit, save (Ctrl+S)
   → Add-in auto-copies to Working/Parts/
5. SolidWorks: Run FreezeVersion macro
   → Creates Parts/Bracket/v001/ snapshot
6. SolidWorks: Continue editing, save again
7. SolidWorks: Run FreezeVersion macro
   → Creates Parts/Bracket/v002/
8. SolidWorks: Run ReleaseVersion macro
   → Marks v002 as released
9. SolidWorks: Run ReworkVersion macro, enter "v001"
   → Restores v001 to Working/ for reworking
```

## Dependencies

- **C# Add-in:** PLMAddIn.PLMAddInMain must be registered with SolidWorks
- **SolidWorks:** 2021 or later
- **VB Script:** Enabled in SolidWorks

## Troubleshooting

**"Error: PLM Add-in not loaded"**
- Solution: Check C# add-in is installed and registered
- Path: `D:\Anurag\PLM-Solidworks\solidworks-addin\PLMAddIn\bin\x64\Debug\PLMAddIn.dll`

**"Error: No active document"**
- Solution: Open a part/assembly first before running macro

**"Error: Failed to freeze version"**
- Solution: Check file is from `Working/Parts/` folder
- Verify project path is set correctly

## Future Enhancement (Phase 3)

Instead of using macros, user will be able to:
- Click toolbar buttons directly
- Access from right-click context menu
- See status indicator of file state (Working/Frozen/Released)
