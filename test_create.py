#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test create project with fixed PLM ID"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from database.db import PLMDatabase

vault_path = os.getenv("PLM_VAULT_PATH", r"D:\Anurag\PLM_VAULT")
db = PLMDatabase(vault_path)

try:
    # Try to create a new project
    proj = db.create_project("TestProject_NEW", "TestUser", "Testing new project")
    print(f"✅ SUCCESS! Created project:")
    print(f"   Name: {proj['name']}")
    print(f"   PLM-ID: {proj['plm_id']}")
    print(f"   Project ID: {proj['project_id']}")
except Exception as e:
    print(f"❌ ERROR: {e}")
