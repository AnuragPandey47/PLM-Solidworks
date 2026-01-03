# Quick Setup Guide - PLM SolidWorks Add-In

## Step 1: Add SolidWorks References

You need to manually add the SolidWorks Interop references to the project:

1. **Open Visual Studio** and load the PLMAddIn project

2. **Add References**:
   - Right-click on "References" in Solution Explorer
   - Select "Add Reference..."
   - Click "Browse..." button at the bottom
   - Navigate to: `C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\`
   - Add these three files:
     * `SolidWorks.Interop.sldworks.dll`
     * `SolidWorks.Interop.swconst.dll`
     * `SolidWorks.Interop.swpublished.dll`
   - Click "Add" then "OK"

3. **Configure References**:
   - In Solution Explorer, expand "References"
   - For EACH of the three SolidWorks references:
     * Click on the reference
     * In the Properties window (F4), set:
       - `Embed Interop Types` = **False**
       - `Copy Local` = **False**

## Step 2: Enable COM Registration

1. Right-click the project (PLMAddIn) in Solution Explorer
2. Select "Properties"
3. Go to the "Build" tab
4. Check ? **"Register for COM interop"**
5. Save and close

## Step 3: Build the Project

1. Set build configuration to "Debug" or "Release"
2. Build the solution (F6 or Build > Build Solution)
3. Verify no compilation errors

## Step 4: Register and Load in SolidWorks

### Option A: Automatic (if COM registration worked)
1. Close SolidWorks if it's running
2. Open SolidWorks
3. Go to **Tools > Add-Ins...**
4. Find "PLM Add-In" in the list
5. Check both boxes (left column for startup, right for currently loaded)
6. Click OK

### Option B: Manual Registration
If the add-in doesn't appear:

1. Open **Command Prompt as Administrator**
2. Navigate to your build output folder:
   ```
   cd "D:\Anurag\PLM-Solidworks\solidworks-addin\PLMAddIn\bin\Debug"
   ```
3. Register the DLL:
   ```
   regasm /codebase PLMAddIn.dll
   ```
4. Follow steps from Option A

## Step 5: Test the Add-In

1. Open SolidWorks
2. Create or open a part/assembly
3. Make a small change
4. Save the file (Ctrl+S)
5. Check that a `working/` folder was created in the same directory
6. Verify the file was copied to `working/`

## Viewing Debug Output

To see the add-in's log messages:

1. In Visual Studio: **Debug > Windows > Output** (or Ctrl+Alt+O)
2. Or use [DebugView](https://learn.microsoft.com/en-us/sysinternals/downloads/debugview) from Sysinternals
3. Look for messages starting with "PLM Add-In:"

## Troubleshooting

### "SolidWorks references not found"
- Verify SolidWorks is installed
- Check the path: `C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\`
- Your installation might be in a different location

### "Add-in doesn't appear in SolidWorks"
- Verify COM registration succeeded (check build output)
- Run Visual Studio as Administrator and rebuild
- Try manual registration (Option B above)

### "Files not being copied to working/"
- Check Debug output for error messages
- Verify you have write permissions in the directory
- Ensure the file was actually saved (not just preview)

### "Build errors about 'Platform target'"
- Project Properties > Build
- Change "Platform target" to "x64" if using 64-bit SolidWorks
- Or set to "Any CPU" with "Prefer 32-bit" unchecked

## What This Add-In Does

? Automatically copies saved files to `working/` subdirectory
? Logs file name, path, size, author, and timestamp
? Creates working directory if it doesn't exist
? Handles errors gracefully without crashing SolidWorks

? Does NOT create versions automatically (that's done through PLM GUI)
? Does NOT modify your original files
? Does NOT add UI elements to SolidWorks

## Next Steps

Once the add-in is working:
- Develop the PLM GUI for manual version creation
- The GUI will create v001/, v002/, etc. folders
- Each version folder will contain an immutable snapshot
- The `working/` folder always has the latest editable copy
