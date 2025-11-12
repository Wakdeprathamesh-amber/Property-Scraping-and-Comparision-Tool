#!/usr/bin/env python3
"""
Start the Property Comparison Tool UI Server

This script starts the FastAPI backend server which serves the UI.
"""

import sys
import uvicorn
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def main():
    """Start the server"""
    print("\n" + "=" * 70)
    print("🏠 Property Comparison Tool - Web UI")
    print("=" * 70)
    print("\n📡 Starting server...")
    print("\n🌐 Access the UI at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    print("\n⚠️  Press CTRL+C to stop the server\n")
    print("=" * 70 + "\n")
    
    # Start uvicorn server
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()


