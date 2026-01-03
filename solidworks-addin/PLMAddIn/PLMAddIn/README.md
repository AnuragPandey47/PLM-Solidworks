# PLM Add-In for SolidWorks

## Overview
This add-in automatically saves SolidWorks files to a "working" directory whenever they are saved, maintaining a mutable working copy for ongoing edits.

## Features
- **Automatic Save to Working Directory**: When you save a file in SolidWorks, it's automatically copied to a `working/` subdirectory in the same location
- **Metadata Tracking**: Updates file timestamps and logs author information
- **Debug Logging**: All operations are logged to the Debug output window
- **Version Control Ready**: The working directory holds the editable copy; version snapshots (v001/, v002/, etc.) are created separately through the PLM GUI

## Architecture
```
[Project Folder]
??? MyPart.SLDPRT          (Original save location)
??? working/
?   ??? MyPart.SLDPRT      (Mutable working copy - updated on every save)
??? v001/                   (Created manually via PLM GUI)
?   ??? MyPart.SLDPRT      (Immutable snapshot)
??? v002/                   (Created manually via PLM GUI)
    ??? MyPart.SLDPRT      (Immutable snapshot)
```

## Setup Instructions

### Prerequisites
- SolidWorks installed (tested with standard installation path)
- Visual Studio (for building)
- .NET Framework 4.8

### Building the Add-In
1. Open the solution in Visual Studio
2. Ensure SolidWorks Interop DLLs are referenced correctly:
   - `SolidWorks.Interop.sldworks.dll`
   - `SolidWorks.Interop.swconst.dll`
   - `SolidWorks.Interop.swpublished.dll`
   
   These are typically located at:
   `C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\`

3. Build the project in Release or Debug mode

### Manual Project Configuration
Since the .csproj file couldn't be edited automatically, you need to add these references manually:

1. Right-click on the project in Solution Explorer
2. Select "Add" > "Reference"
3. Click "Browse" and navigate to: `C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\`
4. Add these three DLLs:
   - `SolidWorks.Interop.sldworks.dll`
   - `SolidWorks.Interop.swconst.dll`
   - `SolidWorks.Interop.swpublished.dll`
5. For each reference, set `Embed Interop Types` to `False` in the Properties window
6. In Project Properties:
   - Go to "Build" tab
   - Check "Register for COM interop" (for both Debug and Release configurations)

### Registering the Add-In
1. Build the project (this will register it for COM if you enabled the setting above)
2. Alternatively, run from an Administrator command prompt:
   ```
   regasm /codebase PLMAddIn.dll
   ```

### Loading in SolidWorks
1. Open SolidWorks
2. Go to Tools > Add-Ins
3. Look for "PLM Add-In" in the list
4. Check both columns (startup and active) to enable it

## Usage
1. Open or create a SolidWorks file
2. Make your changes
3. Save the file (Ctrl+S or File > Save)
4. The add-in will automatically:
   - Create a `working/` directory if it doesn't exist
   - Copy the file to `working/MyFile.SLDPRT`
   - Log the operation to Debug output
   - Update metadata (author, timestamp, file size)

## Debug Output
To view the debug logs:
1. Run Visual Studio with SolidWorks
2. Go to Debug > Windows > Output
3. Look for messages prefixed with "PLM Add-In:"

Example output:
```
PLM Add-In: Successfully connected to SolidWorks
PLM Add-In: File saved to working directory
  File Name: Part1.SLDPRT
  File Path: C:\Projects\MyProject\Part1.SLDPRT
  Working Path: C:\Projects\MyProject\working\Part1.SLDPRT
  File Size: 524288 bytes
  Timestamp: 2026-01-15 14:30:45
  Author: JohnDoe
PLM Add-In: Metadata updated for Part1.SLDPRT
PLM Add-In: File successfully processed
```

## Version Control
This add-in does NOT create version snapshots automatically. Versions (v001/, v002/, etc.) are created manually through the PLM GUI using the "Create Version" button. This ensures that:
- Users have control over when immutable snapshots are created
- Only meaningful milestones become versions
- The working directory remains the single editable copy

## Technical Details
- **GUID**: `{12345678-1234-1234-1234-123456789ABC}`
- **Interface**: `ISwAddin`
- **Events Hooked**: 
  - `FileSaveNotify`
  - `FileSaveAsNotify2`
- **Target Framework**: .NET Framework 4.8
- **COM Visible**: Yes

## Error Handling
The add-in includes comprehensive error handling:
- All exceptions are caught and logged to Debug output
- File operations include existence checks
- Failed operations don't crash SolidWorks

## Troubleshooting
- **Add-in not appearing in SolidWorks**: Ensure COM registration was successful
- **No files being copied**: Check Debug output for error messages
- **Permission errors**: Run SolidWorks as Administrator or check folder permissions
- **SolidWorks references not found**: Update the DLL paths in the project references to match your SolidWorks installation

## License
Copyright © 2026
