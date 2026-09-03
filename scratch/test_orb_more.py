import requests
from bs4 import BeautifulSoup

def test_orb(slug, label):
    url = f"https://onlineradiobox.com/it/{slug}/playlist/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select('table.tablelist-schedule tr')
        print(f"ORB {label} ({slug}): Status {r.status_code}, Found {len(rows)} tracks")
        if len(rows) > 0:
            song_el = rows[0].select_one('.track_history_item a')
            time_el = rows[0].select_one('.time--schedule')
            print(f"  Example: {time_el.get_text(strip=True) if time_el else ''} - {song_el.get_text(strip=True) if song_el else ''}")
    except Exception as e:
        print(f"Error ORB {label} ({slug}): {e}")

if __name__ == "__main__":
    # Test Birikina
    test_orb('birikina', 'Birikina (birikina)')
    test_orb('radiobirikina', 'Birikina (radiobirikina)')
    
    # Test Bruno
    test_orb('bruno', 'Bruno (bruno)')
    test_orb('radiobruno', 'Bruno (radiobruno)')
    
    # Test Kiss Kiss
    test_orb('kisskiss', 'Kiss Kiss (kisskiss)')
    test_orb('kisskisshit', 'Kiss Kiss (kisskisshit)')
    
    # Test m2o
    test_orb('m2o', 'm2o (m2o)')
    test_orb('radiom2o', 'm2o (radiom2o)')
    test_orb('m2oradio', 'm2o (m2oradio)')
    
    # Test Proposta Aosta
    test_orb('radiopropostaaosta', 'Proposta Aosta (radiopropostaaosta)')
    test_orb('radioproposta', 'Proposta Aosta (radioproposta)')
    
    # Test CRT
    test_orb('radiocrt', 'CRT (radiocrt)')
    test_orb('crt', 'CRT (crt)')
    test_orb('crtradio', 'CRT (crtradio)')
