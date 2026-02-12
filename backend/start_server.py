#!/usr/bin/env python
"""
Simple Phase 8 Deployment & Server Startup
"""

import os
import sys
import subprocess
from pathlib import Path

# Get the absolute path to the backend directory
backend_dir = Path(__file__).parent.absolute()
os.chdir(backend_dir)

# Add backend directory to Python path
sys.path.insert(0, str(backend_dir))

print("""
╔══════════════════════════════════════════════════════════╗
║       PHASE 8 DEPLOYMENT - SIMPLE STARTUP                ║
╚══════════════════════════════════════════════════════════╝
""")

print("🔧 Step 1: Installing dependencies...")
os.system("pip install -q -r requirements.txt")

print("\n✅ Step 2: Initializing database...")
try:
    from dotenv import load_dotenv
    from app.database.config import engine, Base
    from app.models.cohort_models import *
    
    load_dotenv()
    Base.metadata.create_all(engine)
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"✅ Database initialized with {len(tables)} tables!")
    print(f"   Tables: {', '.join(sorted(tables)[:5])}...")
except Exception as e:
    print(f"⚠️  Database init: {e}")

print("\n🚀 Step 3: Starting FastAPI server...")
print("   Server will run on: http://localhost:8000")
print("   API docs: http://localhost:8000/docs")
print("   ReDoc: http://localhost:8000/redoc")
print("\n   Press Ctrl+C to stop the server\n")

# Start the server
os.system("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
