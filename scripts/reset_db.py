#!/usr/bin/env python3
"""
Reset database - DROPS ALL TABLES AND DATA!
Use with caution.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.database import reset_db

if __name__ == "__main__":
    response = input("⚠️  This will DELETE ALL DATA. Are you sure? (yes/no): ")
    if response.lower() == "yes":
        print("Resetting database...")
        reset_db()
        print("✅ Database reset complete!")
    else:
        print("Cancelled.")
