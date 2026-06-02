import os
import sys
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

# 1. Determina i percorsi assoluti
current_dir = r"C:\Users\Jonny\Desktop\REPORT CANZONI RADIO"
server_script = os.path.join(current_dir, "server.py")

# Risolvi pythonw.exe
python_exe = sys.executable
pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
if not os.path.exists(pythonw_exe):
    # Fallback generico
    pythonw_exe = "pythonw.exe"

print(f"Risolto Pythonw.exe: {pythonw_exe}")
print(f"Script del Server: {server_script}")

# 2. Crea lo shortcut nella cartella Startup di Windows
startup_dir = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
shortcut_path = os.path.join(startup_dir, "ServerClassificheRadio.lnk")

print(f"Percorso di Startup: {shortcut_path}")

try:
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = pythonw_exe
    shortcut.Arguments = f'"{server_script}"'
    shortcut.WorkingDirectory = current_dir
    shortcut.WindowStyle = 7 # Minimized/Hidden
    shortcut.Save()
    print("Scorciatoia di avvio automatico silenzioso creata con successo tramite pywin32!")
except Exception as e:
    # Fallback con PowerShell se pywin32 non è installato
    print("Pywin32 non disponibile. Tonto fallback con PowerShell...")
    ps_cmd = f'$s = (New-Object -ComObject WScript.Shell).CreateShortcut("{shortcut_path}"); $s.TargetPath = "{pythonw_exe}"; $s.Arguments = "\\"{server_script}\\""; $s.WorkingDirectory = "{current_dir}"; $s.WindowStyle = 7; $s.Save()'
    res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
    if res.returncode == 0:
        print("Scorciatoia di avvio automatico silenzioso creata con successo tramite PowerShell!")
    else:
        print(f"Errore creazione scorciatoia: {res.stderr}")

# 3. Avvia il server in background SILENZIOSAMENTE proprio ora!
print("\nAvvio del server in background silenzioso in corso...")
# Chiudiamo eventuali istanze già attive del server sulla porta 8000 se possibile, o avviamo direttamente
try:
    # Usiamo subprocess.Popen con CREATE_NO_WINDOW per lanciarlo in background in modo totalmente invisibile
    creation_flags = 0x08000000 # CREATE_NO_WINDOW
    subprocess.Popen([pythonw_exe, server_script], cwd=current_dir, creationflags=creation_flags)
    print("Server locale avviato in background in modalità silenziosa! È pronto a rispondere alle richieste di salvataggio.")
except Exception as e:
    print(f"Errore all'avvio del server in background: {e}")
