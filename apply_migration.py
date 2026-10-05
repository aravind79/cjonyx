# Small helper to apply the event_id column to the SQLite DB if it doesn't exist
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'cjonyx.db')

def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print('Database not found at', DB_PATH)
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        if column_exists(conn, 'gallery', 'event_id'):
            print('Column event_id already exists on gallery table.')
        else:
            print('Adding event_id column to gallery table...')
            conn.execute("ALTER TABLE gallery ADD COLUMN event_id INTEGER")
            conn.commit()
            print('Done.')
    finally:
        conn.close()
