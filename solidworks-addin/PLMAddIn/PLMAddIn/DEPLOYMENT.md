# PLM Add-In Deployment Instructions

## For System Administrators

### One-Time Installation Per Computer

1. **Copy the Deployment Folder** to the target computer
   - Recommended location: `C:\Program Files\PLMAddIn\`

2. **Register the Add-In**
   - Right-click `RegisterAddIn.bat`
   - Select "Run as Administrator"
   - Wait for "SUCCESS" message

3. **Verify Registration**
   - Open SolidWorks
   - Go to Tools > Add-Ins
   - You should see "PLM Add-In" in the list

### For Each User (One-Time Setup)

1. **Open SolidWorks**
2. **Go to Tools > Add-Ins**
3. **Find "PLM Add-In"** in the list
4. **Check BOTH boxes**:
   - ? Left column = Load on startup (automatic)
   - ? Right column = Currently active
5. **Click OK**

That's it! The add-in will now automatically:
- Load every time SolidWorks starts
- Copy files to `working/` folder on save

## Uninstallation

To remove the add-in:
1. Right-click `UnregisterAddIn.bat`
2. Select "Run as Administrator"
3. Delete the installation folder

## Troubleshooting

### Add-in doesn't appear in list
- Run RegisterAddIn.bat as Administrator
- Restart SolidWorks

### Files not being copied
- Check Debug output in Visual Studio
- Or download DebugView from Microsoft Sysinternals

### Permission errors
- Run SolidWorks as Administrator
- Or grant write permissions to working directory

## System Requirements

- Windows 7 or later
- SolidWorks 2018 or later
- .NET Framework 4.8
- Administrator rights for installation

## Support

For issues or questions, contact your system administrator.
