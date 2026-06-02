import json
import os

def merge_json(src_path, dst_path):
    if not os.path.exists(src_path):
        print(f"Sorgente {src_path} non trovata.")
        return
    if not os.path.exists(dst_path):
        print(f"Destinazione {dst_path} non trovata, copio sorgente.")
        if os.path.exists(src_path):
            with open(src_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            with open(dst_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        return

    with open(src_path, 'r', encoding='utf-8') as f:
        src_data = json.load(f)
    with open(dst_path, 'r', encoding='utf-8') as f:
        dst_data = json.load(f)

    # Crea set di UID per evitare duplicati
    def get_uid(item):
        return f"{item['song']}|{item['date']}|{item['time']}"

    seen = {get_uid(item) for item in dst_data}
    added = 0
    for item in src_data:
        uid = get_uid(item)
        if uid not in seen:
            dst_data.append(item)
            seen.add(uid)
            added += 1
    
    with open(dst_path, 'w', encoding='utf-8') as f:
        json.dump(dst_data, f, indent=2, ensure_ascii=False)
    
    print(f"Uniti {added} nuovi brani da {src_path} a {dst_path}.")

def merge_json_cache(src_path, dst_path):
    if not os.path.exists(src_path): return
    with open(src_path, 'r', encoding='utf-8') as f: src_cache = json.load(f)
    if os.path.exists(dst_path):
        with open(dst_path, 'r', encoding='utf-8') as f: dst_cache = json.load(f)
    else:
        dst_cache = {}
    
    added = 0
    for k, v in src_cache.items():
        if k not in dst_cache or (dst_cache[k] == "N/A" and v != "N/A"):
            dst_cache[k] = v
            added += 1
    
    with open(dst_path, 'w', encoding='utf-8') as f:
        json.dump(dst_cache, f, indent=2, ensure_ascii=False)
    print(f"Aggiornata cache anni: {added} nuovi inserimenti in {dst_path}.")

if __name__ == "__main__":
    # Unisci Radio Divina
    merge_json('radio_divina_history.json', 'RadioDivina/radio_divina_history.json')
    # Unisci Radio Subasio
    merge_json('radio_subasio_history.json', 'RadioSubasio/radio_subasio_history.json')
    # Unisci Cache anni
    merge_json_cache('song_years_cache.json', 'RadioSubasio/song_years_cache.json')
