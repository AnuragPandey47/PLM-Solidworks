# PLM Vault Directory Structure

This document describes the recommended folder organization for PLM_VAULT.

## Structure Definition

```
PLM_VAULT/
│
├── README.md                                    # Vault documentation
├── config.json                                  # Vault-level configuration
├── db.sqlite                                    # SQLite metadata database
├── db_backup/                                   # Automated backups
│   └── db_20260115_1430.sqlite
│
├── Projects/
│   │
│   ├── ProjectA/
│   │   ├── metadata.json                        # Project info (owner, created, desc)
│   │   ├── .project_lock                        # Lock file during operations
│   │   │
│   │   ├── CAD/
│   │   │   │
│   │   │   ├── BracketBase_Part/
│   │   │   │   ├── metadata.json                # PLM ID, current version, lifecycle
│   │   │   │   ├── v001/
│   │   │   │   │   ├── BracketBase_Part.SLDPRT
│   │   │   │   │   ├── metadata.json            # Author, timestamp, properties
│   │   │   │   │   └── checksum.txt             # SHA256 for validation
│   │   │   │   │
│   │   │   │   ├── v002/
│   │   │   │   │   ├── BracketBase_Part.SLDPRT
│   │   │   │   │   ├── metadata.json
│   │   │   │   │   └── checksum.txt
│   │   │   │   │
│   │   │   │   ├── v003/
│   │   │   │   │   ├── BracketBase_Part.SLDPRT
│   │   │   │   │   ├── metadata.json            # (v003A - Released)
│   │   │   │   │   └── checksum.txt
│   │   │   │   │
│   │   │   │   └── .checkout_history           # Records who checked out when
│   │   │   │
│   │   │   ├── BracketCover_Part/
│   │   │   │   ├── metadata.json
│   │   │   │   ├── v001/
│   │   │   │   └── v002/
│   │   │   │
│   │   │   └── Bracket_Assembly/
│   │   │       ├── metadata.json
│   │   │       ├── v001/
│   │   │       │   ├── Bracket_Assembly.SLDASM
│   │   │       │   ├── metadata.json
│   │   │       │   ├── references.json          # Component tree (by PLM ID)
│   │   │       │   └── checksum.txt
│   │   │       │
│   │   │       └── v002/
│   │   │           ├── Bracket_Assembly.SLDASM
│   │   │           ├── metadata.json
│   │   │           ├── references.json
│   │   │           └── checksum.txt
│   │   │
│   │   ├── Drawings/
│   │   │   └── Bracket_Assembly_Drawing/
│   │   │       ├── metadata.json
│   │   │       └── v001/
│   │   │           ├── Bracket_Assembly_Drawing.SLDDRW
│   │   │           ├── metadata.json
│   │   │           └── checksum.txt
│   │   │
│   │   ├── Excel/                               # Optional: datasheets, BOM exports
│   │   │   └── Assembly_BOM/
│   │   │       ├── v001/
│   │   │       │   ├── BOM_v001.xlsx
│   │   │       │   └── metadata.json
│   │   │       └── v002/
│   │   │
│   │   └── Archive/                             # Deprecated files, old branches
│   │       └── OldBracketDesign_v1/
│   │           └── v001/
│   │
│   └── ProjectB/
│       ├── metadata.json
│       ├── CAD/
│       │   └── [similar structure]
│       │
│       └── Archive/
│
├── Locks/
│   ├── README.md                                # Lock file format documentation
│   ├── ProjectA_BracketBase_Part.lock
│   │   └── Content: {"locked_by": "john.smith", "timestamp": "2026-01-15T14:32:00Z", "session_id": "..."}
│   │
│   └── ProjectA_Bracket_Assembly.lock
│
├── Logs/
│   ├── access_log.json                          # All access events (append-only)
│   ├── version_transitions.json                 # Lifecycle changes
│   ├── error_log.json                           # Errors & warnings
│   └── audit_archive_20260101.json              # Monthly rollover
│
└── Utils/
    ├── migration_scripts/                       # Schema updates, vault repairs
    │   ├── 001_initial_schema.sql
    │   └── 002_add_assembly_table.sql
    │
    └── validate_vault.py                        # Integrity checks (checksums, orphans)
```

## File Specifications

### vault/config.json
```json
{
  "vault_version": "1.0",
  "vault_name": "PLM_VAULT",
  "vault_path": "e:\\PLM_VAULT",
  "created_date": "2026-01-01T00:00:00Z",
  "owner": "admin",
  "max_project_count": 100,
  "database": {
    "type": "sqlite",
    "file": "db.sqlite",
    "version": "3.45.0"
  },
  "backup": {
    "enabled": true,
    "frequency": "daily",
    "retention_days": 30
  },
  "lock_timeout_hours": 24,
  "enable_checksums": true,
  "enable_logging": true
}
```

### vault/Projects/{ProjectName}/metadata.json
```json
{
  "project_id": 1,
  "plm_id": "PLM-PRJ-001",
  "name": "ProjectA",
  "description": "Bracket assembly for XYZ system",
  "owner": "john.smith",
  "created_date": "2026-01-01T10:00:00Z",
  "modified_date": "2026-01-15T14:30:00Z",
  "vault_path": "e:\\PLM_VAULT\\Projects\\ProjectA",
  "team_members": ["john.smith", "jane.doe", "bob.jones"],
  "is_active": true,
  "standards": {
    "naming_convention": "PartName_Type",
    "revision_scheme": "A, B, C, ...",
    "file_types": ["SLDPRT", "SLDASM", "SLDDRW"]
  }
}
```

### vault/Projects/{ProjectName}/CAD/{PartName}/metadata.json
```json
{
  "file_id": 5,
  "plm_id": "PLM-PAR-001",
  "file_name": "BracketBase_Part",
  "file_type": "PART",
  "description": "Main bracket base component",
  "project_id": 1,
  "created_date": "2026-01-10T09:00:00Z",
  "modified_date": "2026-01-15T14:32:00Z",
  "current_version": 3,
  "lifecycle_state": "In-Work",
  "locked_by": null,
  "lock_timestamp": null,
  "vault_path": "e:\\PLM_VAULT\\Projects\\ProjectA\\CAD\\BracketBase_Part",
  "is_active": true,
  "version_count": 3,
  "latest_version_date": "2026-01-15T14:32:00Z"
}
```

### vault/Projects/{ProjectName}/CAD/{PartName}/vXXX/metadata.json
```json
{
  "version_id": 47,
  "file_id": 5,
  "version_number": 3,
  "revision_letter": "A",
  "author": "john.smith",
  "created_timestamp": "2026-01-15T14:32:00Z",
  "change_note": "Increased wall thickness from 2.0mm to 2.5mm per FEA",
  "lifecycle_state": "Released",
  "file_path": "e:\\PLM_VAULT\\Projects\\ProjectA\\CAD\\BracketBase_Part\\v003\\BracketBase_Part.SLDPRT",
  "file_size_bytes": 2847392,
  "checksum": "sha256:abc123def456...",
  "custom_properties": {
    "Material": "Aluminum 6061-T6",
    "Weight": "0.250 kg",
    "Heat_Treatment": "T6",
    "Configuration": "Default"
  },
  "solidworks_properties": {
    "title": "Bracket Base",
    "subject": "Component",
    "author": "john.smith",
    "keywords": "bracket, aluminum",
    "comments": "Production-ready design"
  },
  "is_locked": false
}
```

### vault/Projects/{ProjectName}/CAD/{AssemblyName}/vXXX/references.json
```json
{
  "assembly_plm_id": "PLM-ASM-001",
  "assembly_name": "Bracket_Assembly",
  "assembly_version": 2,
  "assembly_author": "john.smith",
  "created_date": "2026-01-12T11:00:00Z",
  "modified_date": "2026-01-15T14:32:00Z",
  "components": [
    {
      "instance_id": 1,
      "instance_name": "BracketBase_Part-1",
      "component_plm_id": "PLM-PAR-001",
      "component_version": 3,
      "component_revision": "A",
      "component_file_name": "BracketBase_Part.SLDPRT",
      "quantity": 1,
      "position_id": 1,
      "insertion_state": "Configured",
      "suppressed": false,
      "component_vault_path": "e:\\PLM_VAULT\\Projects\\ProjectA\\CAD\\BracketBase_Part\\v003\\BracketBase_Part.SLDPRT"
    },
    {
      "instance_id": 2,
      "instance_name": "BracketCover_Part-1",
      "component_plm_id": "PLM-PAR-002",
      "component_version": 2,
      "component_revision": "",
      "component_file_name": "BracketCover_Part.SLDPRT",
      "quantity": 1,
      "position_id": 2,
      "insertion_state": "Resolved",
      "suppressed": false,
      "component_vault_path": "e:\\PLM_VAULT\\Projects\\ProjectA\\CAD\\BracketCover_Part\\v002\\BracketCover_Part.SLDPRT"
    },
    {
      "instance_id": 3,
      "instance_name": "Fastener_M4_Socket_Head-1",
      "component_plm_id": "PLM-PAR-100",
      "component_version": 1,
      "component_revision": "",
      "component_file_name": "Fastener_M4_Socket_Head.SLDPRT",
      "quantity": 8,
      "position_id": 3,
      "insertion_state": "Configured",
      "suppressed": false,
      "component_vault_path": "e:\\PLM_VAULT\\Projects\\ProjectA\\CAD\\Fastener_M4_Socket_Head\\v001\\Fastener_M4_Socket_Head.SLDPRT"
    }
  ],
  "external_references": [
    {
      "external_plm_id": "PLM-PRJ-002_PLM-PAR-500",
      "external_file": "Connector_Type_A.SLDPRT",
      "external_project": "ProjectB",
      "version_used": 1,
      "reason": "Standard connector (cross-project reuse)"
    }
  ]
}
```

### vault/Locks/{ProjectName}_{PartName}.lock
```json
{
  "lock_id": 1,
  "file_id": 5,
  "file_name": "BracketBase_Part",
  "locked_by": "john.smith",
  "lock_timestamp": "2026-01-15T14:32:00Z",
  "lock_reason": "Edit",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "lock_expiry": "2026-01-16T14:32:00Z",
  "last_heartbeat": "2026-01-15T15:25:00Z",
  "is_stale": false
}
```

### vault/Logs/access_log.json
```json
[
  {
    "log_id": 1001,
    "timestamp": "2026-01-15T14:32:00Z",
    "user": "john.smith",
    "action": "SAVE",
    "project_name": "ProjectA",
    "file_name": "BracketBase_Part",
    "version": 3,
    "details": {
      "previous_version": 2,
      "change_note": "Increased wall thickness",
      "file_size": 2847392,
      "duration_ms": 1250
    }
  },
  {
    "log_id": 1002,
    "timestamp": "2026-01-15T14:35:00Z",
    "user": "jane.doe",
    "action": "OPEN",
    "project_name": "ProjectA",
    "file_name": "BracketBase_Part",
    "version": 3,
    "details": {
      "access_mode": "READ_ONLY",
      "reason": "File locked by john.smith"
    }
  },
  {
    "log_id": 1003,
    "timestamp": "2026-01-15T16:00:00Z",
    "user": "john.smith",
    "action": "PROMOTE",
    "project_name": "ProjectA",
    "file_name": "BracketBase_Part",
    "version": 3,
    "details": {
      "from_state": "In-Work",
      "to_state": "Released",
      "new_revision": "A"
    }
  }
]
```

## Directory Structure Creation Script

```python
# create_vault_structure.py
import os
import json
from pathlib import Path
from datetime import datetime

def create_vault_structure(vault_root: str):
    """Create initial PLM_VAULT directory structure"""
    
    # Root directories
    dirs = [
        vault_root,
        f"{vault_root}/Projects",
        f"{vault_root}/Locks",
        f"{vault_root}/Logs",
        f"{vault_root}/Utils",
        f"{vault_root}/db_backup",
        f"{vault_root}/Utils/migration_scripts"
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {d}")
    
    # Create vault config
    config = {
        "vault_version": "1.0",
        "vault_name": "PLM_VAULT",
        "vault_path": vault_root,
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
    
    with open(f"{vault_root}/config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Created: {vault_root}/config.json")

if __name__ == "__main__":
    create_vault_structure("e:\\PLM_VAULT")
    print("\n✓ Vault structure created successfully!")
```

## Directory Permissions

Set folder permissions (Windows NTFS):
```
PLM_VAULT/               → Full Control (Admins) + Modify (Users)
  Projects/             → Modify (all team members)
    ProjectA/           → Modify (project team)
      CAD/              → Read + Execute (all users reading files)
        Part1/          → Read + Execute
          v001/         → Read-Only (immutable)
          v002/         → Read-Only (immutable)
  Locks/                → Modify (service account only)
  Logs/                 → Append-Only (service account)
```

## Maintenance

**Daily:**
- Monitor Locks/ for stale .lock files (age > 24h)
- Compact SQLite database if size > 500MB

**Weekly:**
- Validate checksums on all vault files
- Generate access reports

**Monthly:**
- Archive logs to `audit_archive_YYYYMM.json`
- Backup entire vault

