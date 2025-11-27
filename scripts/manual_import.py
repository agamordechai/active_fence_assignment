#!/usr/bin/env python3
"""
Manual data import script - Run this to populate the database
Usage: python3 manual_import.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.database import init_db
from src.import_data import import_all_from_directory

if __name__ == "__main__":
    print("🔧 Initializing database...")
    init_db()
    print("✅ Database initialized")

    print("\n📥 Importing data...")
    import_all_from_directory("data/processed")
    print("\n✅ Import complete!")

    print("\n📊 Checking results...")
    from src.database.database import get_db_context
    from src.database import crud

    with get_db_context() as db:
        stats = crud.get_statistics(db)
        print(f"   Posts: {stats['total_posts']}")
        print(f"   Users: {stats['total_users']}")
        print(f"   High-risk posts: {stats['high_risk_posts']}")
        print(f"   High-risk users: {stats['high_risk_users']}")

    print("\n🎉 Database is populated! Start the API and check http://localhost:8000/statistics")

