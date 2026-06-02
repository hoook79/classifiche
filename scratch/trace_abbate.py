import sys
import os

sys.path.append(os.getcwd())
from fetch_years import get_year_from_musicbrainz, get_year_from_itunes, get_year_from_genius, get_year_from_wikipedia

song = "FEDERICA ABBATE - SUPERMAN"
print(f"MusicBrainz year: {get_year_from_musicbrainz(song)}")
print(f"iTunes year: {get_year_from_itunes(song)}")
print(f"Genius year: {get_year_from_genius(song)}")
print(f"Wikipedia year: {get_year_from_wikipedia(song)}")
