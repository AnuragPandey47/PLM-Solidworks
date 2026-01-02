#!/usr/bin/env python3
"""
PLM System Initialization Script
Run this once to set up the entire PLM vault and database
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database.db import PLMDatabase


def setup_vault(vault_path: str) -> int:
    """Initialize PLM vault structure"""
    
    print("=" * 70)
    print("PLM SYSTEM INITIALIZATION")
    print("=" * 70)
    
    vault_path_obj = Path(vault_path)
    
    # 1. Create directory structure
    print("\n[1/4] Creating vault directory structure...")
    
    dirs = [
        vault_path_obj,
        vault_path_obj / "Projects",
        vault_path_obj / "Locks",
        vault_path_obj / "Logs",
        vault_path_obj / "Utils",
        vault_path_obj / "Utils" / "migration_scripts",
        vault_path_obj / "db_backup"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {d}")
    
    # 2. Create vault config
    print("\n[2/4] Creating vault configuration...")
    
    config = {
        "vault_version": "1.0",
        "vault_name": "PLM_VAULT",
        "vault_path": str(vault_path_obj),
        "created_date": datetime.utcnow().isoformat() + "Z",
        "owner": os.getenv("USERNAME"),
        "max_project_count": 100,
        "database": {
            "type": "sqlite",
            "file": "db.sqlite",
            "version": "3.45.0"
        },
        "backup": {
            "enabled": True,
            "frequency": "daily",
            "retention_days": 30
        },
        "lock_timeout_hours": 24,
        "enable_checksums": True,
        "enable_logging": True
    }
    
    config_path = vault_path_obj / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"  ✓ {config_path}")
    
    # 3. Initialize database
    print("\n[3/4] Initializing SQLite database...")
    
    db = PLMDatabase(str(vault_path_obj))
    print(f"  ✓ Database created: {vault_path_obj / 'db.sqlite'}")
    
    # 4. Verify setup
    print("\n[4/4] Verifying setup...")
    
    integrity = db.validate_vault_integrity()
    print(f"  ✓ Database integrity check:")
    print(f"    - Projects: {integrity['project_count']}")
    print(f"    - Files: {integrity['file_count']}")
    print(f"    - Versions: {integrity['version_count']}")
    
    # 5. Create sample project (optional)
    print("\n" + "=" * 70)
    response = input("Create sample project 'Demo'? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\nCreating sample project...")
        owner = os.getenv("USERNAME") or "Administrator"
        sample_proj = db.create_project(
            name="Demo",
            owner=owner,
            description="Sample project for testing"
        )
        
        # Create sample directories
        demo_path = Path(sample_proj["vault_path"])
        for subdir in ["CAD", "Drawings", "Excel", "Archive"]:
            (demo_path / subdir).mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Sample project created:")
        print(f"  PLM ID: {sample_proj['plm_id']}")
        print(f"  Location: {sample_proj['vault_path']}")
    
    print("\n" + "=" * 70)
    print("✓ PLM INITIALIZATION COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Copy PLM_VAULT to desired location (e.g., \\\\server\\PLM_VAULT)")
    print("2. Install SolidWorks Add-in (See: solidworks-addin/README.md)")
    print("3. Use CLI tool: python cli-tool/plm.py --help")
    print("4. Start using PLM in SolidWorks!")
    print("\nDocumentation:")
    print("- ARCHITECTURE.md: System design & concepts")
    print("- VAULT_STRUCTURE.md: Directory & file organization")
    print("- DATABASE_SCHEMA.md: Database schema & queries")
    
    return 0


if __name__ == "__main__":
    vault_path = r"e:\PLM_VAULT"
    
    # Check if vault already exists
    if Path(vault_path).exists() and (Path(vault_path) / "db.sqlite").exists():
        print(f"Vault already exists at {vault_path}")
        response = input("Reinitialize? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(0)
    
    try:
        exit_code = setup_vault(vault_path)
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
