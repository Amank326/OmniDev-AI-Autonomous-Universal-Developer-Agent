#!/usr/bin/env python
"""Phase 8 Server Launcher - Fixed Path Handling"""
import sys
import os
from pathlib import Path

# Set up paths
root_dir = Path(__file__).parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

print("""
╔════════════════════════════════════════════════════╗
║      PHASE 8 - PRODUCTION DEPLOYMENT               ║
║       OmniDev AI - Advanced Analytics               ║
╚════════════════════════════════════════════════════╝

🚀 Launching FastAPI Server...
📍 Location: http://localhost:8000
📚 Docs: http://localhost:8000/docs
🔄 Auto-reload: Enabled

""")

# Import and run uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
