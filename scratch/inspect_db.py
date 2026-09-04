import sqlite3

conn = sqlite3.connect('radio_reports.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print('Tables in radio_reports.db:', tables)
for t in tables:
    tname = t[0]
    c.execute(f"PRAGMA table_info('{tname}')")
    cols = [col[1] for col in c.fetchall()]
    c.execute(f"SELECT COUNT(*) FROM '{tname}'")
    cnt = c.fetchone()[0]
    print(f" Table {tname}: {cnt} rows, cols = {cols}")

conn.close()
