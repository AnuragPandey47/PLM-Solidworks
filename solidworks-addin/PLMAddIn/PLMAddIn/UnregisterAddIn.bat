@echo off
echo ================================================
echo PLM Add-In Unregistration Script
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

echo Unregistering PLM Add-In from COM...
echo.

REM Set the path to the DLL (adjust if needed)
set DLL_PATH=%~dp0bin\Debug\PLMAddIn.dll

if not exist "%DLL_PATH%" (
    set DLL_PATH=%~dp0bin\Release\PLMAddIn.dll
)

if not exist "%DLL_PATH%" (
    echo WARNING: Cannot find PLMAddIn.dll
    echo Will attempt to unregister anyway...
    echo.
)

if exist "%DLL_PATH%" (
    echo Found DLL at: %DLL_PATH%
    echo.
    REM Unregister with RegAsm
    "%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\RegAsm.exe" /unregister "%DLL_PATH%"
)

echo.
echo ================================================
echo PLM Add-In unregistration complete
echo ================================================
echo.

pause
