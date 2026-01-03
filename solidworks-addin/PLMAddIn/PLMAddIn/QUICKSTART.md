# ?? Quick Start Guide

## Prerequisites
- ? Visual Studio installed
- ? SolidWorks installed
- ? .NET Framework 4.8

## Setup in 5 Steps

### 1?? Add SolidWorks References
In Visual Studio:
1. Right-click **References** ? **Add Reference**
2. Browse to: `C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\`
3. Add these 3 DLLs:
   - `SolidWorks.Interop.sldworks.dll`
   - `SolidWorks.Interop.swconst.dll`
   - `SolidWorks.Interop.swpublished.dll`
4. For each reference, set:
   - **Embed Interop Types** = `False`
   - **Copy Local** = `False`

### 2?? Enable COM Registration
1. Right-click project ? **Properties**
2. **Build** tab
3. Check ? **"Register for COM interop"**

### 3?? Build the Project
Press **F6** or **Build > Build Solution**

### 4?? Register with SolidWorks
**Option A: Automatic**
- If build succeeded, registration is automatic
- Restart SolidWorks

**Option B: Manual**
- Run `RegisterAddIn.bat` as Administrator

### 5?? Enable in SolidWorks
1. Open SolidWorks
2. **Tools > Add-Ins**
3. Find **"PLM Add-In"**
4. Check both boxes (startup & active)
5. Click **OK**

---

## ? Test It Works

1. Open/create a part in SolidWorks
2. Make a change
3. Save (**Ctrl+S**)
4. Check that a **`working/`** folder was created
5. Verify your file is inside **`working/`**

---

## ?? View Debug Logs

**In Visual Studio:**
- **Debug > Windows > Output** (Ctrl+Alt+O)
- Look for "PLM Add-In:" messages

**Alternative: DebugView**
- Download from Microsoft Sysinternals
- Shows debug output without Visual Studio

---

## ?? What to Expect

### When You Save:
```
?? C:\Projects\MyProject\
??? ?? Part1.SLDPRT          (your save location)
??? ?? working/
    ??? ?? Part1.SLDPRT      (auto-copied here!)
```

### Debug Output:
```
PLM Add-In: File saved to working directory
  File Name: Part1.SLDPRT
  File Path: C:\Projects\MyProject\Part1.SLDPRT
  Working Path: C:\Projects\MyProject\working\Part1.SLDPRT
  File Size: 524288 bytes
  Timestamp: 2026-01-15 14:30:45
  Author: YourUsername
PLM Add-In: File successfully processed
```

---

## ?? Troubleshooting

| Problem | Solution |
|---------|----------|
| References not found | Check SolidWorks install path |
| Add-in not in list | Run `RegisterAddIn.bat` as Admin |
| Files not copied | Check Debug output for errors |
| Permission denied | Run SolidWorks as Administrator |
| Build errors | Set Platform to x64 or Any CPU |

---

## ?? More Information

- **Detailed setup**: See `SETUP.md`
- **Full documentation**: See `README.md`
- **Implementation details**: See `IMPLEMENTATION_SUMMARY.md`

---

## ?? You're Done!

The add-in now automatically saves your files to `working/` every time you save in SolidWorks.

**Next**: Build the PLM GUI to create version snapshots (v001/, v002/, etc.)
