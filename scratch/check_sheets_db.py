import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'google_credentials.json')
SPREADSHEET_NAME = "RadioCharts_Database"

print("Authenticating with Google Sheets API...")
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
spreadsheet = client.open(SPREADSHEET_NAME)

print("Reading 'Users' worksheet...")
try:
    user_sheet = spreadsheet.worksheet("Users")
    records = user_sheet.get_all_records()
    print(f"Found {len(records)} users in database.")
except Exception as e:
    print(f"Error reading 'Users' worksheet: {e}")
    exit(1)

# Apps Script URL to test
apps_script_url = "https://script.google.com/macros/s/AKfycbx_p44hQCjBjPvNOdM5whPI3hgd8SA96gbAcwva3ywe8CRjci4RAYUQXYc4oVMuzEic/exec"

for idx, r in enumerate(records):
    user = r.get("A (Username)")
    password = r.get("B (Password)")
    role = r.get("C (Role)")
    allowed = r.get("E (AllowedRadios)")
    
    print(f"\n--- Testing User {idx+1}: {user} (Role: {role}, Allowed: {allowed}) ---")
    
    params = {
        "action": "getData",
        "username": user,
        "password": password
    }
    
    try:
        response = requests.get(apps_script_url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")
        
        # Try to parse JSON
        try:
            data = response.json()
            if data.get("success"):
                print("  [OK] Success! Retrieved data keys:")
                print(f"       {list(data.get('data', {}).keys())}")
                print(f"       Role: {data.get('role')}, AllowedRadios: {data.get('allowedRadios')}")
            else:
                print(f"  [API ERROR] success=false, error: {data.get('error')}")
        except Exception as je:
            print("  [PARSE ERROR] Response is not valid JSON!")
            print(f"  Error message: {je}")
            print(f"  Body (first 1000 chars):")
            print(response.text[:1000])
            
    except Exception as e:
        print(f"  [CONNECTION ERROR] {e}")
