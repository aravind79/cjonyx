#!/usr/bin/env python3
"""
Script to ensure the `gallery` table has an `event_id` column in a SQLite DB.
Usage: python scripts/fix_gallery_event_id.py --db cjonyx.db
If no --db provided, defaults to `cjonyx.db` in current directory.
"""
import sqlite3
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--db', default='cjonyx.db', help='Path to SQLite DB file')
args = parser.parse_args()

db_path = args.db

print(f"Opening DB: {db_path}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check if gallery table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gallery';")
row = cur.fetchone()
if not row:
    print("`gallery` table not found — creating table with event_id column.")
    cur.execute('''
        CREATE TABLE gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url TEXT NOT NULL,
            description TEXT,
            created_at DATETIME,
            event_id INTEGER
        );
    ''')
    conn.commit()
    print("gallery table created.")
    conn.close()
    sys.exit(0)

# If gallery exists, check columns
cur.execute("PRAGMA table_info('gallery')")
cols = [r[1] for r in cur.fetchall()]
print('Existing gallery columns:', cols)
if 'event_id' in cols:
    print('`event_id` already present — nothing to do.')
    conn.close()
    sys.exit(0)

# Add the column
print('Adding `event_id` column to gallery table...')
try:
    cur.execute("ALTER TABLE gallery ADD COLUMN event_id INTEGER;")
    conn.commit()
    print('Added event_id column.')
except sqlite3.OperationalError as e:
    print('OperationalError while adding column:', e)
    print('Attempting table rebuild as fallback...')
    # Rebuild table: create new table, copy data, drop old, rename
    cur.execute("PRAGMA foreign_keys=off;")
    conn.commit()
    cur.execute('''
        CREATE TABLE gallery_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url TEXT NOT NULL,
            description TEXT,
            created_at DATETIME,
            event_id INTEGER
        );
    ''')
    cur.execute("INSERT INTO gallery_new (id, image_url, description, created_at) SELECT id, image_url, description, created_at FROM gallery;")
    cur.execute("DROP TABLE gallery;")
    cur.execute("ALTER TABLE gallery_new RENAME TO gallery;")
    cur.execute("PRAGMA foreign_keys=on;")
    conn.commit()
    print('Rebuilt gallery table with event_id column.')

conn.close()
print('Done.')
