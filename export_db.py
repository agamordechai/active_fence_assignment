#!/usr/bin/env python3
"""
Script to export reddit_detection.db to CSV and JSON files.
Each table is exported to a separate CSV and JSON file in the data/ directory.
"""

import sqlite3
import csv
import json
from pathlib import Path
from datetime import datetime


def get_tables(cursor):
    """Get all table names from the database."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def export_table_to_csv(cursor, table_name, output_path):
    """Export a single table to CSV."""
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    return len(rows)


def export_table_to_json(cursor, table_name, output_path):
    """Export a single table to JSON."""
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    data = []
    for row in rows:
        row_dict = {}
        for col, val in zip(columns, row):
            # Parse JSON fields that are stored as strings
            if isinstance(val, str) and val.startswith(("{", "[")):
                try:
                    val = json.loads(val)
                except json.JSONDecodeError:
                    pass
            row_dict[col] = val
        data.append(row_dict)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    return len(data)


def main():
    # Paths
    script_dir = Path(__file__).parent
    db_path = script_dir / "data" / "reddit_detection.db"
    output_dir = script_dir / "data" / "exports"

    # Check if database exists
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return 1

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        tables = get_tables(cursor)
        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        print(f"Output directory: {output_dir}")
        print("-" * 50)

        for table in tables:
            # Export to CSV
            csv_path = output_dir / f"{table}.csv"
            csv_count = export_table_to_csv(cursor, table, csv_path)
            print(f"Exported {table} to CSV: {csv_count} rows -> {csv_path.name}")

            # Export to JSON
            json_path = output_dir / f"{table}.json"
            json_count = export_table_to_json(cursor, table, json_path)
            print(f"Exported {table} to JSON: {json_count} rows -> {json_path.name}")
            print()

        print("-" * 50)
        print(f"Export completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Files saved to: {output_dir}")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    exit(main())
