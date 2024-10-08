import pandas as pd
from main import process_and_insert, conn, cursor
import os

files = [
    'attachments/calls.xlsx',
    'attachments/contacts.xlsx',
    'attachments/installed+apps.xlsx',  # Changed 'installed apps.xlsx' to 'installed+apps.xlsx'
    'attachments/keylogs.xlsx',
    'attachments/messanger.xlsx',
    'attachments/sms.xlsx'
]

for file in files:
    print(f'Processing {file}...')
    if os.path.exists(file):
        df = pd.read_excel(file)
        process_and_insert({'name': file, 'content': df})
    else:
        print(f"File not found: {file}")

print('All files processed.')
conn.close()
