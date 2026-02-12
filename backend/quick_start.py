#!/usr/bin/env python
"""Quick Phase 8 Launch Script"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.system("python -m uvicorn app.main:app --reload --port 8000")
