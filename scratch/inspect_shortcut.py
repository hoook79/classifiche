import os
import win32com.client

startup_dir = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
shortcut_path = os.path.join(startup_dir, "ServerClassificheRadio.lnk")

shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortcut(shortcut_path)
print("Shortcut Details:")
print(f"Target: {shortcut.TargetPath}")
print(f"Arguments: {shortcut.Arguments}")
print(f"WorkingDir: {shortcut.WorkingDirectory}")
print(f"WindowStyle: {shortcut.WindowStyle}")
