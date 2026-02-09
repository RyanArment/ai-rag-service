#!/usr/bin/env python3
"""
Add missing error_message column to queries table.
Safe to run multiple times.
"""
import sys
from pathlib import Path
from sqlalchemy import inspect, text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.database import engine


def main() -> None:
    inspector = inspect(engine)
    if "queries" not in inspector.get_table_names():
        print("queries table not found; run init_db first.")
        return

    columns = {col["name"] for col in inspector.get_columns("queries")}
    if "error_message" in columns:
        print("✅ queries.error_message already exists.")
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE queries ADD COLUMN error_message TEXT"))
    print("✅ Added queries.error_message column.")


if __name__ == "__main__":
    main()
