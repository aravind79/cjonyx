"""
Apply `allow_late_registration` column to any local SQLite DBs the project might use.
This script attempts to add the column to both `cjonyx.db` in repo root and `instance/cjonyx.db`.
"""
import sqlite3
import os

candidates = [os.path.join(os.getcwd(), 'cjonyx.db'), os.path.join(os.getcwd(), 'instance', 'cjonyx.db')]

for db_path in candidates:
    if not os.path.exists(db_path):
        print('DB not found:', db_path)
        continue
    print('Checking DB:', db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("PRAGMA table_info('event')")
        cols = [r[1] for r in cur.fetchall()]
        if 'allow_late_registration' in cols:
            print('  Column already exists on', db_path)
            continue
        print('  Adding column allow_late_registration to event...')
        # SQLite supports simple ALTER TABLE ADD COLUMN
        conn.execute("ALTER TABLE event ADD COLUMN allow_late_registration BOOLEAN DEFAULT 0")
        conn.commit()
        print('  Done for', db_path)
    except Exception as e:
        print('  Error updating', db_path, e)
    finally:
        conn.close()
