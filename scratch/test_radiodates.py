import sys
sys.path.append(r'c:\Users\Jonny\Desktop\REPORT CANZONI RADIO')

from scrape_earone_radiodates import search_earone_via_web

print("=== AVVIO TEST INTEGRATO DI RICERCA WEB RADIO DATES (IMPORTATO) ===")

song = "MARCO MASINI - E poi ti ho visto cadere"
print(f"\nRicerca per: '{song}'")
res = search_earone_via_web(song)
print(f"-> RISULTATO OTTENUTO: {res}")
