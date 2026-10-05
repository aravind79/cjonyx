import sqlite3, os
paths=[os.path.join(os.getcwd(),'cjonyx.db'), os.path.join(os.getcwd(),'instance','cjonyx.db')]
for p in paths:
    print('DB:',p)
    if not os.path.exists(p):
        print('  not found')
        continue
    conn=sqlite3.connect(p)
    try:
        cur=conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables=[r[0] for r in cur.fetchall()]
        print('  tables:', tables)
    finally:
        conn.close()
