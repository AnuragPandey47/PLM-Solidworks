#!/usr/bin/env python3
"""
PLM CLI Tool
Command-line interface for PLM operations (works without SolidWorks)
- Create projects
- List versions
- Promote lifecycle state
- Manage files
- Vault operations
"""

import sys
import os
import json
import argparse
from typing import Optional
from pathlib import Path
from datetime import datetime
from typing import Optional
import sqlite3

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from database.db import PLMDatabase


class PLMCLI:
    """Command-line interface for PLM operations"""
    
    def __init__(self, vault_path: str = r"e:\PLM_VAULT"):
        self.vault_path = vault_path
        self.db = PLMDatabase(vault_path)
    
    # ========================
    # PROJECT COMMANDS
    # ========================
    
    def cmd_project_create(self, name: str, owner: str, description: str = ""):
        """Create new project
        
        Usage: plm project create --name ProjectA --owner john.smith --description "Bracket assembly"
        """
        try:
            project = self.db.create_project(name, owner, description)
            
            # Create vault directory structure
            vault_path = project["vault_path"]
            for subdir in ["CAD", "Drawings", "Excel", "Archive"]:
                Path(os.path.join(vault_path, subdir)).mkdir(parents=True, exist_ok=True)
            
            print(f"✓ Project created successfully")
            print(f"  PLM ID: {project['plm_id']}")
            print(f"  Name: {project['name']}")
            print(f"  Owner: {owner}")
            print(f"  Vault path: {vault_path}")
            return 0
        except Exception as e:
            print(f"✗ Error creating project: {e}")
            return 1
    
    def cmd_project_list(self):
        """List all projects"""
        try:
            projects = self.db.list_projects()
            
            if not projects:
                print("No projects found")
                return 0
            
            print(f"\n{'PLM ID':<15} {'Name':<20} {'Owner':<15} {'Created':<19}")
            print("-" * 70)
            
            for proj in projects:
                created = proj["created_date"][:10] if proj["created_date"] else "N/A"
                print(f"{proj['plm_id']:<15} {proj['name']:<20} {proj['owner']:<15} {created:<19}")
            
            print(f"\nTotal: {len(projects)} projects")
            return 0
        except Exception as e:
            print(f"✗ Error listing projects: {e}")
            return 1
    
    def cmd_project_info(self, project_id: int):
        """Show project details"""
        try:
            project = self.db.get_project(project_id)
            
            if not project:
                print(f"✗ Project {project_id} not found")
                return 1
            
            print(f"\nProject: {project['name']} ({project['plm_id']})")
            print(f"  Owner: {project['owner']}")
            print(f"  Description: {project['description'] or 'N/A'}")
            print(f"  Created: {project['created_date']}")
            print(f"  Vault path: {project['vault_path']}")
            
            # List files in project
            files = self.db.list_project_files(project_id)
            print(f"\n  Files ({len(files)}):")
            for f in files:
                print(f"    - {f['file_name']} ({f['plm_id']}) - v{f['current_version']} - {f['lifecycle_state']}")
            
            return 0
        except Exception as e:
            print(f"✗ Error getting project info: {e}")
            return 1
    
    # ========================
    # FILE COMMANDS
    # ========================
    
    def cmd_file_list(self, project_id: int):
        """List files in project"""
        try:
            files = self.db.list_project_files(project_id)
            
            if not files:
                print(f"No files in project {project_id}")
                return 0
            
            print(f"\n{'PLM ID':<15} {'File Name':<25} {'Type':<10} {'Ver':<3} {'State':<12} {'Lock':<15}")
            print("-" * 85)
            
            for f in files:
                lock_info = f["locked_by"] or "-"
                print(f"{f['plm_id']:<15} {f['file_name']:<25} {f['file_type']:<10} " 
                      f"{f['current_version']:<3} {f['lifecycle_state']:<12} {lock_info:<15}")
            
            print(f"\nTotal: {len(files)} files")
            return 0
        except Exception as e:
            print(f"✗ Error listing files: {e}")
            return 1
    
    def cmd_file_info(self, file_id: int):
        """Show file details and version history"""
        try:
            file = self.db.get_file(file_id)
            
            if not file:
                print(f"✗ File {file_id} not found")
                return 1
            
            print(f"\nFile: {file['file_name']} ({file['plm_id']})")
            print(f"  Type: {file['file_type']}")
            print(f"  Project ID: {file['project_id']}")
            print(f"  Current Version: v{file['current_version']}")
            print(f"  Lifecycle: {file['lifecycle_state']}")
            print(f"  Locked by: {file['locked_by'] or 'None'}")
            print(f"  Vault path: {file['vault_path']}")
            
            # List versions
            versions = self.db.list_file_versions(file_id)
            print(f"\n  Version History ({len(versions)}):")
            print(f"  {'Ver':<4} {'Rev':<3} {'Author':<15} {'Created':<19} {'State':<12} {'Note':<50}")
            print("  " + "-" * 100)
            
            for v in versions:
                created = v["created_timestamp"][:10] if v["created_timestamp"] else "N/A"
                note = (v["change_note"] or "")[:50]
                rev = v["revision_letter"] or "-"
                print(f"  {v['version_number']:<4} {rev:<3} {v['author']:<15} {created:<19} "
                      f"{v['lifecycle_state']:<12} {note:<50}")
            
            return 0
        except Exception as e:
            print(f"✗ Error getting file info: {e}")
            return 1
    
    # ========================
    # VERSION COMMANDS
    # ========================
    
    def cmd_version_list(self, file_id: int):
        """List all versions of a file"""
        try:
            file = self.db.get_file(file_id)
            if not file:
                print(f"✗ File {file_id} not found")
                return 1
            
            versions = self.db.list_file_versions(file_id)
            
            print(f"\nVersions of {file['file_name']} ({file['plm_id']}):")
            print(f"\n{'Ver':<4} {'Rev':<4} {'Author':<15} {'Created':<19} {'State':<12} {'Size':<10} {'Note':<50}")
            print("-" * 110)
            
            for v in versions:
                created = v["created_timestamp"][:16] if v["created_timestamp"] else "N/A"
                rev = v["revision_letter"] or "-"
                size_kb = (v["file_size_bytes"] or 0) // 1024
                note = (v["change_note"] or "")[:50]
                print(f"{v['version_number']:<4} {rev:<4} {v['author']:<15} {created:<19} "
                      f"{v['lifecycle_state']:<12} {size_kb:<10} {note:<50}")
            
            return 0
        except Exception as e:
            print(f"✗ Error listing versions: {e}")
            return 1
    
    def cmd_version_promote(self, file_id: int, version_num: int, new_state: str, 
                           user: str, note: str = ""):
        """Promote version to new lifecycle state
        
        Usage: plm version promote --file-id 5 --version 3 --state Released --user john.smith
        """
        try:
            file = self.db.get_file(file_id)
            if not file:
                print(f"✗ File {file_id} not found")
                return 1
            
            # Get version ID
            versions = self.db.list_file_versions(file_id)
            version_id = None
            for v in versions:
                if v["version_number"] == version_num:
                    version_id = v["version_id"]
                    break
            
            if not version_id:
                print(f"✗ Version {version_num} not found")
                return 1
            
            # Check valid state
            if new_state not in ["In-Work", "Released", "Obsolete"]:
                print(f"✗ Invalid state: {new_state}")
                return 1
            
            # Promote
            self.db.promote_version(version_id, new_state, user, note)
            
            print(f"✓ Promoted {file['file_name']} v{version_num} → {new_state}")
            print(f"  Promoted by: {user}")
            if note:
                print(f"  Note: {note}")
            
            return 0
        except Exception as e:
            print(f"✗ Error promoting version: {e}")
            return 1
    
    # ========================
    # ASSEMBLY COMMANDS
    # ========================
    
    def cmd_assembly_bom(self, assembly_file_id: int):
        """Show assembly bill of materials (BOM)"""
        try:
            assembly = self.db.get_file(assembly_file_id)
            if not assembly:
                print(f"✗ Assembly {assembly_file_id} not found")
                return 1
            
            bom = self.db.get_assembly_bom(assembly_file_id)
            
            print(f"\nBOM for {assembly['file_name']} ({assembly['plm_id']})")
            print(f"\n{'Component':<25} {'PLM ID':<15} {'Ver':<3} {'Qty':<3}")
            print("-" * 50)
            
            total_qty = 0
            for item in bom:
                print(f"{item['component_name']:<25} {item['component_plm_id']:<15} "
                      f"{item['component_version']:<3} {item['instance_count']:<3}")
                total_qty += item["instance_count"]
            
            print("-" * 50)
            print(f"Total parts: {len(bom)}, Total qty: {total_qty}")
            return 0
        except Exception as e:
            print(f"✗ Error getting BOM: {e}")
            return 1
    
    # ========================
    # LOCK COMMANDS
    # ========================
    
    def cmd_lock_list(self):
        """List active file locks"""
        try:
            locks = self.db.get_active_locks()
            
            if not locks:
                print("No active locks")
                return 0
            
            print(f"\nActive Locks:")
            print(f"\n{'File':<25} {'Locked By':<15} {'Since':<19} {'Age (hrs)':<10}")
            print("-" * 70)
            
            for lock in locks:
                timestamp = lock["lock_timestamp"][:16] if lock["lock_timestamp"] else "N/A"
                print(f"{lock['file_name']:<25} {lock['locked_by']:<15} {timestamp:<19} "
                      f"{lock['hours_locked']:<10}")
            
            return 0
        except Exception as e:
            print(f"✗ Error listing locks: {e}")
            return 1
    
    def cmd_lock_clean(self, max_age_hours: int = 24):
        """Clean stale locks (older than N hours)"""
        try:
            count = self.db.clean_stale_locks(max_age_hours)
            print(f"✓ Cleaned {count} stale lock(s) (older than {max_age_hours} hours)")
            return 0
        except Exception as e:
            print(f"✗ Error cleaning locks: {e}")
            return 1
    
    # ========================
    # VAULT COMMANDS
    # ========================
    
    def cmd_vault_status(self):
        """Show vault integrity status"""
        try:
            integrity = self.db.validate_vault_integrity()
            
            print("\n=== VAULT INTEGRITY CHECK ===")
            print(f"Projects:           {integrity['project_count']}")
            print(f"Files:              {integrity['file_count']}")
            print(f"Versions:           {integrity['version_count']}")
            print(f"Orphaned versions:  {integrity['orphaned_versions']}")
            print(f"Missing checksums:  {integrity['missing_checksums']}")
            print(f"Stale locks:        {integrity['stale_locks']}")
            
            # Warning for issues
            if integrity['orphaned_versions'] > 0:
                print(f"\n⚠ Warning: {integrity['orphaned_versions']} orphaned versions found")
            if integrity['missing_checksums'] > 0:
                print(f"⚠ Warning: {integrity['missing_checksums']} versions missing checksums")
            if integrity['stale_locks'] > 0:
                print(f"⚠ Warning: {integrity['stale_locks']} stale locks detected")
            
            if integrity['orphaned_versions'] == 0 and integrity['stale_locks'] == 0:
                print("\n✓ Vault is healthy")
            
            return 0
        except Exception as e:
            print(f"✗ Error checking vault: {e}")
            return 1
    
    def cmd_audit_log(self, file_id: Optional[int] = None, user: Optional[str] = None, limit: int = 50):
        """Show audit log"""
        try:
            logs = self.db.get_audit_trail(file_id, user, limit)
            
            if not logs:
                print("No audit log entries")
                return 0
            
            print(f"\nAudit Trail ({len(logs)} entries):")
            print(f"\n{'Timestamp':<19} {'User':<15} {'Action':<12} {'File':<25}")
            print("-" * 72)
            
            for log in logs:
                timestamp = log["action_timestamp"][:19] if log["action_timestamp"] else "N/A"
                print(f"{timestamp:<19} {log['user']:<15} {log['action']:<12} "
                      f"{log.get('file_id', '-'):<25}")
            
            return 0
        except Exception as e:
            print(f"✗ Error reading audit log: {e}")
            return 1
    
    # ========================
    # MAIN CLI ENTRY
    # ========================
    
    def main(self):
        """Main CLI entry point"""
        parser = argparse.ArgumentParser(
            description="PLM CLI Tool - SolidWorks Product Lifecycle Management",
            prog="plm"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # PROJECT commands
        proj_parser = subparsers.add_parser("project", help="Project management")
        proj_sub = proj_parser.add_subparsers(dest="project_command")
        
        proj_create = proj_sub.add_parser("create", help="Create new project")
        proj_create.add_argument("--name", required=True, help="Project name")
        proj_create.add_argument("--owner", required=True, help="Project owner (username)")
        proj_create.add_argument("--description", default="", help="Project description")
        
        proj_list = proj_sub.add_parser("list", help="List all projects")
        
        proj_info = proj_sub.add_parser("info", help="Show project details")
        proj_info.add_argument("--id", type=int, required=True, help="Project ID")
        
        # FILE commands
        file_parser = subparsers.add_parser("file", help="File management")
        file_sub = file_parser.add_subparsers(dest="file_command")
        
        file_list = file_sub.add_parser("list", help="List files in project")
        file_list.add_argument("--project-id", type=int, required=True, help="Project ID")
        
        file_info = file_sub.add_parser("info", help="Show file details")
        file_info.add_argument("--id", type=int, required=True, help="File ID")
        
        # VERSION commands
        ver_parser = subparsers.add_parser("version", help="Version management")
        ver_sub = ver_parser.add_subparsers(dest="version_command")
        
        ver_list = ver_sub.add_parser("list", help="List versions of a file")
        ver_list.add_argument("--file-id", type=int, required=True, help="File ID")
        
        ver_promote = ver_sub.add_parser("promote", help="Promote version to new state")
        ver_promote.add_argument("--file-id", type=int, required=True, help="File ID")
        ver_promote.add_argument("--version", type=int, required=True, help="Version number")
        ver_promote.add_argument("--state", required=True, help="New state (In-Work|Released|Obsolete)")
        ver_promote.add_argument("--user", required=True, help="Promoted by (username)")
        ver_promote.add_argument("--note", default="", help="Promotion note")
        
        # ASSEMBLY commands
        asm_parser = subparsers.add_parser("assembly", help="Assembly management")
        asm_sub = asm_parser.add_subparsers(dest="assembly_command")
        
        asm_bom = asm_sub.add_parser("bom", help="Show assembly BOM")
        asm_bom.add_argument("--id", type=int, required=True, help="Assembly file ID")
        
        # LOCK commands
        lock_parser = subparsers.add_parser("lock", help="Lock management")
        lock_sub = lock_parser.add_subparsers(dest="lock_command")
        
        lock_list = lock_sub.add_parser("list", help="List active locks")
        
        lock_clean = lock_sub.add_parser("clean", help="Clean stale locks")
        lock_clean.add_argument("--max-age", type=int, default=24, help="Max age in hours (default: 24)")
        
        # VAULT commands
        vault_parser = subparsers.add_parser("vault", help="Vault management")
        vault_sub = vault_parser.add_subparsers(dest="vault_command")
        
        vault_status = vault_sub.add_parser("status", help="Show vault integrity status")
        
        vault_audit = vault_sub.add_parser("audit", help="Show audit log")
        vault_audit.add_argument("--file-id", type=int, help="Filter by file ID")
        vault_audit.add_argument("--user", help="Filter by user")
        vault_audit.add_argument("--limit", type=int, default=50, help="Number of entries")
        
        # Parse arguments
        args = parser.parse_args()
        
        # Execute commands
        if args.command == "project":
            if args.project_command == "create":
                return self.cmd_project_create(args.name, args.owner, args.description)
            elif args.project_command == "list":
                return self.cmd_project_list()
            elif args.project_command == "info":
                return self.cmd_project_info(args.id)
        
        elif args.command == "file":
            if args.file_command == "list":
                return self.cmd_file_list(args.project_id)
            elif args.file_command == "info":
                return self.cmd_file_info(args.id)
        
        elif args.command == "version":
            if args.version_command == "list":
                return self.cmd_version_list(args.file_id)
            elif args.version_command == "promote":
                return self.cmd_version_promote(args.file_id, args.version, args.state, 
                                               args.user, args.note)
        
        elif args.command == "assembly":
            if args.assembly_command == "bom":
                return self.cmd_assembly_bom(args.id)
        
        elif args.command == "lock":
            if args.lock_command == "list":
                return self.cmd_lock_list()
            elif args.lock_command == "clean":
                return self.cmd_lock_clean(args.max_age)
        
        elif args.command == "vault":
            if args.vault_command == "status":
                return self.cmd_vault_status()
            elif args.vault_command == "audit":
                return self.cmd_audit_log(args.file_id, args.user, args.limit)
        
        else:
            parser.print_help()
            return 1
        
        return 0


if __name__ == "__main__":
    cli = PLMCLI()
    exit_code = cli.main()
    sys.exit(exit_code)
