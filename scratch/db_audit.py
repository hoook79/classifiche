import sqlite3

conn = sqlite3.connect('radio_reports.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) as tot FROM canzoni_metadati')
tot = cursor.fetchone()['tot']

cursor.execute('''
SELECT 
    SUM(case when codice_siae IS NULL or codice_siae in (\'\', \'-\', \'N/A\') then 1 else 0 end) as empty_siae,
    SUM(case when codice_iswc IS NULL or codice_iswc in (\'\', \'-\', \'N/A\') then 1 else 0 end) as empty_iswc,
    SUM(case when codice_isrc IS NULL or codice_isrc in (\'\', \'-\', \'N/A\') then 1 else 0 end) as empty_isrc,
    SUM(case when compositore IS NULL or compositore in (\'\', \'-\', \'N/A\') then 1 else 0 end) as empty_composer,
    SUM(case when autore IS NULL or autore in (\'\', \'-\', \'N/A\') then 1 else 0 end) as empty_author,
    SUM(case when casa_discografica IS NULL or casa_discografica in (\'\', \'-\', \'N/A\') then 1 else 0 end) as empty_label,
    SUM(case when anno_pubblicazione IS NULL or anno_pubblicazione in (\'\', \'-\', \'N/A\', 0) then 1 else 0 end) as empty_year
FROM canzoni_metadati
''')
row = cursor.fetchone()

print(f"Totale canzoni: {tot}")
print(f"Senza SIAE: {row['empty_siae']} ({row['empty_siae']/tot*100:.2f}%)")
print(f"Senza ISWC: {row['empty_iswc']} ({row['empty_iswc']/tot*100:.2f}%)")
print(f"Senza ISRC: {row['empty_isrc']} ({row['empty_isrc']/tot*100:.2f}%)")
print(f"Senza Compositore: {row['empty_composer']} ({row['empty_composer']/tot*100:.2f}%)")
print(f"Senza Autore: {row['empty_author']} ({row['empty_author']/tot*100:.2f}%)")
print(f"Senza Label: {row['empty_label']} ({row['empty_label']/tot*100:.2f}%)")
print(f"Senza Anno: {row['empty_year']} ({row['empty_year']/tot*100:.2f}%)")

conn.close()
