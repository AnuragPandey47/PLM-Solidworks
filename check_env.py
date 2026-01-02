"""
PLM System Quick Start & Requirements
Test & verify environment before running SETUP.py
"""

import sys
import os
from pathlib import Path

def check_environment():
    """Verify system is ready for PLM"""
    
    print("=" * 70)
    print("PLM ENVIRONMENT VERIFICATION")
    print("=" * 70)
    
    issues = []
    warnings = []
    
    # 1. Check Python version
    print(f"\n[1/5] Python version...")
    py_version = sys.version_info
    if py_version.major >= 3 and py_version.minor >= 9:
        print(f"  ✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        issues.append(f"Python 3.9+ required (found {py_version.major}.{py_version.minor})")
    
    # 2. Check SQLite
    print(f"\n[2/5] SQLite availability...")
    try:
        import sqlite3
        conn = sqlite3.connect(':memory:')
        version = sqlite3.sqlite_version
        print(f"  ✓ SQLite {version}")
        conn.close()
    except Exception as e:
        issues.append(f"SQLite error: {e}")
    
    # 3. Check vault path
    print(f"\n[3/5] Vault path...")
    vault_path = Path(r"e:\PLM_VAULT")
    if vault_path.drive:
        print(f"  ✓ Vault path: {vault_path}")
        
        # Check if path exists
        if vault_path.exists():
            if (vault_path / "db.sqlite").exists():
                warnings.append("Vault already exists at e:\\PLM_VAULT")
            else:
                print(f"    (Directory exists but not initialized)")
        else:
            print(f"    (Will be created by SETUP.py)")
    else:
        issues.append("Invalid vault path: e:\\PLM_VAULT")
    
    # 4. Check disk space
    print(f"\n[4/5] Disk space...")
    try:
        import shutil
        stat = shutil.disk_usage(vault_path.drive)
        free_gb = stat.free / (1024 ** 3)
        print(f"  ✓ Free space: {free_gb:.1f} GB")
        
        if free_gb < 1:
            issues.append(f"Not enough disk space (need 1+ GB, have {free_gb:.1f} GB)")
        elif free_gb < 5:
            warnings.append(f"Low disk space ({free_gb:.1f} GB)")
    except Exception as e:
        warnings.append(f"Could not check disk space: {e}")
    
    # 5. Check Windows version
    print(f"\n[5/5] Windows version...")
    try:
        import platform
        os_name = platform.system()
        win_version = platform.win32_ver()[1]  # e.g., '10'
        
        if os_name == "Windows":
            print(f"  ✓ Windows {win_version}")
            if float(win_version) < 10:
                warnings.append("Windows 10+ recommended")
        else:
            issues.append(f"PLM requires Windows (detected {os_name})")
    except Exception as e:
        warnings.append(f"Could not detect Windows version: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    
    if issues:
        print(f"\n❌ {len(issues)} CRITICAL ISSUE(S):\n")
        for issue in issues:
            print(f"  • {issue}")
        return False
    
    if warnings:
        print(f"\n⚠️ {len(warnings)} WARNING(S):\n")
        for warning in warnings:
            print(f"  • {warning}")
    
    print("\n✅ ENVIRONMENT OK - Ready to run SETUP.py\n")
    return True


def show_help():
    """Show quick help"""
    print("""
PLM QUICK START
═════════════════════════════════════════════════════════════════════

1. Verify Environment:
   python check_env.py

2. Initialize Vault:
   python SETUP.py

3. Test CLI Tool:
   python cli-tool\\plm.py vault status

4. Build & Install Add-in:
   See solidworks-addin\\README.md

5. Start Using PLM:
   Open SolidWorks and start saving files!

═════════════════════════════════════════════════════════════════════

Documentation:
  README.md                    - User guide & overview
  ARCHITECTURE.md             - System design & concepts  
  DATABASE_SCHEMA.md          - Database structure
  VERSIONING_ALGORITHM.md     - Versioning rules
  IMPLEMENTATION_SUMMARY.md   - Project status & roadmap

═════════════════════════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    check_environment()
    show_help()
