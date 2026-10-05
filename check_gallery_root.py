import sqlite3, os
p = os.path.join(os.getcwd(), 'cjonyx.db')
print('DB:', p)
if not os.path.exists(p):
    print('DB not found')
    raise SystemExit(1)
conn = sqlite3.connect(p)
try:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gallery'")
    if not cur.fetchone():
        print('gallery table: NOT FOUND')
    else:
        cur2 = conn.execute("PRAGMA table_info('gallery')")
        cols = [r[1] for r in cur2.fetchall()]
        print('gallery columns:', cols)
finally:
    conn.close()
