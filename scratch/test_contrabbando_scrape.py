import sys
import os

sys.path.append(os.getcwd())
from scrape_earone_radiodates import search_earone_via_web

song = "CRISTIANO MALGIOGLIO - Amore di Contrabbando"
print(f"Scraping web search for: {song}")
date = search_earone_via_web(song)
print(f"Result: {date}")
