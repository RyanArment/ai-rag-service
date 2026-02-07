#!/usr/bin/env python3
"""
Initialize database - creates all tables.
Run this after setting up your database.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.database import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("✅ Database initialized successfully!")
    print("\nTables created:")
    print("  - users")
    print("  - documents")
    print("  - document_chunks")
    print("  - queries")
    print("  - api_keys")
    print("  - sec_companies")
    print("  - sec_filings")
    print("  - filing_cross_references")
