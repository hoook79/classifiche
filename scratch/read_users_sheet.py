import os
import sys
import json

BASE_DIR = r"C:\Users\Jonny\Desktop\REPORT CANZONI RADIO"
sys.path.append(BASE_DIR)

from google_sheets_sync import get_sheets_client, SPREADSHEET_NAME

def main():
    client = get_sheets_client()
    if not client:
        print("Errore: impossibile ottenere il client Google Sheets.")
        return
        
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        users_sheet = spreadsheet.worksheet("Users")
        records = users_sheet.get_all_values()
        print("\n--- DATI SCHEDA USERS ---")
        for row in records:
            print(row)
        print("-------------------------\n")
    except Exception as e:
        print(f"Errore durante la lettura: {e}")

if __name__ == '__main__':
    main()
