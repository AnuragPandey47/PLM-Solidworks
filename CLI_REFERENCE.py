"""
PLM CLI Tool - Quick Reference
Print this or keep it open while using the tool!
"""

CLI_REFERENCE = r"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    PLM CLI TOOL - QUICK REFERENCE                         ║
║                    Version 1.0 - January 2026                             ║
╚════════════════════════════════════════════════════════════════════════════╝

INSTALLATION
────────────────────────────────────────────────────────────────────────────
$ cd e:\PLM_SOLIDWORKS
$ python cli-tool\plm.py --help


PROJECT MANAGEMENT
────────────────────────────────────────────────────────────────────────────

Create a new project:
$ python plm.py project create \\
  --name "ProjectA" \\
  --owner "john.smith" \\
  --description "Bracket assembly project"
  
Output: PLM ID (e.g., PLM-PRJ-001)

List all projects:
$ python plm.py project list

Show project details:
$ python plm.py project info --id 1


FILE MANAGEMENT
────────────────────────────────────────────────────────────────────────────

List files in a project:
$ python plm.py file list --project-id 1

Show file details and version history:
$ python plm.py file info --id 5


VERSION CONTROL
────────────────────────────────────────────────────────────────────────────

List all versions of a file:
$ python plm.py version list --file-id 5

Expected output:
  Ver  Rev   Author          Created             State        
  1         john.smith      2026-01-10 09:00    In-Work      
  2         john.smith      2026-01-12 14:30    In-Work      
  3    A     john.smith      2026-01-15 16:00    Released     

Promote version to Released (lock for editing):
$ python plm.py version promote \\
  --file-id 5 \\
  --version 3 \\
  --state "Released" \\
  --user "john.smith" \\
  --note "FEA validated, ready for manufacturing"

Valid states: In-Work, Released, Obsolete


ASSEMBLY MANAGEMENT
────────────────────────────────────────────────────────────────────────────

Show assembly bill of materials (BOM):
$ python plm.py assembly bom --id 10

Expected output:
  Component                  PLM ID          Ver  Qty
  ───────────────────────────────────────────────────
  BracketBase_Part           PLM-PAR-001     3    1
  BracketCover_Part          PLM-PAR-002     2    1
  Fastener_M4_Socket_Head    PLM-PAR-100     1    8


LOCK MANAGEMENT
────────────────────────────────────────────────────────────────────────────

List all active file locks:
$ python plm.py lock list

Clean stale locks (older than 24 hours):
$ python plm.py lock clean
$ python plm.py lock clean --max-age 12  # 12 hours instead


VAULT OPERATIONS
────────────────────────────────────────────────────────────────────────────

Check vault health and integrity:
$ python plm.py vault status

Output includes:
  - Number of projects, files, versions
  - Orphaned versions (data issues)
  - Missing checksums
  - Stale locks (old locks > 24h)

Show audit trail (activity log):
$ python plm.py vault audit

Filter by file:
$ python plm.py vault audit --file-id 5 --limit 20

Filter by user:
$ python plm.py vault audit --user "john.smith" --limit 10


COMMON WORKFLOWS
────────────────────────────────────────────────────────────────────────────

1. START NEW PROJECT
   ────────────────────────────────────────────────────────────────────
   $ python plm.py project create \\
     --name "NewProject" \\
     --owner "john.smith" \\
     --description "Description here"


2. VIEW PROJECT FILES
   ────────────────────────────────────────────────────────────────────
   $ python plm.py project list           # Get project ID
   $ python plm.py file list --project-id 1


3. VIEW FILE VERSION HISTORY
   ────────────────────────────────────────────────────────────────────
   $ python plm.py file list --project-id 1   # Get file ID
   $ python plm.py version list --file-id 5


4. PROMOTE FILE TO RELEASED (PRODUCTION)
   ────────────────────────────────────────────────────────────────────
   $ python plm.py version promote \\
     --file-id 5 \\
     --version 3 \\
     --state "Released" \\
     --user "john.smith" \\
     --note "Production approved"


5. CHECK VAULT HEALTH
   ────────────────────────────────────────────────────────────────────
   $ python plm.py vault status       # See if any issues
   $ python plm.py lock list          # Check for stuck locks
   $ python plm.py lock clean         # Clean stale locks


6. VIEW ASSEMBLY COMPONENTS
   ────────────────────────────────────────────────────────────────────
   $ python plm.py assembly bom --id 10   # View assembly BOM


7. TRACK USER ACTIVITY
   ────────────────────────────────────────────────────────────────────
   $ python plm.py vault audit --user "john.smith"


TROUBLESHOOTING
────────────────────────────────────────────────────────────────────────────

"File not found" error?
→ Check file ID: $ python plm.py file list --project-id 1

"Cannot promote Released version"?
→ That's correct - Released versions can't be modified. Create new major 
  version in SolidWorks to continue editing.

"Stale locks detected"?
→ Clean them: $ python plm.py lock clean

"Database appears corrupted"?
→ Restore from backup: See README.md Troubleshooting section


TIPS & TRICKS
────────────────────────────────────────────────────────────────────────────

1. Always check vault health after major changes:
   $ python plm.py vault status

2. View audit trail for specific file to understand change history:
   $ python plm.py vault audit --file-id 5

3. Get project ID first, then list files:
   $ python plm.py project list      # Shows project IDs
   $ python plm.py file list --project-id 1

4. Use the CLI to manage lifecycle without opening SolidWorks:
   $ python plm.py version promote ... # Perfect for automation

5. Regular vault status checks catch issues early:
   $ python plm.py vault status       # Run weekly


HELP & DOCUMENTATION
────────────────────────────────────────────────────────────────────────────

Command help:
  $ python plm.py --help
  $ python plm.py project --help
  $ python plm.py file --help
  $ python plm.py version --help
  $ python plm.py assembly --help
  $ python plm.py lock --help
  $ python plm.py vault --help

Read the documentation:
  - README.md - User guide & quick start
  - ARCHITECTURE.md - System design
  - DATABASE_SCHEMA.md - Database structure
  - VERSIONING_ALGORITHM.md - Versioning rules


KEYBOARD SHORTCUTS
────────────────────────────────────────────────────────────────────────────

None yet (CLI tool doesn't use interactive mode)
Note: Could be added in future versions!


KEYBOARD SHORTCUTS
────────────────────────────────────────────────────────────────────────────

Ctrl+C          Interrupt current command
Tab             No auto-complete yet (future enhancement)


PATH EXAMPLES
────────────────────────────────────────────────────────────────────────────

Vault location:           e:\PLM_VAULT
Project folder:           e:\PLM_VAULT\Projects\ProjectA
File folder:              e:\PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part
Version folder:           e:\PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part\v003
Metadata file:            e:\PLM_VAULT\Projects\ProjectA\CAD\BracketBase_Part\v003\metadata.json
Database:                 e:\PLM_VAULT\db.sqlite


ENVIRONMENT SETUP
────────────────────────────────────────────────────────────────────────────

Verify environment:
  $ python check_env.py

Initialize vault (first time):
  $ python SETUP.py

Set up as scheduled task (Windows):
  Task Scheduler → New Task
  Trigger: Daily 2 AM
  Action: python c:\PLM_SOLIDWORKS\cli-tool\plm.py vault status


═══════════════════════════════════════════════════════════════════════════════

Questions? See:
  - README.md for usage guide
  - ARCHITECTURE.md for design details
  - DATABASE_SCHEMA.md for database info

Report issues or suggestions to: [your team]

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(CLI_REFERENCE)
    
    # Optionally save to file
    with open("CLI_REFERENCE.txt", "w") as f:
        f.write(CLI_REFERENCE)
    print("\n✓ Reference saved to CLI_REFERENCE.txt")
