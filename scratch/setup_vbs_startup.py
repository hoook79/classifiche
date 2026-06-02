import os
import subprocess
import sys
import time

# 1. Definisci percorsi
current_dir = r"C:\Users\Jonny\Desktop\REPORT CANZONI RADIO"
server_script = os.path.join(current_dir, "server.py")
startup_dir = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")

vbs_startup_path = os.path.join(startup_dir, "ServerClassificheRadio.vbs")
vbs_local_path = os.path.join(current_dir, "avvia_server_silente.vbs")

# Risolvi python.exe assoluto
python_exe = sys.executable
print(f"Percorso assoluto Python: {python_exe}")

# 2. Contenuto del file VBScript con percorso assoluto e virgolette doppie corrette
# Esegue python.exe in modalità completamente invisibile (WindowStyle = 0)
vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """{python_exe}"" ""{server_script}""", 0, False
'''

# 3. Rimuovi la vecchia scorciatoia .lnk se esiste
old_lnk = os.path.join(startup_dir, "ServerClassificheRadio.lnk")
if os.path.exists(old_lnk):
    try:
        os.remove(old_lnk)
        print(f"Rimosso vecchio shortcut LNK: {old_lnk}")
    except Exception as e:
        print(f"Errore rimozione vecchio shortcut: {e}")

# 4. Scrivi il VBScript nella cartella Startup
try:
    with open(vbs_startup_path, 'w', encoding='utf-8') as f:
        f.write(vbs_content)
    print(f"Creato script di avvio automatico silente VBS in Startup: {vbs_startup_path}")
except Exception as e:
    print(f"Errore creazione script in Startup: {e}")

# 5. Scrivi il VBScript locale nella cartella del progetto
try:
    with open(vbs_local_path, 'w', encoding='utf-8') as f:
        f.write(vbs_content)
    print(f"Creato script locale VBS per l'avvio manuale silente: {vbs_local_path}")
except Exception as e:
    print(f"Errore creazione script locale: {e}")

# 6. Avvia il server tramite lo script VBS locale!
print("Avvio del server in corso tramite VBScript...")
try:
    # Esegui wscript.exe per lanciare il VBScript in background
    subprocess.run(["wscript.exe", vbs_local_path], shell=True)
    print("VBScript eseguito con successo!")
except Exception as e:
    print(f"Errore durante l'esecuzione del VBScript: {e}")
