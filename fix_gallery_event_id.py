import sqlite3
import os

candidates = [os.path.join(os.getcwd(), 'cjonyx.db'), os.path.join(os.getcwd(), 'instance', 'cjonyx.db')]

for db_path in candidates:
    print('\nChecking DB:', db_path)
    if not os.path.exists(db_path):
        print('  not found')
        continue
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gallery'")
        if not cur.fetchone():
            print('  gallery table not found')
            continue
        print('  gallery table exists')
        # Check columns
        cur = conn.execute("PRAGMA table_info('gallery')")
        cols = [r[1] for r in cur.fetchall()]
        print('  columns:', cols)
        if 'event_id' in cols:
            print('  event_id already present')
            continue
        # Add column
        print('  Adding event_id column...')
        conn.execute("ALTER TABLE gallery ADD COLUMN event_id INTEGER")
        conn.commit()
        print('  event_id added successfully')
    except Exception as e:
        print('  Error:', e)
    finally:
        conn.close()

print('\nDone')
