from nicegui import ui, app
import pandas as pd
import sqlite3
from datetime import datetime
import re
import os
from werkzeug.utils import secure_filename
import tempfile

# Define column_sets before the process_and_insert function
column_sets = {
    'Calls': {'call_type', 'time', 'from_to', 'duration_sec', 'location'},
    'Messenger': {'contact_name', 'message_time', 'message_text'},
    'SMS': {'phone_number', 'message_time', 'message_text', 'location'},
    'Contacts': {'name', 'phone_number', 'email'},
    'InstalledApps': {'app_name', 'package_name', 'install_date'},
    'Keylogs': {'application', 'time', 'text'}
}

# Add this line after the imports
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Database Connection
DATABASE_FILE = 'data.db'
conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

# Utility Functions
def convert_time_to_string(time_str):
    try:
        year_match = re.search(r"(\d{4})", time_str)
        year = year_match.group(1) if year_match else datetime.now().year
        return datetime.strptime(f"{year} {time_str}", '%Y %b %d, %I:%M %p').strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        ui.notify(f"Invalid time format: {time_str}", type='error')
        return None

def convert_duration_to_seconds(duration_str):
    if pd.isnull(duration_str):
        return None
    match = re.match(r"(?:(\d+)\s*Min)?(?:\s*&\s*)?(?:(\d+)\s*Sec)?", duration_str)
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds = int(match.group(2)) if match.group(2) else 0
        return minutes * 60 + seconds
    else:
        ui.notify(f"Invalid duration format: {duration_str}", type='error')
        return None

def validate_required_columns(df, required_columns):
    if not set(required_columns).issubset(df.columns):
        missing_columns = set(required_columns) - set(df.columns)
        ui.notify(f"Missing columns: {', '.join(missing_columns)}", type='error')
        return False
    return True

# Table Creation
def create_tables():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Calls (
            call_id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_type TEXT,
            time DATETIME,
            from_to TEXT,
            duration_sec INTEGER,
            location TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Messenger (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_name TEXT,
            message_time DATETIME,
            message_text TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SMS (
            sms_id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            message_time DATETIME,
            message_text TEXT,
            location TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Contacts (
            contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone_number TEXT,
            email TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS InstalledApps (
            app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT,
            package_name TEXT,
            install_date DATETIME
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Keylogs (
            keylog_id INTEGER PRIMARY KEY AUTOINCREMENT,
            application TEXT,
            time DATETIME,
            text TEXT
        )
    ''')
    conn.commit()
    ui.notify('Tables created successfully!', type='positive')

def process_and_insert(file: ui.UploadFile):
    try:
        # Create a temporary file with a secure filename in the project directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(secure_filename(file.filename))[1], dir=PROJECT_DIR) as temp_file:
            temp_file.write(file.content.read())
            temp_file_path = temp_file.name

        # Identify the table based on the file contents
        df = pd.read_csv(temp_file_path) if temp_file_path.endswith('.csv') else pd.read_excel(temp_file_path)

        table_name = identify_table(df)
        if not table_name:
            ui.notify('Unable to identify the table for this data.', type='negative')
            return

        # Rename the file based on the identified table
        new_filename = f"{table_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{os.path.splitext(file.filename)[1]}"
        new_file_path = os.path.join(PROJECT_DIR, new_filename)
        os.rename(temp_file_path, new_file_path)

        # Validate required columns
        if not validate_required_columns(df, column_sets[table_name]):
            return

        # Insert data into the appropriate table
        for _, row in df.iterrows():
            if table_name == 'Calls':
                cursor.execute('''
                    INSERT INTO Calls (call_type, time, from_to, duration_sec, location)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    row['call_type'],
                    convert_time_to_string(row['time']),
                    row['from_to'],
                    convert_duration_to_seconds(row['duration_sec']),
                    row['location']
                ))
            elif table_name == 'Messenger':
                cursor.execute('''
                    INSERT INTO Messenger (contact_name, message_time, message_text)
                    VALUES (?, ?, ?)
                ''', (
                    row['contact_name'],
                    convert_time_to_string(row['message_time']),
                    row['message_text']
                ))
            elif table_name == 'SMS':
                cursor.execute('''
                    INSERT INTO SMS (phone_number, message_time, message_text, location)
                    VALUES (?, ?, ?, ?)
                ''', (
                    row['phone_number'],
                    convert_time_to_string(row['message_time']),
                    row['message_text'],
                    row['location']
                ))
            elif table_name == 'Contacts':
                cursor.execute('''
                    INSERT INTO Contacts (name, phone_number, email)
                    VALUES (?, ?, ?)
                ''', (
                    row['name'],
                    row['phone_number'],
                    row['email']
                ))
            elif table_name == 'InstalledApps':
                cursor.execute('''
                    INSERT INTO InstalledApps (app_name, package_name, install_date)
                    VALUES (?, ?, ?)
                ''', (
                    row['app_name'],
                    row['package_name'],
                    convert_time_to_string(row['install_date'])
                ))
            elif table_name == 'Keylogs':
                cursor.execute('''
                    INSERT INTO Keylogs (application, time, text)
                    VALUES (?, ?, ?)
                ''', (
                    row['application'],
                    convert_time_to_string(row['time']),
                    row['text']
                ))

        conn.commit()
        ui.notify(f'Data inserted into {table_name} table successfully!', type='positive')
        display_table(table_name)
    except Exception as e:
        ui.notify(f'Error processing file: {str(e)}', type='negative')
    finally:
        if os.path.exists(new_file_path):
            os.unlink(new_file_path)

def identify_table(df):
    df_columns = set(df.columns)
    for table, columns in column_sets.items():
        if columns.issubset(df_columns):
            return table
    return None

def bottom_navigation():
    with ui.footer().classes('bg-blue-600 text-white fixed-bottom'):
        with ui.row().classes('w-full justify-around items-center'):
            ui.button(on_click=lambda: display_table('Calls')).props('flat color=white icon=phone')
            ui.button(on_click=lambda: display_table('SMS')).props('flat color=white icon=sms')
            ui.button(on_click=lambda: ui.upload(on_upload=process_and_insert).props('accept=.csv,.xlsx').open()).props('flat color=white icon=upload')
            ui.button(on_click=lambda: display_table('Contacts')).props('flat color=white icon=contacts')
            ui.button(on_click=lambda: display_table('InstalledApps')).props('flat color=white icon=apps')

@ui.page('/')
def main():
    ui.add_head_html('''
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
            .content-area {
                padding: 16px;
                margin-bottom: 56px; /* Height of the bottom navigation */
            }
        </style>
    ''')

    with ui.column().classes('w-full items-center content-area'):
        ui.label('Data Management System').classes('text-h5 q-my-md')

        with ui.card().classes('w-full max-w-md'):
            ui.label('Upload Data').classes('text-h6 q-mb-sm')
            ui.upload(on_upload=process_and_insert).props('accept=.csv,.xlsx').classes('q-mb-md')

    bottom_navigation()

def display_table(table_name, search_term=None):
    with ui.column().classes('w-full content-area'):
        ui.label(f'{table_name} Table').classes('text-h6 q-mb-md')
        search_input = ui.input(placeholder='Search...', on_change=lambda e: display_table(table_name, e.value)).props('outlined dense')

        query = f"SELECT * FROM {table_name}"
        if search_term:
            columns = [col[1] for col in cursor.execute(f"PRAGMA table_info({table_name})")]
            search_conditions = " OR ".join([f"{col} LIKE ?" for col in columns])
            query += f" WHERE {search_conditions}"
            params = tuple(f"%{search_term}%" for _ in columns)
        else:
            params = ()

        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        with ui.table().classes('w-full').props('flat bordered'):
            with ui.thead():
                for col in columns:
                    ui.th().text(col)
            with ui.tbody():
                for row in rows:
                    with ui.tr():
                        for cell in row:
                            ui.td().text(str(cell))

if __name__ in {"__main__", "__mp_main__"}:
    create_tables()
    ui.run(title='Data Management System', host='0.0.0.0', port=8080)
