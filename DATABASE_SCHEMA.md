# PLM Database Schema

## Overview

SQLite schema designed for immutable versioning, lifecycle management, and assembly tracking. Structured for future PostgreSQL migration.

---

## Complete SQL Schema

```sql
-- ============================================
-- 1. PROJECTS TABLE
-- ============================================

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plm_id TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    owner TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP,
    vault_path TEXT NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT 1,
    metadata JSON,
    
    CHECK (name != ''),
    CHECK (owner != '')
);

CREATE INDEX idx_projects_plm_id ON projects(plm_id);
CREATE INDEX idx_projects_owner ON projects(owner);
CREATE INDEX idx_projects_active ON projects(is_active);


-- ============================================
-- 2. FILES TABLE (Parts, Assemblies, Drawings)
-- ============================================

CREATE TABLE files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plm_id TEXT UNIQUE NOT NULL,
    project_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'PART', 'ASSEMBLY', 'DRAWING', 'OTHER'
    description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP,
    current_version INTEGER DEFAULT 1,
    lifecycle_state TEXT DEFAULT 'In-Work',  -- 'In-Work', 'Released', 'Obsolete'
    locked_by TEXT,
    lock_timestamp TIMESTAMP,
    vault_path TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CHECK (file_name != ''),
    CHECK (file_type IN ('PART', 'ASSEMBLY', 'DRAWING', 'OTHER')),
    CHECK (lifecycle_state IN ('In-Work', 'Released', 'Obsolete')),
    UNIQUE (project_id, file_name)
);

CREATE INDEX idx_files_plm_id ON files(plm_id);
CREATE INDEX idx_files_project ON files(project_id);
CREATE INDEX idx_files_lifecycle ON files(lifecycle_state);
CREATE INDEX idx_files_locked_by ON files(locked_by);
CREATE INDEX idx_files_active ON files(is_active);


-- ============================================
-- 3. VERSIONS TABLE (Immutable history)
-- ============================================

CREATE TABLE versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    revision_letter TEXT DEFAULT '',  -- '', 'A', 'B', 'C', etc.
    author TEXT NOT NULL,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_note TEXT,
    lifecycle_state TEXT DEFAULT 'In-Work',  -- 'In-Work', 'Released', 'Obsolete'
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    checksum TEXT,  -- SHA256
    custom_properties JSON,
    solidworks_properties JSON,
    is_locked BOOLEAN DEFAULT 0,
    lock_reason TEXT,  -- 'Edit', 'Review', etc.
    locked_by TEXT,
    lock_timestamp TIMESTAMP,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id),
    UNIQUE (file_id, version_number, revision_letter),
    CHECK (version_number > 0),
    CHECK (revision_letter IN ('', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'))
);

CREATE INDEX idx_versions_file ON versions(file_id);
CREATE INDEX idx_versions_created ON versions(created_timestamp);
CREATE INDEX idx_versions_author ON versions(author);
CREATE INDEX idx_versions_lifecycle ON versions(lifecycle_state);


-- ============================================
-- 4. ASSEMBLY RELATIONSHIPS (BOM tracking)
-- ============================================

CREATE TABLE assembly_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    assembly_file_id INTEGER NOT NULL,  -- Parent (assembly)
    component_file_id INTEGER NOT NULL,  -- Child (part)
    component_version INTEGER NOT NULL,  -- Which version is used in this assembly version
    instance_count INTEGER DEFAULT 1,
    instance_names TEXT,  -- JSON list: ["BracketBase-1", "BracketBase-2"]
    insertion_state TEXT,  -- 'Configured', 'Resolved', 'Suppressed'
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP,
    
    FOREIGN KEY (assembly_file_id) REFERENCES files(file_id),
    FOREIGN KEY (component_file_id) REFERENCES files(file_id),
    UNIQUE (assembly_file_id, component_file_id, component_version),
    CHECK (component_version > 0),
    CHECK (instance_count > 0)
);

CREATE INDEX idx_assembly_parent ON assembly_relationships(assembly_file_id);
CREATE INDEX idx_assembly_component ON assembly_relationships(component_file_id);


-- ============================================
-- 5. FILE LOCKS TABLE
-- ============================================

CREATE TABLE file_locks (
    lock_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    locked_by TEXT NOT NULL,
    lock_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lock_release_timestamp TIMESTAMP,
    lock_reason TEXT,  -- 'Edit', 'Review'
    session_id TEXT UNIQUE,  -- Unique session identifier (GUID)
    is_stale BOOLEAN DEFAULT 0,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id),
    CHECK (lock_reason IN ('Edit', 'Review', 'Other'))
);

CREATE INDEX idx_locks_file ON file_locks(file_id);
CREATE INDEX idx_locks_user ON file_locks(locked_by);
CREATE INDEX idx_locks_active ON file_locks(lock_release_timestamp);


-- ============================================
-- 6. VERSION TRANSITIONS (Lifecycle audit)
-- ============================================

CREATE TABLE version_transitions (
    transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    promoted_by TEXT NOT NULL,
    promotion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    promotion_note TEXT,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id),
    FOREIGN KEY (version_id) REFERENCES versions(version_id),
    CHECK (from_state IN ('In-Work', 'Released', 'Obsolete')),
    CHECK (to_state IN ('In-Work', 'Released', 'Obsolete'))
);

CREATE INDEX idx_transitions_file ON version_transitions(file_id);
CREATE INDEX idx_transitions_timestamp ON version_transitions(promotion_timestamp);


-- ============================================
-- 7. ACCESS LOG (Audit trail)
-- ============================================

CREATE TABLE access_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'OPEN', 'SAVE', 'PROMOTE', 'DELETE', 'CHECK_OUT', 'CHECK_IN'
    file_id INTEGER,
    project_id INTEGER,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,
    details JSON,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CHECK (action IN ('OPEN', 'SAVE', 'PROMOTE', 'DELETE', 'CHECK_OUT', 'CHECK_IN', 'REVERT'))
);

CREATE INDEX idx_log_user ON access_log(user);
CREATE INDEX idx_log_action ON access_log(action);
CREATE INDEX idx_log_timestamp ON access_log(action_timestamp);


-- ============================================
-- 8. VIEWS (For convenience queries)
-- ============================================

-- Latest version of each file
CREATE VIEW latest_versions AS
SELECT 
    f.file_id,
    f.plm_id,
    f.file_name,
    v.version_id,
    v.version_number,
    v.revision_letter,
    v.author,
    v.created_timestamp,
    v.lifecycle_state,
    f.locked_by,
    f.is_active
FROM files f
JOIN versions v ON f.file_id = v.file_id
WHERE v.version_id = (
    SELECT MAX(version_id) FROM versions WHERE file_id = f.file_id
);

-- Active locks only
CREATE VIEW active_locks AS
SELECT 
    lock_id,
    file_id,
    locked_by,
    lock_timestamp,
    session_id,
    CAST((julianday('now') - julianday(lock_timestamp)) * 24 AS INTEGER) AS hours_locked
FROM file_locks
WHERE lock_release_timestamp IS NULL
  AND is_stale = 0;

-- Assembly BOM for a specific assembly version
CREATE VIEW assembly_bom AS
SELECT 
    a.assembly_file_id,
    f_parent.file_name AS assembly_name,
    f_parent.plm_id AS assembly_plm_id,
    a.component_file_id,
    f_child.file_name AS component_name,
    f_child.plm_id AS component_plm_id,
    a.component_version,
    a.instance_count,
    a.insertion_state
FROM assembly_relationships a
JOIN files f_parent ON a.assembly_file_id = f_parent.file_id
JOIN files f_child ON a.component_file_id = f_child.file_id;
```

---

## Schema Design Rationale

| Feature | Design | Why |
|---------|--------|-----|
| **Immutable versions** | Separate `versions` table with unique `(file_id, version_number, revision_letter)` | Prevent accidental modification, maintain full history |
| **PLM IDs** | Unique `plm_id` column across all files | Assembly references survive file moves/renames |
| **Lifecycle states** | Single `lifecycle_state` column with CHECK constraint | Enforce valid transitions (In-Work → Released → Obsolete) |
| **Checksums** | SHA256 in `versions` table | Detect vault file corruption |
| **JSON metadata** | `custom_properties` and `solidworks_properties` as JSON | Flexible SWKS property storage, no schema bloat |
| **Lock session IDs** | GUID-based `session_id` | Detect stale locks, prevent false conflicts |
| **Audit trail** | Separate `access_log` table (append-only) | Complete traceability, no data loss on updates |
| **Constraints** | CHECK, UNIQUE, FOREIGN KEY | Database-level integrity, prevent invalid states |

---

## Database Initialization Script (Python)

```python
# database/init_db.py
import sqlite3
import os
from pathlib import Path

def init_database(vault_path: str):
    """Initialize PLM SQLite database with schema"""
    
    db_path = os.path.join(vault_path, "db.sqlite")
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Execute schema SQL
    schema_sql = """
    -- Projects
    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plm_id TEXT UNIQUE NOT NULL,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        owner TEXT NOT NULL,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_date TIMESTAMP,
        vault_path TEXT NOT NULL UNIQUE,
        is_active BOOLEAN DEFAULT 1,
        metadata JSON,
        
        CHECK (name != ''),
        CHECK (owner != '')
    );
    
    CREATE INDEX IF NOT EXISTS idx_projects_plm_id ON projects(plm_id);
    CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner);
    
    -- [Additional tables as defined above...]
    
    """
    
    cursor.executescript(schema_sql)
    conn.commit()
    
    print(f"✓ Database initialized: {db_path}")
    return conn

def get_next_plm_id(conn: sqlite3.Connection, prefix: str) -> str:
    """Generate next PLM ID (e.g., PLM-PAR-001)"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX(CAST(SUBSTR(plm_id, -3) AS INTEGER)) FROM files WHERE plm_id LIKE '{prefix}-%'")
    result = cursor.fetchone()
    next_num = (result[0] or 0) + 1
    return f"{prefix}-{next_num:03d}"

if __name__ == "__main__":
    conn = init_database("e:\\PLM_VAULT")
    print("Database ready for use!")
    conn.close()
```

---

## Migration to PostgreSQL (v1.0+)

### Migration Strategy

```sql
-- 1. Create PostgreSQL tables (identical schema)
CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    plm_id TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    ...
);

-- 2. Export SQLite data
SELECT * INTO OUTFILE 'projects.csv' FROM projects;

-- 3. Import into PostgreSQL
COPY projects FROM 'projects.csv' WITH (FORMAT csv);

-- 4. Verify row counts
SELECT COUNT(*) FROM projects;  -- Compare with SQLite

-- 5. Validate checksums
SELECT COUNT(*) WHERE checksum IS NOT NULL;  -- Should match SQLite

-- 6. Run in parallel for 24+ hours with data validation

-- 7. Switch application connection strings
-- OLD: sqlite:///e:\PLM_VAULT\db.sqlite
-- NEW: postgresql://user:pass@db.example.com:5432/plm_vault
```

### PostgreSQL Advantages Over SQLite

| Feature | SQLite | PostgreSQL |
|---------|--------|-----------|
| **Concurrent users** | Limited (file-level lock) | Unlimited (MVCC) |
| **Network access** | No (local only) | Yes (LAN + VPN) |
| **Replication** | Manual backup | Built-in (Streaming, Logical) |
| **Full-text search** | Basic | Advanced (tsvector, GiST) |
| **Row-level security** | No | Yes |
| **JSON support** | Basic | Advanced (jsonb operators) |

---

## Queries Reference

### Find latest version of a part

```sql
SELECT f.plm_id, f.file_name, v.version_number, v.revision_letter, v.author, v.created_timestamp
FROM files f
JOIN versions v ON f.file_id = v.file_id
WHERE f.plm_id = 'PLM-PAR-001'
ORDER BY v.version_id DESC
LIMIT 1;
```

### Find all parts in an assembly

```sql
SELECT DISTINCT
    f_child.plm_id,
    f_child.file_name,
    a.component_version,
    a.instance_count
FROM assembly_relationships a
JOIN files f_parent ON a.assembly_file_id = f_parent.file_id
JOIN files f_child ON a.component_file_id = f_child.file_id
WHERE f_parent.plm_id = 'PLM-ASM-001'
ORDER BY f_child.file_name;
```

### Find files locked for more than 24 hours

```sql
SELECT 
    f.file_name,
    fl.locked_by,
    fl.lock_timestamp,
    CAST((julianday('now') - julianday(fl.lock_timestamp)) * 24 AS INTEGER) AS hours_locked
FROM file_locks fl
JOIN files f ON fl.file_id = f.file_id
WHERE fl.lock_release_timestamp IS NULL
  AND (julianday('now') - julianday(fl.lock_timestamp)) * 24 > 24
ORDER BY hours_locked DESC;
```

### Audit trail for a specific file

```sql
SELECT 
    user,
    action,
    action_timestamp,
    details
FROM access_log
WHERE file_id = (SELECT file_id FROM files WHERE plm_id = 'PLM-PAR-001')
ORDER BY action_timestamp DESC
LIMIT 50;
```

---

