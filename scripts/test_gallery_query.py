#!/usr/bin/env python3
import sqlite3
import sys

db = sys.argv[1] if len(sys.argv) > 1 else 'cjonyx.db'
print(f'Checking gallery query on: {db}')
conn = sqlite3.connect(db)
cur = conn.cursor()
try:
    sql = '''SELECT count(*) AS count_1 FROM (SELECT gallery.id AS gallery_id, gallery.image_url AS gallery_image_url, gallery.description AS gallery_description, gallery.created_at AS gallery_created_at, gallery.event_id AS gallery_event_id FROM gallery) AS anon_1'''
    cur.execute(sql)
    r = cur.fetchone()
    print('Query successful, count:', r[0])
except Exception as e:
    print('Query failed:', e)
finally:
    conn.close()
