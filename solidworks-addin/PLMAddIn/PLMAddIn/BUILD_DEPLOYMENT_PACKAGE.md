# Building a Deployment Package

## For Developers - Creating the Deployment Package

After building your project successfully, follow these steps to create a deployment package:

### Step 1: Build in Release Mode
```
1. In Visual Studio, set Configuration to "Release"
2. Build the solution (F6)
3. Find the output in: bin\Release\
```

### Step 2: Create Deployment Folder Structure
```
?? PLMAddIn_v1.0_Deployment/
??? ?? PLMAddIn.dll (from bin\Release\)
??? ?? RegisterAddIn.bat
??? ?? UnregisterAddIn.bat
??? ?? RegisterAddIn.reg (optional)
??? ?? UnregisterAddIn.reg (optional)
??? ?? DEPLOYMENT.md (renamed to README.txt)
??? ?? LICENSE.txt (if applicable)
```

### Step 3: Copy Required Files

**Essential Files:**
- `bin\Release\PLMAddIn.dll` ? Main add-in assembly
- `RegisterAddIn.bat` ? Registration script
- `UnregisterAddIn.bat` ? Uninstallation script
- `DEPLOYMENT.md` ? User instructions (rename to README.txt)

**Optional Files:**
- `RegisterAddIn.reg` ? Registry entries (manual import)
- `UnregisterAddIn.reg` ? Registry cleanup

### Step 4: Test the Package

Before distributing:
1. Copy the deployment folder to a test machine
2. Run RegisterAddIn.bat as Administrator
3. Open SolidWorks and verify add-in appears
4. Enable it and test functionality
5. Run UnregisterAddIn.bat to clean up

### Step 5: Distribute

**Methods:**
- **ZIP File**: Compress and share via email/download
- **Network Share**: Place on company network
- **Installer**: Create with Inno Setup or WiX (advanced)

## Version Management

When releasing updates:
1. Increment version in `AssemblyInfo.cs`
2. Build new release
3. Name package: `PLMAddIn_v1.1_Deployment.zip`
4. Include changelog

## Important Notes

### Registry Keys Used
```
HKEY_LOCAL_MACHINE\SOFTWARE\SolidWorks\Addins\{12345678-1234-1234-1234-123456789ABC}
HKEY_CURRENT_USER\Software\SolidWorks\AddInsStartup\{12345678-1234-1234-1234-123456789ABC}
```

### Installation Location
Recommended: `C:\Program Files\PLMAddIn\`
- Requires admin rights
- Accessible to all users
- Standard location for programs

Alternative: `C:\Users\{Username}\AppData\Local\PLMAddIn\`
- No admin rights needed
- Per-user installation
- Less standard

### .NET Framework Dependency
The target machine MUST have .NET Framework 4.8 installed.
- Usually pre-installed on Windows 10/11
- Can be downloaded from Microsoft

## Advanced: Creating an MSI Installer

For professional deployment, consider using **Inno Setup**:

1. Download Inno Setup (free)
2. Create a script:
```iss
[Setup]
AppName=PLM Add-In for SolidWorks
AppVersion=1.0
DefaultDirName={pf}\PLMAddIn
OutputDir=installer_output
OutputBaseFilename=PLMAddIn_Setup

[Files]
Source: "bin\Release\PLMAddIn.dll"; DestDir: "{app}"

[Run]
Filename: "{sys}\regasm.exe"; Parameters: "/codebase ""{app}\PLMAddIn.dll"""; Flags: runhidden

[UninstallRun]
Filename: "{sys}\regasm.exe"; Parameters: "/unregister ""{app}\PLMAddIn.dll"""; Flags: runhidden
```

3. Compile to create `PLMAddIn_Setup.exe`
4. Distribute single installer file

## Checklist Before Distribution

- [ ] Tested on clean Windows machine
- [ ] Version number updated
- [ ] README/instructions included
- [ ] All required DLLs included
- [ ] Registration works without errors
- [ ] Add-in appears in SolidWorks
- [ ] Save functionality works
- [ ] Uninstall works cleanly

## Security Considerations

- Code sign your DLL for trust
- Use official GUID (not the example one)
- Test on multiple SolidWorks versions
- Include antivirus scan results

## Support Plan

Consider creating:
- Installation video/GIF
- FAQ document
- Support email/contact
- Update notification system
