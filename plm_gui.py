#!/usr/bin/env python3
"""
PLM GUI - Desktop Interface for PLM System
Simple tkinter-based GUI for managing projects, files, versions, and locks
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
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
        
        # Initialize database
        vault_path_str = os.getenv("PLM_VAULT_PATH", r"e:\PLM_VAULT")
        vault_path = Path(vault_path_str)
        if not vault_path.exists():
            messagebox.showerror("Error", f"PLM vault not found at {vault_path_str}\n\nRun SETUP.py first to initialize.")
            sys.exit(1)
        
        self.db = PLMDatabase(str(vault_path))
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
        
        # Create tabs
        self.create_projects_tab()
        self.create_files_tab()
        self.create_versions_tab()
        self.create_locks_tab()
        self.create_audit_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Connected as: {self.current_user}")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=5, pady=2)
    
    def create_projects_tab(self):
        """Projects management tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Projects")
        
        # Button frame
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Create Project", command=self.create_project).pack(side=tk.LEFT, padx=2)
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
    
    def create_versions_tab(self):
        """Versions management tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Versions")
        
        # File selector
        selector_frame = ttk.Frame(frame)
        selector_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(selector_frame, text="File:").pack(side=tk.LEFT, padx=2)
        self.file_combo = ttk.Combobox(selector_frame, state="readonly", width=30)
        self.file_combo.pack(side=tk.LEFT, padx=2)
        self.file_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_versions())
        
        # Action buttons
        ttk.Button(selector_frame, text="Create Version", command=self.create_version).pack(side=tk.LEFT, padx=2)
        ttk.Button(selector_frame, text="Freeze Version", command=self.freeze_version).pack(side=tk.LEFT, padx=2)
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
    
    def create_locks_tab(self):
        """Lock management tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Locks")
        
        # Button frame
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Acquire Lock", command=self.acquire_lock).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Release Lock", command=self.release_lock).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clean Expired", command=self.clean_locks).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_locks).pack(side=tk.LEFT, padx=2)
        
        # Treeview
        columns = ("File", "User", "Acquired", "Expires")
        self.locks_tree = ttk.Treeview(frame, columns=columns, height=20)
        self.locks_tree.heading("#0", text="ID")
        self.locks_tree.column("#0", width=30)
        self.locks_tree.heading("File", text="File Name")
        self.locks_tree.column("File", width=200)
        self.locks_tree.heading("User", text="Locked By")
        self.locks_tree.column("User", width=100)
        self.locks_tree.heading("Acquired", text="Acquired At")
        self.locks_tree.column("Acquired", width=150)
        self.locks_tree.heading("Expires", text="Expires At")
        self.locks_tree.column("Expires", width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.locks_tree.yview)
        self.locks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.locks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_locks()
    
    def create_audit_tab(self):
        """Audit log tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Audit Log")
        
        # Filter frame
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Limit:").pack(side=tk.LEFT, padx=2)
        self.audit_limit = ttk.Combobox(filter_frame, values=["10", "20", "50", "100", "200"], state="readonly", width=5)
        self.audit_limit.set("50")
        self.audit_limit.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(filter_frame, text="Refresh", command=self.refresh_audit).pack(side=tk.LEFT, padx=2)
        
        # Treeview
        columns = ("Timestamp", "User", "Action", "Details")
        self.audit_tree = ttk.Treeview(frame, columns=columns, height=25)
        self.audit_tree.heading("#0", text="ID")
        self.audit_tree.column("#0", width=30)
        self.audit_tree.heading("Timestamp", text="Timestamp")
        self.audit_tree.column("Timestamp", width=150)
        self.audit_tree.heading("User", text="User")
        self.audit_tree.column("User", width=100)
        self.audit_tree.heading("Action", text="Action")
        self.audit_tree.column("Action", width=150)
        self.audit_tree.heading("Details", text="Details")
        self.audit_tree.column("Details", width=400)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.audit_tree.yview)
        self.audit_tree.configure(yscrollcommand=scrollbar.set)
        
        self.audit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_audit()
    
    # Refresh methods
    def refresh_projects(self):
        """Refresh projects list"""
        self.projects_tree.delete(*self.projects_tree.get_children())
        projects = self.db.list_projects()
        
        for proj in projects:
            self.projects_tree.insert("", "end", text=proj["name"],
                values=(proj["plm_id"], proj["owner"], proj["created_date"], "Yes"))
        
        # Update combo if it exists
        if self.project_combo is not None:
            self.project_combo["values"] = [p["name"] for p in projects]
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
        for f in files:
            locked = f.get("locked_by", "")
            self.files_tree.insert("", "end", text=f["file_name"],
                values=(f["plm_id"], f["file_type"], locked, f.get("lifecycle_state", "In-Work")))
        
        # Update combo if it exists
        if self.file_combo is not None:
            self.file_combo["values"] = [f["file_name"] for f in files]
    
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
    
    def refresh_locks(self):
        """Refresh locks list"""
        self.locks_tree.delete(*self.locks_tree.get_children())
        
        locks = self.db.get_active_locks()
        for lock in locks:
            file = self.db.get_file(lock["file_id"])
            self.locks_tree.insert("", "end", text=str(lock["id"]),
                values=(file["file_name"] if file else "?", lock["locked_by"],
                       lock["locked_at"], lock["expires_at"]))
    
    def refresh_audit(self):
        """Refresh audit log"""
        self.audit_tree.delete(*self.audit_tree.get_children())
        
        if self.audit_limit is None:
            return
        
        limit = int(str(self.audit_limit.get()))
        logs = self.db.get_audit_trail(limit=limit)
        
        for log in logs:
            self.audit_tree.insert("", "end", text=str(log["id"]),
                values=(log["timestamp"], log["user"], log["action"], log.get("details", "")))
    
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
                self.db.create_project(name, self.current_user, desc)
                messagebox.showinfo("Success", f"Project '{name}' created")
                self.refresh_projects()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Create", command=save).grid(row=2, column=1, padx=5, pady=10, sticky="e")
    
    def create_version(self):
        """Create new version dialog"""
        if self.file_combo is None:
            messagebox.showerror("Error", "Files tab not initialized")
            return
        
        file_name = self.file_combo.get()
        if not file_name:
            messagebox.showerror("Error", "Select a file first")
            return
        
        note = simpledialog.askstring("Create Version", "Change note (optional):", parent=self.root)
        if note is None:
            return
        
        try:
            # Find file
            if self.project_combo is None:
                raise Exception("Project selector not initialized")
            
            projects = self.db.list_projects()
            if not projects:
                raise Exception("No projects found")
            project_name = self.project_combo.get()
            project = next((p for p in projects if p["name"] == project_name), None)
            if not project:
                raise Exception("Project not found")
            files = self.db.list_project_files(project["project_id"])
            if not files:
                raise Exception("No files found")
            file = next((f for f in files if f["file_name"] == file_name), None)
            if not file:
                raise Exception("File not found")
            
            # Create version
            vault_path = file.get("vault_path", "")
            self.db.create_version(file["file_id"], vault_path, change_note=note)
            
            messagebox.showinfo("Success", "Version created")
            self.refresh_versions()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def freeze_version(self):
        """Freeze selected version"""
        selection = self.versions_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Select a version")
            return
        
        if self.file_combo is None:
            messagebox.showerror("Error", "Files tab not initialized")
            return
        
        file_name = self.file_combo.get()
        item = selection[0]
        values = self.versions_tree.item(item, "values")
        version_num = int(values[0])
        
        if messagebox.askyesno("Confirm", f"Freeze version v{version_num:03d}? (Read-Only)"):
            try:
                if self.project_combo is None:
                    raise Exception("Project selector not initialized")
                
                projects = self.db.list_projects()
                if not projects:
                    raise Exception("No projects found")
                project_name = self.project_combo.get()
                project = next((p for p in projects if p["name"] == project_name), None)
                if not project:
                    raise Exception("Project not found")
                files = self.db.list_project_files(project["project_id"])
                if not files:
                    raise Exception("No files found")
                file = next((f for f in files if f["file_name"] == file_name), None)
                if not file:
                    raise Exception("File not found")
                
                self.db.freeze_version(file["file_id"], version_num, self.current_user)
                messagebox.showinfo("Success", f"Version v{version_num:03d} frozen")
                self.refresh_versions()
                self.refresh_locks()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def acquire_lock(self):
        """Acquire lock for file"""
        if self.file_combo is None:
            messagebox.showerror("Error", "Files tab not initialized")
            return
        
        file_name = self.file_combo.get()
        if not file_name:
            messagebox.showerror("Error", "Select a file first")
            return
        
        try:
            if self.project_combo is None:
                raise Exception("Project selector not initialized")
            
            projects = self.db.list_projects()
            if not projects:
                raise Exception("No projects found")
            project_name = self.project_combo.get()
            project = next((p for p in projects if p["name"] == project_name), None)
            if not project:
                raise Exception("Project not found")
            files = self.db.list_project_files(project["project_id"])
            if not files:
                raise Exception("No files found")
            file = next((f for f in files if f["file_name"] == file_name), None)
            if not file:
                raise Exception("File not found")
            
            self.db.acquire_lock(file["file_id"], self.current_user, "Edit")
            messagebox.showinfo("Success", "Lock acquired (24 hours)")
            self.refresh_locks()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def release_lock(self):
        """Release lock for file"""
        if self.file_combo is None:
            messagebox.showerror("Error", "Files tab not initialized")
            return
        
        file_name = self.file_combo.get()
        if not file_name:
            messagebox.showerror("Error", "Select a file first")
            return
        
        try:
            if self.project_combo is None:
                raise Exception("Project selector not initialized")
            
            projects = self.db.list_projects()
            if not projects:
                raise Exception("No projects found")
            project_name = self.project_combo.get()
            project = next((p for p in projects if p["name"] == project_name), None)
            if not project:
                raise Exception("Project not found")
            files = self.db.list_project_files(project["project_id"])
            if not files:
                raise Exception("No files found")
            file = next((f for f in files if f["file_name"] == file_name), None)
            if not file:
                raise Exception("File not found")
            
            self.db.release_lock(file["file_id"], self.current_user)
            messagebox.showinfo("Success", "Lock released")
            self.refresh_locks()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def clean_locks(self):
        """Clean expired locks"""
        try:
            self.db.clean_stale_locks()
            messagebox.showinfo("Success", "Expired locks cleaned")
            self.refresh_locks()
        except Exception as e:
            messagebox.showerror("Error", str(e))


def main():
    root = tk.Tk()
    app = PLMGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
