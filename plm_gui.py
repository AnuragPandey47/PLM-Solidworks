#!/usr/bin/env python3
"""
PLM GUI - Desktop Interface for PLM System
Simple tkinter-based GUI for managing projects, files, versions, and locks
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))
from database.db import PLMDatabase


class PLMGUI:
    """PLM Desktop GUI Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PLM System - Desktop Manager")
        self.root.geometry("1200x700")
        
        # Find vault path from config.json or environment variable
        vault_path_str = self._find_vault_path()
        self.vault_root = Path(vault_path_str)
        if not self.vault_root.exists():
            messagebox.showerror("Error", f"PLM vault not found at {vault_path_str}\n\nRun SETUP.py first to initialize.")
            sys.exit(1)
        
        self.db = PLMDatabase(str(self.vault_root))
        self.current_user = os.getenv("USERNAME", "Unknown")
        
        # Initialize combo boxes as None (will be created in tabs)
        self.project_combo = None
        self.file_combo = None
        self.audit_limit = None
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize tabs
        self.__init_tabs()
        
    def _find_vault_path(self) -> str:
        """Find vault path from config.json or environment variable"""
        # Check common vault locations
        search_paths = [
            Path("D:/Anurag/PLM_VAULT/config.json"),
            Path("E:/PLM_VAULT/config.json"),
            Path(os.getenv("PLM_VAULT_PATH", "")) / "config.json" if os.getenv("PLM_VAULT_PATH") else None
        ]
        
        for config_path in search_paths:
            if config_path and config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        return config.get("vault_path", "")
                except Exception:
                    continue
        
        # Fallback to environment variable or default
        return os.getenv("PLM_VAULT_PATH", r"e:\PLM_VAULT")
    
    def __init_tabs(self):
        """Initialize GUI tabs after database is ready"""
        # Create tabs
        self.create_projects_tab()
        self.create_files_tab()
        self.create_history_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Connected as: {self.current_user}")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=5, pady=2)
    
    def create_projects_tab(self):
        """Projects management tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Projects")
        
        # Button frame
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Create Project", command=self.create_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete Project", command=self.delete_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_projects).pack(side=tk.LEFT, padx=2)
        
        # Treeview
        columns = ("PLM ID", "Owner", "Created", "Active")
        self.projects_tree = ttk.Treeview(frame, columns=columns, height=20)
        self.projects_tree.heading("#0", text="Project Name")
        self.projects_tree.column("#0", width=200)
        self.projects_tree.heading("PLM ID", text="PLM ID")
        self.projects_tree.column("PLM ID", width=100)
        self.projects_tree.heading("Owner", text="Owner")
        self.projects_tree.column("Owner", width=100)
        self.projects_tree.heading("Created", text="Created")
        self.projects_tree.column("Created", width=150)
        self.projects_tree.heading("Active", text="Active")
        self.projects_tree.column("Active", width=50)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=scrollbar.set)
        
        self.projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_projects()
    
    def create_files_tab(self):
        """Files management tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Files")
        
        # Project selector
        selector_frame = ttk.Frame(frame)
        selector_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(selector_frame, text="Project:").pack(side=tk.LEFT, padx=2)
        self.project_combo = ttk.Combobox(selector_frame, state="readonly", width=30)
        self.project_combo.pack(side=tk.LEFT, padx=2)
        self.project_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_files())
        
        ttk.Button(selector_frame, text="Refresh", command=self.refresh_files).pack(side=tk.LEFT, padx=2)
        
        # Treeview
        columns = ("PLM ID", "Type", "Locked By", "State")
        self.files_tree = ttk.Treeview(frame, columns=columns, height=20)
        self.files_tree.heading("#0", text="File Name")
        self.files_tree.column("#0", width=200)
        self.files_tree.heading("PLM ID", text="PLM ID")
        self.files_tree.column("PLM ID", width=100)
        self.files_tree.heading("Type", text="Type")
        self.files_tree.column("Type", width=80)
        self.files_tree.heading("Locked By", text="Locked By")
        self.files_tree.column("Locked By", width=100)
        self.files_tree.heading("State", text="State")
        self.files_tree.column("State", width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_projects()
    
    def create_history_tab(self):
        """Version history tab (read-only)"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="History")
        
        # File selector
        selector_frame = ttk.Frame(frame)
        selector_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(selector_frame, text="File:").pack(side=tk.LEFT, padx=2)
        self.file_combo = ttk.Combobox(selector_frame, state="readonly", width=30)
        self.file_combo.pack(side=tk.LEFT, padx=2)
        self.file_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_versions())
        
        ttk.Button(selector_frame, text="Refresh", command=self.refresh_versions).pack(side=tk.LEFT, padx=2)
        
        # Treeview
        columns = ("Version", "State", "Author", "Created", "Note")
        self.versions_tree = ttk.Treeview(frame, columns=columns, height=20)
        self.versions_tree.heading("#0", text="v")
        self.versions_tree.column("#0", width=30)
        self.versions_tree.heading("Version", text="Number")
        self.versions_tree.column("Version", width=60)
        self.versions_tree.heading("State", text="State")
        self.versions_tree.column("State", width=100)
        self.versions_tree.heading("Author", text="Author")
        self.versions_tree.column("Author", width=100)
        self.versions_tree.heading("Created", text="Created")
        self.versions_tree.column("Created", width=150)
        self.versions_tree.heading("Note", text="Change Note")
        self.versions_tree.column("Note", width=300)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.versions_tree.yview)
        self.versions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.versions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    
    # Refresh methods
    def refresh_projects(self):
        """Refresh projects list"""
        self.projects_tree.delete(*self.projects_tree.get_children())
        projects = self.db.list_projects()
        
        valid_projects = []
        for proj in projects:
            # Only show projects that exist on disk
            proj_path = Path(proj.get("vault_path", ""))
            if proj_path.exists():
                created = proj.get("created_date", "N/A")
                self.projects_tree.insert("", "end", text=proj["name"],
                    values=(proj["plm_id"], proj.get("owner", ""), created, "Yes"))
                valid_projects.append(proj)
        
        # Update combo if it exists
        if self.project_combo is not None:
            self.project_combo["values"] = [p["name"] for p in valid_projects]
        if self.file_combo is not None:
            self.file_combo["values"] = []
    
    def refresh_files(self):
        """Refresh files list"""
        self.files_tree.delete(*self.files_tree.get_children())
        
        if self.project_combo is None:
            return
        
        project_name = self.project_combo.get()
        if not project_name:
            return
        
        projects = self.db.list_projects()
        if not projects:
            return
        project = next((p for p in projects if p["name"] == project_name), None)
        if not project:
            return
        
        files = self.db.list_project_files(project["project_id"])
        valid_files = []
        for f in files:
            # Check if file exists in new structure: Parts/FileName/part_meta.json
            file_folder = Path(f["vault_path"])
            metadata_file = file_folder / "part_meta.json"
            if metadata_file.exists():
                locked = f.get("locked_by", "")
                state = f.get("file_state", "Working")
                self.files_tree.insert("", "end", text=f["file_name"],
                    values=(f["plm_id"], f["file_type"], locked, state))
                valid_files.append(f)
        
        # Update combo if it exists
        if self.file_combo is not None:
            self.file_combo["values"] = [f["file_name"] for f in valid_files]
    
    def refresh_versions(self):
        """Refresh versions list"""
        self.versions_tree.delete(*self.versions_tree.get_children())
        
        if self.file_combo is None:
            return
        
        file_name = self.file_combo.get()
        if not file_name:
            return
        
        # Find file
        if self.project_combo is None:
            return
        
        projects = self.db.list_projects()
        if not projects:
            return
        project_name = self.project_combo.get()
        project = next((p for p in projects if p["name"] == project_name), None)
        if not project:
            return
        
        files = self.db.list_project_files(project["project_id"])
        if not files:
            return
        file = next((f for f in files if f["file_name"] == file_name), None)
        if not file:
            return
        
        versions = self.db.list_file_versions(file["file_id"])
        for v in versions:
            self.versions_tree.insert("", "end", text=f"v{v.get('version_number', 0):03d}",
                values=(v.get("version_number"), v.get("lifecycle_state", "In-Work"), 
                       v.get("author", ""), v.get("created_timestamp", ""), 
                       v.get("change_note", "")))
    
    # Action methods
    def create_project(self):
        """Create new project dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Project")
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="Project Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        desc_text = tk.Text(dialog, width=30, height=4)
        desc_text.grid(row=1, column=1, padx=5, pady=5)
        
        def save():
            name = name_entry.get().strip()
            desc = desc_text.get("1.0", "end").strip()
            
            if not name:
                messagebox.showerror("Error", "Project name required")
                return
            
            try:
                # Check if project already exists
                existing_projects = self.db.list_projects()
                if any(p["name"].lower() == name.lower() for p in existing_projects):
                    messagebox.showerror("Error", f"Project '{name}' already exists")
                    return
                
                # Create project in database
                result = self.db.create_project(name, self.current_user, desc)
                
                # Create project folder structure on disk
                project_path = self.vault_root / "Projects" / name
                project_path.mkdir(parents=True, exist_ok=True)
                
                # Create Working/Parts subfolder
                working_parts = project_path / "Working" / "Parts"
                working_parts.mkdir(parents=True, exist_ok=True)
                
                # Create Parts subfolder (for versions)
                parts_folder = project_path / "Parts"
                parts_folder.mkdir(parents=True, exist_ok=True)
                
                messagebox.showinfo("Success", f"Project '{name}' created")
                self.refresh_projects()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Create", command=save).grid(row=2, column=1, padx=5, pady=10, sticky="e")
    
    def delete_project(self):
        """Delete selected project"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a project to delete")
            return
        
        item = selection[0]
        project_name = self.projects_tree.item(item, "text")
        
        # Confirm deletion
        if messagebox.askyesno("Confirm", f"Delete project '{project_name}'?\nThis will remove the project folder and all files."):
            try:
                # Get project from database
                projects = self.db.list_projects()
                project = next((p for p in projects if p["name"] == project_name), None)
                
                if not project:
                    messagebox.showerror("Error", f"Project '{project_name}' not found")
                    return
                
                project_id = project["project_id"]
                project_path = Path(project["vault_path"])
                
                # Delete from database
                conn = sqlite3.connect(self.db.db_path)
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Get all files in project
                cursor.execute("SELECT file_id FROM files WHERE project_id = ?", (project_id,))
                file_ids = [row[0] for row in cursor.fetchall()]
                
                # Delete related data
                for file_id in file_ids:
                    cursor.execute("DELETE FROM file_locks WHERE file_id = ?", (file_id,))
                    cursor.execute("DELETE FROM assembly_relationships WHERE assembly_file_id = ? OR component_file_id = ?", (file_id, file_id))
                    cursor.execute("DELETE FROM version_transitions WHERE version_id IN (SELECT version_id FROM versions WHERE file_id = ?)", (file_id,))
                    cursor.execute("DELETE FROM versions WHERE file_id = ?", (file_id,))
                
                cursor.execute("DELETE FROM access_log WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM files WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
                
                conn.commit()
                conn.close()
                
                # Delete folder from disk if it exists
                if project_path.exists():
                    import shutil
                    shutil.rmtree(project_path)
                
                messagebox.showinfo("Success", f"Project '{project_name}' deleted")
                self.refresh_projects()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete project: {str(e)}")
    
    


def main():
    root = tk.Tk()
    app = PLMGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
