import sqlite3
import pandas as pd
from nicegui import ui
from datetime import datetime
from typing import List, Dict, Any
import re
import json
from io import BytesIO
from pathlib import Path
import tempfile
import os

column_sets = {
    'Calls': {'call_type', 'time', 'from_to', 'duration', 'location'},
    'Messages': {'message_type', 'time', 'from_to', 'message'},
    'Contacts': {'name', 'phone_number', 'email'},
    'InstalledApps': {'app_name', 'package_name', 'install_date'},
    'Keylogs': {'application', 'time', 'text'}
}

# Database configuration
DATABASE_FILE = 'data.db'

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
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
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
            CREATE TABLE IF NOT EXISTS Messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_type TEXT,
                time DATETIME,
                from_to TEXT,
                message TEXT
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

# Data Insertion
def insert_data(table_name, df):
    placeholders = ', '.join(['?' for _ in df.columns])
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.executemany(f"INSERT INTO {table_name} VALUES (NULL, {placeholders})", df.values.tolist())
            conn.commit()
        ui.notify(f"Data inserted into '{table_name}' successfully.", type='positive')
    except Exception as e:
        ui.notify(f"Error inserting data: {e}", type='error')

# File processing and insertion
def process_and_insert(uploaded_file):
    try:
        file_content = uploaded_file.content
        file_name = uploaded_file.name

        if file_name.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(file_content))
        elif file_name.endswith('.csv'):
            df = pd.read_csv(BytesIO(file_content))
        else:
            ui.notify("Unsupported file format. Please upload CSV or Excel files.", type='negative')
            return None

        headers = set(df.columns)
        table_name = next((table for table, columns in column_sets.items() if columns.issubset(headers)), None)

        if table_name is None:
            ui.notify("Unable to determine the appropriate table for this file.", type='negative')
            return None

        insert_data(table_name, df)
        ui.notify(f"File processed and data inserted into {table_name} table.", type='positive')
        return table_name
    except Exception as e:
        ui.notify(f"Error processing file: {str(e)}", type='negative')
        return None

def get_avatar(name):
    return f"https://ui-avatars.com/api/?name={name}&background=random&color=fff&font-size=0.5"

def show_data(active_tab='Messages'):
    with ui.column().classes('w-full h-full main-content'):
        with ui.row().classes('w-full justify-between items-center p-4 bg-blue-500 text-white'):
            ui.label('Data View').classes('text-xl font-bold')
            ui.button(icon='add', on_click=lambda: ui.upload(on_upload=process_and_notify).classes('w-full')).classes('bg-white text-blue-500 rounded-full')

        with ui.tabs().classes('w-full') as tabs:
            ui.tab('Messages', icon='chat').classes('text-sm')
            ui.tab('Calls', icon='call').classes('text-sm')
            ui.tab('Contacts', icon='contacts').classes('text-sm')
            ui.tab('Apps', icon='apps').classes('text-sm')
            ui.tab('Keylogs', icon='keyboard').classes('text-sm')

        with ui.tab_panels(tabs, value=active_tab).classes('w-full flex-grow'):
            with ui.tab_panel('Messages'):
                display_messages()
            with ui.tab_panel('Calls'):
                display_calls()
            with ui.tab_panel('Contacts'):
                display_contacts()
            with ui.tab_panel('Apps'):
                display_apps()
            with ui.tab_panel('Keylogs'):
                display_keylogs()

        ui.input(placeholder='Search conversations...').classes('fixed bottom-4 left-4 right-4 bg-white rounded-full p-2')

def display_messages():
    messages = get_all_messages()
    contacts = {contact['phone_number']: contact['name'] for contact in get_contacts()}
    grouped_messages = {}

    for message in messages:
        contact = contacts.get(message['from_to'], message['from_to'])
        if contact not in grouped_messages:
            grouped_messages[contact] = []
        grouped_messages[contact].append(message)

    for contact, msgs in grouped_messages.items():
        with ui.expansion(contact).classes('w-full mb-2'):
            for message in msgs:
                with ui.card().classes('w-full mb-2 p-2'):
                    with ui.row().classes('items-center'):
                        ui.avatar(get_avatar(contact)).classes('mr-2')
                        with ui.column():
                            ui.label(contact).classes('font-bold')
                            ui.label(message['time']).classes('text-xs text-gray-500')
                    ui.label(message['message']).classes('mt-2 text-sm chat-bubble')

def display_calls():
    calls = get_calls()
    contacts = {contact['phone_number']: contact['name'] for contact in get_contacts()}

    with ui.column().classes('w-full').style('max-height: calc(100vh - 200px); overflow-y: auto;'):
        for call in calls:
            with ui.card().classes('w-full mb-2 p-2'):
                with ui.row().classes('items-center'):
                    ui.avatar(get_avatar(contacts.get(call['from_to'], call['from_to']))).classes('mr-2')
                    with ui.column():
                        ui.label(contacts.get(call['from_to'], call['from_to'])).classes('font-bold')
                        ui.label(f"{call['call_type']} - {call['time']}").classes('text-xs text-gray-500')
                ui.label(f"Duration: {call['duration_sec']} seconds").classes('mt-2 text-sm')

def display_contacts():
    contacts = get_contacts()
    with ui.column().classes('w-full').style('max-height: calc(100vh - 200px); overflow-y: auto;'):
        for contact in contacts:
            with ui.card().classes('w-full mb-2 p-2'):
                with ui.row().classes('items-center'):
                    ui.avatar(get_avatar(contact['name'])).classes('mr-2')
                    with ui.column():
                        ui.label(contact['name']).classes('font-bold')
                        ui.label(contact.get('phone_number', '')).classes('text-sm')
                        ui.label(contact.get('email', '')).classes('text-sm')

def display_apps():
    apps = get_installed_apps()
    with ui.column().classes('w-full').style('max-height: calc(100vh - 200px); overflow-y: auto;'):
        for app in apps:
            with ui.card().classes('w-full mb-2 p-2'):
                ui.label(app['app_name']).classes('text-base font-bold')
                ui.label(app['package_name']).classes('text-sm')
                ui.label(app['install_date']).classes('text-sm text-gray-500')

def display_keylogs():
    keylogs = get_keylogs()
    with ui.column().classes('w-full').style('max-height: calc(100vh - 200px); overflow-y: auto;'):
        for keylog in keylogs:
            with ui.card().classes('w-full mb-2 p-2'):
                ui.label(f"{keylog['application']} - {keylog['time']}").classes('text-sm text-gray-500')
                ui.label(keylog['text']).classes('text-base')

def get_all_messages():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Messages ORDER BY time DESC LIMIT 100")
        messages = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    return messages

def get_calls():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Calls ORDER BY time DESC LIMIT 100")
        calls = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    return calls

def get_contacts():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Contacts")
        contacts = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    return contacts

def get_installed_apps():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM InstalledApps ORDER BY install_date DESC")
        apps = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    return apps

def get_keylogs():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Keylogs ORDER BY time DESC LIMIT 100")
        keylogs = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    return keylogs

def process_and_notify(e):
    table_name = process_and_insert(e)
    if table_name:
        show_data(table_name)

def main():
    create_tables()
    show_data()
    ui.run(port=8080, title='Data Management System')

if __name__ in {"__main__", "__mp_main__"}:
    main()

# Add CSS for chat bubble appearance
ui.add_body_html("""
<style>
.chat-bubble {
    background-color: #e5e5ea;
    border-radius: 0.8em;
    padding: 0.5em 0.8em;
    margin: 0.5em 0;
    max-width: 80%;
    word-wrap: break-word;
}
</style>
""")
