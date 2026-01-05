"""
PLM Database Layer
- SQLite initialization & migration
- CRUD operations for projects, files, versions
- Lock management
- Lifecycle management
"""

import sqlite3
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import logging
from contextlib import contextmanager
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PLMDatabase:
    """Main database interface for PLM system"""
    
    def __init__(self, vault_path: str):
        """Initialize PLM database
        
        Args:
            vault_path: Root path to PLM_VAULT directory
        """
        self.vault_path = vault_path
        self.db_path = os.path.join(vault_path, "db.sqlite")
        self._init_database()
    
    def _init_database(self):
        """Create database file if not exists, initialize schema"""
        
        # Create database file
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Connect and initialize
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        self._create_schema(cursor)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")
    
    def _create_schema(self, cursor):
        """Create all database tables and indexes"""
        
        schema = """
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
CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(is_active);

-- Files
CREATE TABLE IF NOT EXISTS files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plm_id TEXT UNIQUE NOT NULL,
    project_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP,
    current_version INTEGER DEFAULT 1,
    lifecycle_state TEXT DEFAULT 'In-Work',
    locked_by TEXT,
    lock_timestamp TIMESTAMP,
    vault_path TEXT NOT NULL,
    metadata_file_path TEXT,
    file_state TEXT DEFAULT 'Working',
    is_active BOOLEAN DEFAULT 1,
    
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CHECK (file_name != ''),
    CHECK (file_type IN ('PART', 'ASSEMBLY', 'DRAWING', 'OTHER')),
    CHECK (lifecycle_state IN ('In-Work', 'Released', 'Obsolete')),
    UNIQUE (project_id, file_name)
);

CREATE INDEX IF NOT EXISTS idx_files_plm_id ON files(plm_id);
CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id);
CREATE INDEX IF NOT EXISTS idx_files_lifecycle ON files(lifecycle_state);
CREATE INDEX IF NOT EXISTS idx_files_locked_by ON files(locked_by);

-- Versions
CREATE TABLE IF NOT EXISTS versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    revision_letter TEXT DEFAULT '',
    author TEXT NOT NULL,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_note TEXT,
    lifecycle_state TEXT DEFAULT 'In-Work',
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    checksum TEXT,
    custom_properties JSON,
    solidworks_properties JSON,
    is_locked BOOLEAN DEFAULT 0,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id),
    UNIQUE (file_id, version_number, revision_letter),
    CHECK (version_number > 0)
);

CREATE INDEX IF NOT EXISTS idx_versions_file ON versions(file_id);
CREATE INDEX IF NOT EXISTS idx_versions_created ON versions(created_timestamp);
CREATE INDEX IF NOT EXISTS idx_versions_author ON versions(author);

-- Assembly relationships
CREATE TABLE IF NOT EXISTS assembly_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    assembly_file_id INTEGER NOT NULL,
    component_file_id INTEGER NOT NULL,
    component_version INTEGER NOT NULL,
    instance_count INTEGER DEFAULT 1,
    instance_names TEXT,
    insertion_state TEXT,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP,
    
    FOREIGN KEY (assembly_file_id) REFERENCES files(file_id),
    FOREIGN KEY (component_file_id) REFERENCES files(file_id),
    UNIQUE (assembly_file_id, component_file_id, component_version),
    CHECK (component_version > 0),
    CHECK (instance_count > 0)
);

CREATE INDEX IF NOT EXISTS idx_assembly_parent ON assembly_relationships(assembly_file_id);
CREATE INDEX IF NOT EXISTS idx_assembly_component ON assembly_relationships(component_file_id);

-- File locks
CREATE TABLE IF NOT EXISTS file_locks (
    lock_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    locked_by TEXT NOT NULL,
    lock_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lock_release_timestamp TIMESTAMP,
    lock_reason TEXT,
    session_id TEXT UNIQUE,
    is_stale BOOLEAN DEFAULT 0,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id)
);

CREATE INDEX IF NOT EXISTS idx_locks_file ON file_locks(file_id);
CREATE INDEX IF NOT EXISTS idx_locks_user ON file_locks(locked_by);
CREATE INDEX IF NOT EXISTS idx_locks_active ON file_locks(lock_release_timestamp);

-- Version transitions (lifecycle changes)
CREATE TABLE IF NOT EXISTS version_transitions (
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

CREATE INDEX IF NOT EXISTS idx_transitions_file ON version_transitions(file_id);
CREATE INDEX IF NOT EXISTS idx_transitions_timestamp ON version_transitions(promotion_timestamp);

-- Access log
CREATE TABLE IF NOT EXISTS access_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    action TEXT NOT NULL,
    file_id INTEGER,
    project_id INTEGER,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,
    details JSON,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CHECK (action IN ('OPEN', 'SAVE', 'PROMOTE', 'DELETE', 'CHECK_OUT', 'CHECK_IN', 'REVERT'))
);

CREATE INDEX IF NOT EXISTS idx_log_user ON access_log(user);
CREATE INDEX IF NOT EXISTS idx_log_action ON access_log(action);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON access_log(action_timestamp);

-- Views
CREATE VIEW IF NOT EXISTS latest_versions AS
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

CREATE VIEW IF NOT EXISTS active_locks AS
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
        """
        
        cursor.executescript(schema)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ========================
    # PROJECT OPERATIONS
    # ========================
    
    def create_project(self, name: str, owner: str, description: str = "") -> Dict[str, Any]:
        """Create new project
        
        Args:
            name: Project name (unique)
            owner: Project owner (Windows username)
            description: Optional project description
            
        Returns:
            dict with project_id, plm_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Generate PLM ID
            plm_id = self._get_next_plm_id(cursor, "PRJ")
            
            # Create vault path
            vault_path = os.path.join(self.vault_path, "Projects", name)
            
            try:
                cursor.execute("""
                    INSERT INTO projects (plm_id, name, owner, description, vault_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (plm_id, name, owner, description, vault_path))
                
                conn.commit()
                project_id = cursor.lastrowid
                
                logger.info(f"Created project: {name} ({plm_id})")
                return {
                    "project_id": project_id,
                    "plm_id": plm_id,
                    "name": name,
                    "vault_path": vault_path
                }
            except sqlite3.IntegrityError as e:
                logger.error(f"Failed to create project: {e}")
                raise
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """Get project by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_projects(self, active_only: bool = True) -> List[Dict]:
        """List all projects"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM projects"
            if active_only:
                query += " WHERE is_active = 1"
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # FILE OPERATIONS
    # ========================
    
    def create_file(self, project_id: int, file_name: str, file_type: str, 
                   vault_path: str, description: str = "", metadata_file_path: str = "") -> Dict[str, Any]:
        """Create new file record in vault
        
        Args:
            project_id: Project ID
            file_name: File name (e.g., "BracketBase_Part")
            file_type: Type: PART, ASSEMBLY, DRAWING, OTHER
            vault_path: Vault path to file folder (e.g., Projects/ProjectName/Parts/FileName/)
            description: Optional description
            metadata_file_path: Path to part_meta.json file
            
        Returns:
            dict with file_id, plm_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Generate PLM ID
            type_map = {"PART": "PAR", "ASSEMBLY": "ASM", "DRAWING": "DRW"}
            type_code = type_map.get(file_type, "FIL")
            plm_id = self._get_next_plm_id(cursor, type_code)
            
            try:
                # Create folder structure on disk
                vault_path_obj = Path(vault_path)
                vault_path_obj.mkdir(parents=True, exist_ok=True)
                
                # Create metadata file if path provided
                if metadata_file_path:
                    metadata_path_obj = Path(metadata_file_path)
                    if not metadata_path_obj.exists():
                        initial_metadata = {
                            "latest_version": "v000",
                            "released_version": None,
                            "state": "Working"
                        }
                        with open(metadata_path_obj, 'w') as f:
                            json.dump(initial_metadata, f, indent=2)
                
                # Get project to find project vault path
                cursor.execute("SELECT vault_path FROM projects WHERE project_id = ?", (project_id,))
                project_row = cursor.fetchone()
                if not project_row:
                    raise Exception(f"Project {project_id} not found")
                
                project_vault_path = Path(project_row[0])
                
                # Create Working/Parts/ folder (flat, not subfolders per file)
                working_parts_folder = project_vault_path / "Working" / "Parts"
                working_parts_folder.mkdir(parents=True, exist_ok=True)
                
                # Create actual SLDPRT file in Working/Parts/
                ext_map = {"PART": ".SLDPRT", "ASSEMBLY": ".SLDASM", "DRAWING": ".SLDDRW"}
                ext = ext_map.get(file_type, ".txt")
                working_file = working_parts_folder / f"{file_name}{ext}"
                working_file.touch()  # Create empty file
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO files (plm_id, project_id, file_name, file_type, 
                                      vault_path, description, metadata_file_path, file_state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (plm_id, project_id, file_name, file_type, vault_path, description, 
                      metadata_file_path, "Working"))
                
                conn.commit()
                file_id = cursor.lastrowid
                
                logger.info(f"Created file: {file_name} ({plm_id}) at {vault_path}")
                return {
                    "file_id": file_id,
                    "plm_id": plm_id,
                    "file_name": file_name
                }
            except sqlite3.IntegrityError as e:
                logger.error(f"Failed to create file: {e}")
                raise
    
    def get_file(self, file_id: int) -> Optional[Dict]:
        """Get file by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE file_id = ?", (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_file_by_plm_id(self, plm_id: str) -> Optional[Dict]:
        """Get file by PLM ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE plm_id = ?", (plm_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_project_files(self, project_id: int) -> List[Dict]:
        """List all files in project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM files WHERE project_id = ? AND is_active = 1 ORDER BY file_name",
                (project_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # VERSION OPERATIONS
    # ========================
    
    def create_version(self, file_id: int, author: str, change_note: str = "",
                      file_path: str = "", file_size: int = 0, checksum: str = "",
                      custom_properties: Optional[Dict] = None, 
                      solidworks_properties: Optional[Dict] = None) -> Dict[str, Any]:
        """Create new version for file
        
        Args:
            file_id: File ID
            author: Author (Windows username)
            change_note: Description of changes
            file_path: Path to vault file
            file_size: File size in bytes
            checksum: SHA256 checksum
            custom_properties: dict of SWKS properties
            solidworks_properties: dict of SWKS metadata
            
        Returns:
            dict with version_id, version_number
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get next version number
            cursor.execute(
                "SELECT MAX(version_number) FROM versions WHERE file_id = ?",
                (file_id,)
            )
            result = cursor.fetchone()
            next_version = (result[0] or 0) + 1
            
            try:
                cursor.execute("""
                    INSERT INTO versions (file_id, version_number, author, change_note,
                                        file_path, file_size_bytes, checksum,
                                        custom_properties, solidworks_properties)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_id, next_version, author, change_note, file_path, file_size,
                    checksum,
                    json.dumps(custom_properties) if custom_properties else None,
                    json.dumps(solidworks_properties) if solidworks_properties else None
                ))
                
                # Update file's current_version
                cursor.execute(
                    "UPDATE files SET current_version = ?, modified_date = CURRENT_TIMESTAMP WHERE file_id = ?",
                    (next_version, file_id)
                )
                
                conn.commit()
                version_id = cursor.lastrowid
                
                logger.info(f"Created version {next_version} for file_id {file_id}")
                return {
                    "version_id": version_id,
                    "version_number": next_version,
                    "revision_letter": ""
                }
            except Exception as e:
                logger.error(f"Failed to create version: {e}")
                raise
    
    def get_version(self, version_id: int) -> Optional[Dict]:
        """Get version by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM versions WHERE version_id = ?", (version_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_file_versions(self, file_id: int) -> List[Dict]:
        """List all versions of a file"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM versions WHERE file_id = ? ORDER BY version_number DESC",
                (file_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_version(self, file_id: int) -> Optional[Dict]:
        """Get latest version of file"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM versions 
                WHERE file_id = ? 
                ORDER BY version_id DESC 
                LIMIT 1
            """, (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ========================
    # LOCK MANAGEMENT
    # ========================
    
    def acquire_lock(self, file_id: int, user: str, reason: str = "Edit") -> str:
        """Acquire file lock
        
        Args:
            file_id: File to lock
            user: Current user (Windows username)
            reason: Lock reason (Edit, Review, etc.)
            
        Returns:
            session_id (unique identifier for this lock)
            
        Raises:
            Exception if file already locked by different user
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if already locked
            cursor.execute(
                "SELECT locked_by FROM files WHERE file_id = ?",
                (file_id,)
            )
            row = cursor.fetchone()
            if row and row[0] and row[0] != user:
                raise Exception(f"File locked by {row[0]}")
            
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            try:
                # Create lock record
                cursor.execute("""
                    INSERT INTO file_locks (file_id, locked_by, lock_reason, session_id)
                    VALUES (?, ?, ?, ?)
                """, (file_id, user, reason, session_id))
                
                # Update files table
                cursor.execute(
                    "UPDATE files SET locked_by = ?, lock_timestamp = CURRENT_TIMESTAMP WHERE file_id = ?",
                    (user, file_id)
                )
                
                conn.commit()
                logger.info(f"Acquired lock for file_id {file_id}, user {user}, session {session_id}")
                return session_id
            except Exception as e:
                logger.error(f"Failed to acquire lock: {e}")
                raise
    
    def release_lock(self, file_id: int, user: str):
        """Release file lock
        
        Args:
            file_id: File to unlock
            user: Current user (must be lock owner)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Update lock record
                cursor.execute("""
                    UPDATE file_locks 
                    SET lock_release_timestamp = CURRENT_TIMESTAMP 
                    WHERE file_id = ? AND locked_by = ? AND lock_release_timestamp IS NULL
                """, (file_id, user))
                
                # Update files table
                cursor.execute(
                    "UPDATE files SET locked_by = NULL, lock_timestamp = NULL WHERE file_id = ?",
                    (file_id,)
                )
                
                conn.commit()
                logger.info(f"Released lock for file_id {file_id}")
            except Exception as e:
                logger.error(f"Failed to release lock: {e}")
                raise
    
    def get_active_locks(self, max_age_hours: int = 24) -> List[Dict]:
        """Get all active locks (optionally filter by age)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    fl.lock_id, fl.file_id, fl.locked_by, fl.lock_timestamp, fl.session_id,
                    CAST((julianday('now') - julianday(fl.lock_timestamp)) * 24 AS INTEGER) AS hours_locked,
                    f.file_name
                FROM file_locks fl
                JOIN files f ON fl.file_id = f.file_id
                WHERE fl.lock_release_timestamp IS NULL 
                  AND fl.is_stale = 0
                  AND CAST((julianday('now') - julianday(fl.lock_timestamp)) * 24 AS INTEGER) < ?
                ORDER BY fl.lock_timestamp DESC
            """, (max_age_hours,))
            return [dict(row) for row in cursor.fetchall()]
    
    def clean_stale_locks(self, max_age_hours: int = 24) -> int:
        """Release stale locks (not accessed for N hours)
        
        Returns:
            count of locks released
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE file_locks 
                SET is_stale = 1, lock_release_timestamp = CURRENT_TIMESTAMP
                WHERE lock_release_timestamp IS NULL
                  AND CAST((julianday('now') - julianday(lock_timestamp)) * 24 AS INTEGER) > ?
            """, (max_age_hours,))
            
            conn.commit()
            count = cursor.rowcount
            logger.info(f"Cleaned {count} stale locks")
            return count
    
    # ========================
    # LIFECYCLE MANAGEMENT
    # ========================
    
    def promote_version(self, version_id: int, new_state: str, user: str, 
                       note: str = "") -> bool:
        """Promote version to new lifecycle state
        
        Args:
            version_id: Version to promote
            new_state: Target state (Released, Obsolete)
            user: User performing promotion
            note: Promotion note
            
        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Get current version state
                cursor.execute(
                    "SELECT file_id, lifecycle_state, revision_letter FROM versions WHERE version_id = ?",
                    (version_id,)
                )
                row = cursor.fetchone()
                if not row:
                    raise Exception(f"Version {version_id} not found")
                
                file_id, from_state, revision = row[0], row[1], row[2]
                
                # Update version lifecycle
                cursor.execute("""
                    UPDATE versions 
                    SET lifecycle_state = ? 
                    WHERE version_id = ?
                """, (new_state, version_id))
                
                # Log transition
                cursor.execute("""
                    INSERT INTO version_transitions 
                    (file_id, version_id, from_state, to_state, promoted_by, promotion_note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (file_id, version_id, from_state, new_state, user, note))
                
                # Update file lifecycle if this is latest version
                cursor.execute(
                    "SELECT MAX(version_id) FROM versions WHERE file_id = ?",
                    (file_id,)
                )
                if cursor.fetchone()[0] == version_id:
                    cursor.execute(
                        "UPDATE files SET lifecycle_state = ? WHERE file_id = ?",
                        (new_state, file_id)
                    )
                
                conn.commit()
                logger.info(f"Promoted version {version_id} to {new_state}")
                return True
            except Exception as e:
                logger.error(f"Failed to promote version: {e}")
                raise
    
    def freeze_version(self, file_id: int, version_number: int, user: str) -> bool:
        """Freeze version (make read-only) and release lock
        
        Args:
            file_id: File ID
            version_number: Version to freeze
            user: User freezing version
            
        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Check lock ownership
                cursor.execute(
                    "SELECT locked_by FROM file_locks WHERE file_id = ?",
                    (file_id,)
                )
                lock_row = cursor.fetchone()
                if lock_row and lock_row[0] != user:
                    raise Exception(f"File locked by {lock_row[0]}, not {user}")
                
                # Update version state to Released
                cursor.execute("""
                    UPDATE versions 
                    SET state = 'Released'
                    WHERE file_id = ? AND version_number = ?
                """, (file_id, version_number))
                
                # Log freeze action
                cursor.execute("""
                    INSERT INTO access_log
                    (user, action, file_id, details)
                    VALUES (?, ?, ?, ?)
                """, (user, 'freeze_version', file_id, 
                      json.dumps({"version": version_number})))
                
                # Release lock
                cursor.execute(
                    "DELETE FROM file_locks WHERE file_id = ? AND locked_by = ?",
                    (file_id, user)
                )
                
                conn.commit()
                logging.info(f"Version {version_number} frozen by {user}")
                return True
            except Exception as e:
                logging.error(f"Error freezing version: {e}")
                return False
    
    # ========================
    # ASSEMBLY MANAGEMENT
    # ========================
    
    def add_assembly_component(self, assembly_file_id: int, component_file_id: int,
                              component_version: int, quantity: int = 1,
                              instance_names: Optional[List[str]] = None) -> Optional[int]:
        """Add component to assembly BOM
        
        Args:
            assembly_file_id: Parent assembly
            component_file_id: Child component
            component_version: Version of component used
            quantity: Number of instances
            instance_names: List of instance names
            
        Returns:
            relationship_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO assembly_relationships 
                    (assembly_file_id, component_file_id, component_version, instance_count, instance_names)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    assembly_file_id, component_file_id, component_version, quantity,
                    json.dumps(instance_names) if instance_names else None
                ))
                
                conn.commit()
                relationship_id = cursor.lastrowid
                logger.info(f"Added component {component_file_id} to assembly {assembly_file_id}")
                return relationship_id
            except Exception as e:
                logger.error(f"Failed to add assembly component: {e}")
                raise
    
    def get_assembly_bom(self, assembly_file_id: int) -> List[Dict]:
        """Get complete BOM for assembly"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a.relationship_id,
                    f_parent.plm_id AS assembly_plm_id,
                    f_parent.file_name AS assembly_name,
                    f_child.plm_id AS component_plm_id,
                    f_child.file_name AS component_name,
                    a.component_version,
                    a.instance_count,
                    a.insertion_state
                FROM assembly_relationships a
                JOIN files f_parent ON a.assembly_file_id = f_parent.file_id
                JOIN files f_child ON a.component_file_id = f_child.file_id
                WHERE a.assembly_file_id = ?
                ORDER BY f_child.file_name
            """, (assembly_file_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # ACCESS LOGGING
    # ========================
    
    def log_action(self, user: str, action: str, file_id: Optional[int] = None, 
                  project_id: Optional[int] = None, duration_ms: Optional[int] = None, 
                  details: Optional[Dict] = None) -> Optional[int]:
        """Log user action to audit trail
        
        Returns:
            log_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO access_log 
                (user, action, file_id, project_id, duration_ms, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user, action, file_id, project_id, duration_ms,
                json.dumps(details) if details else None
            ))
            conn.commit()
            row_id = cursor.lastrowid
            return row_id if row_id else None
    
    def get_audit_trail(self, file_id: Optional[int] = None, user: Optional[str] = None, 
                       limit: int = 100) -> List[Dict]:
        """Get audit trail"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM access_log WHERE 1=1"
            params = []
            
            if file_id:
                query += " AND file_id = ?"
                params.append(file_id)
            
            if user:
                query += " AND user = ?"
                params.append(user)
            
            query += " ORDER BY action_timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================
    # UTILITY FUNCTIONS
    # ========================
    
    def _get_next_plm_id(self, cursor, prefix: str) -> str:
        """Generate next PLM ID (e.g., PLM-PAR-001)"""
        # Search pattern must include the full PLM- prefix
        search_pattern = f"PLM-{prefix}-%"
        
        cursor.execute(
            f"SELECT MAX(CAST(SUBSTR(plm_id, -3) AS INTEGER)) FROM files WHERE plm_id LIKE ?"
            , (search_pattern,)
        )
        result = cursor.fetchone()
        next_num = (result[0] or 0) + 1
        
        # Also check projects table
        cursor.execute(
            f"SELECT MAX(CAST(SUBSTR(plm_id, -3) AS INTEGER)) FROM projects WHERE plm_id LIKE ?",
            (search_pattern,)
        )
        proj_result = cursor.fetchone()
        proj_num = proj_result[0] or 0
        
        next_num = max(next_num, proj_num) + 1
        return f"PLM-{prefix}-{next_num:03d}"
    
    def validate_vault_integrity(self) -> Dict[str, Any]:
        """Validate vault database integrity
        
        Returns:
            dict with validation results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            results = {
                "project_count": 0,
                "file_count": 0,
                "version_count": 0,
                "orphaned_versions": 0,
                "missing_checksums": 0,
                "stale_locks": 0
            }
            
            # Count tables
            cursor.execute("SELECT COUNT(*) FROM projects WHERE is_active = 1")
            results["project_count"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM files WHERE is_active = 1")
            results["file_count"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM versions")
            results["version_count"] = cursor.fetchone()[0]
            
            # Find orphaned versions (file deleted but versions remain)
            cursor.execute("""
                SELECT COUNT(*) FROM versions v
                WHERE NOT EXISTS (SELECT 1 FROM files f WHERE f.file_id = v.file_id)
            """)
            results["orphaned_versions"] = cursor.fetchone()[0]
            
            # Find missing checksums
            cursor.execute("SELECT COUNT(*) FROM versions WHERE checksum IS NULL")
            results["missing_checksums"] = cursor.fetchone()[0]
            
            # Find stale locks
            cursor.execute("""
                SELECT COUNT(*) FROM file_locks 
                WHERE lock_release_timestamp IS NULL
                  AND CAST((julianday('now') - julianday(lock_timestamp)) * 24 AS INTEGER) > 24
            """)
            results["stale_locks"] = cursor.fetchone()[0]
            
            logger.info(f"Vault integrity check: {results}")
            return results


if __name__ == "__main__":
    # Example usage
    db = PLMDatabase("e:\\PLM_VAULT")
    
    # Create project
    proj = db.create_project("ProjectA", "john.smith", "Bracket assembly project")
    print(f"Created project: {proj}")
    
    # Validate
    integrity = db.validate_vault_integrity()
    print(f"Vault integrity: {integrity}")
