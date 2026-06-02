import os
import subprocess
import sys
import time
import datetime

# Define the directory for script outputs
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script_outputs')
os.makedirs(output_dir, exist_ok=True)

def run_script(script_name):
    print(f"\n--- Esecuzione di {script_name} ---", flush=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    stdout_file = os.path.join(output_dir, f"{script_name.replace('.py', '')}_{timestamp}_stdout.log")
    stderr_file = os.path.join(output_dir, f"{script_name.replace('.py', '')}_{timestamp}_stderr.log")

    try:
        # Usa Popen per mostrare l'output in tempo reale sulla console
        # e salvarlo contemporaneamente nel file di log
        with open(stdout_file, 'w', encoding='utf-8') as f_stdout, \
             open(stderr_file, 'w', encoding='utf-8') as f_stderr:

            process = subprocess.Popen(
                ['python', '-u', script_name],  # -u = unbuffered output
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # Leggi stdout in tempo reale: mostra a schermo E salva nel file
            stdout_lines = []
            for line in process.stdout:
                line_stripped = line.rstrip('\n')
                print(line_stripped, flush=True)   # console in tempo reale
                f_stdout.write(line)               # file di log
                stdout_lines.append(line_stripped)

            # Aspetta la fine e cattura stderr
            _, stderr_data = process.communicate()
            if stderr_data:
                f_stderr.write(stderr_data)

        return_code = process.returncode

        if return_code != 0:
            print(f"\n[ATTENZIONE] {script_name} uscito con codice {return_code}", flush=True)
            if stderr_data and stderr_data.strip():
                print("--- STDERR ---", flush=True)
                print(stderr_data[:2000], flush=True)  # Mostra solo i primi 2000 char
        else:
            # Rimuovi file stderr vuoto
            if os.path.getsize(stderr_file) == 0:
                os.remove(stderr_file)
            print(f"[OK] {script_name} completato.", flush=True)

    except Exception as e:
        print(f"[ERRORE] Errore imprevisto durante {script_name}: {e}", flush=True)

if __name__ == "__main__":
    start_time = time.time()

    # 1. Aggiornamento Radio Divina
    run_script('update_radio_playlist.py')

    # 2. Aggiornamento Radio Subasio
    run_script('update_subasio_playlist.py')

    # 3. Aggiornamento Radio Mitology
    run_script('update_mitology_playlist.py')

    # 4. Aggiornamento Radio Nostalgia Toscana
    run_script('update_nostalgia_playlist.py')

    # 5. Aggiornamento Radio Toscana
    run_script('update_toscana_playlist.py')

    # 5.5. Aggiornamento Radio Italia, RDS, RTL 102.5
    run_script('update_new_playlists.py')

    # 6. Recupero anni mancanti
    run_script('fetch_years.py')

    # 6.5. Recupero radio date da EarOne
    run_script('scrape_earone_radiodates.py')

    # 7. Recupero anteprime audio (iTunes + Deezer) — aggiorna solo i nuovi brani
    run_script('fetch_previews.py')

    # 8. Rigenera l'HTML con tutti i dati aggiornati
    run_script('genera_html.py')

    end_time = time.time()
    elapsed = round(end_time - start_time, 2)
    print(f"\nAggiornamento quotidiano completato in {elapsed} secondi.")
    input("Premi INVIO per uscire...")
