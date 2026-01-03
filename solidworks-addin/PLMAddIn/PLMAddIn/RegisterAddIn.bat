@echo off
echo ================================================
echo PLM Add-In Registration Script
echo ================================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges
    echo Please right-click and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo Registering PLM Add-In with COM...
echo.

REM Set the path to the DLL (adjust if needed)
set DLL_PATH=%~dp0bin\Debug\PLMAddIn.dll

if not exist "%DLL_PATH%" (
    set DLL_PATH=%~dp0bin\Release\PLMAddIn.dll
)

if not exist "%DLL_PATH%" (
    echo ERROR: Cannot find PLMAddIn.dll
    echo Expected location: %~dp0bin\Debug\PLMAddIn.dll
    echo                or: %~dp0bin\Release\PLMAddIn.dll
    echo.
    echo Please build the project first!
    echo.
    pause
    exit /b 1
)

echo Found DLL at: %DLL_PATH%
echo.

REM Register with RegAsm
"%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\RegAsm.exe" /codebase "%DLL_PATH%"

if %errorLevel% equ 0 (
    echo.
    echo ================================================
    echo SUCCESS: PLM Add-In registered successfully!
    echo ================================================
    echo.
    echo Next steps:
    echo 1. Start SolidWorks
    echo 2. Go to Tools ^> Add-Ins
    echo 3. Enable "PLM Add-In"
    echo.
) else (
    echo.
    echo ERROR: Registration failed!
    echo Please check that:
    echo - .NET Framework 4.8 is installed
    echo - The DLL was built successfully
    echo.
)

pause
