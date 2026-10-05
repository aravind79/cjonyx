import sqlite3
import os

DB = os.path.join(os.getcwd(), 'cjonyx.db')
print('DB path:', DB)
if not os.path.exists(DB):
    print('Database not found:', DB)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
try:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gallery'")
    if cur.fetchone():
        print('gallery table already exists in root DB')
    else:
        print('Creating gallery table in root DB...')
        conn.execute('''
            CREATE TABLE gallery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_url TEXT NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT (datetime('now')),
                event_id INTEGER
            )
        ''')
        conn.commit()
        print('gallery table created with event_id column')
finally:
    conn.close()
