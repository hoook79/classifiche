import openpyxl
import os

file_path = r"classifica_radio_rds_STORICO.xlsx"
if os.path.exists(file_path):
    wb = openpyxl.load_workbook(file_path, read_only=True)
    sheet = wb.active
    # Leggi la prima riga (intestazioni)
    headers = [cell.value for cell in next(sheet.iter_rows(max_row=1))]
    print("Intestazioni RDS STORICO:", headers)
else:
    print("File rds_STORICO.xlsx non trovato")
