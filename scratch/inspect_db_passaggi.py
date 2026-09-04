import sqlite3

conn = sqlite3.connect('radio_reports.db')
c = conn.cursor()
c.execute("SELECT id_radio, COUNT(*), MIN(data), MAX(data) FROM passaggi GROUP BY id_radio")
rows = c.fetchall()
for row in rows:
    print(f"Radio {row[0]:20s}: {row[1]:6d} rows, from {row[2]} to {row[3]}")

conn.close()
