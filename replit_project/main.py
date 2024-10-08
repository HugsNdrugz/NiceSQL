from nicegui import ui
import pandas as pd
import sqlite3
from datetime import datetime
import re
import os
from werkzeug.utils import secure_filename
import tempfile
# Configuration for Replit will be added at the end of the file

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

def process_and_insert(file):
    # [Existing implementation]

def identify_table(df):
    # [Existing implementation]

@ui.page('/')
def main():
    ui.add_head_html('''
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
        <style>
            /* [Existing styles] */
            .call-list, .contact-list, .sms-list {
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
            .call-item, .contact-item, .sms-item {
                display: flex;
                align-items: center;
                padding: 12px 16px;
                border-bottom: 1px solid #e0e0e0;
            }
            .call-icon, .contact-avatar, .sms-avatar {
                width: 48px;
                height: 48px;
                border-radius: 50%;
                margin-right: 16px;
                background-color: #e0e0e0;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .call-details, .contact-details, .sms-content {
                flex: 1;
            }
            .call-name, .contact-name, .sms-name {
                font-weight: bold;
                margin-bottom: 4px;
            }
            .call-info, .contact-info, .sms-message {
                color: #65676B;
                font-size: 14px;
            }
            .chat-messages { max-height: 70vh; overflow-y: auto; }
            .message-row { margin-bottom: 8px; }
            .message-time { font-size: 12px; color: #65676B; }
            .message-text { background-color: #E4E6EB; padding: 8px 12px; border-radius: 18px; display: inline-block; }
            .message-input { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 20px; }
            .send-button { margin-left: 8px; }
            .back-button { margin-bottom: 16px; }
            .contact-list-item { cursor: pointer; }
        </style>
    ''')

    current_section = ui.state('chats')
    current_chat = ui.state(None)

    def show_section(section):
        current_section.set(section)
        current_chat.set(None)

    def show_chat(contact, section):
        current_section.set(f'individual_{section}')
        current_chat.set(contact)

    with ui.column().classes('content-area'):
        with ui.column().bind_visibility_from(current_section, lambda x: x == 'chats'):
            ui.label('Chats').classes('text-h5 q-mb-md')
            with ui.column().classes('chat-list'):
                cursor.execute('SELECT DISTINCT contact_name FROM Messenger ORDER BY message_time DESC')
                chat_contacts = cursor.fetchall()
                for contact in chat_contacts:
                    with ui.row().classes('chat-item').on('click', lambda _, c=contact[0]: show_chat(c, 'chats')):
                        ui.label().classes('chat-avatar')
                        with ui.column().classes('chat-content'):
                            ui.label(contact[0]).classes('chat-name')
                            cursor.execute('SELECT message_text FROM Messenger WHERE contact_name = ? ORDER BY message_time DESC LIMIT 1', (contact[0],))
                            last_message = cursor.fetchone()
                            ui.label(last_message[0] if last_message else 'No messages').classes('chat-message')

        with ui.column().bind_visibility_from(current_section, lambda x: x == 'sms'):
            ui.label('SMS').classes('text-h5 q-mb-md')
            with ui.column().classes('sms-list'):
                cursor.execute('SELECT DISTINCT phone_number FROM SMS ORDER BY message_time DESC')
                sms_contacts = cursor.fetchall()
                for contact in sms_contacts:
                    with ui.row().classes('sms-item').on('click', lambda _, c=contact[0]: show_chat(c, 'sms')):
                        ui.label().classes('sms-avatar')
                        with ui.column().classes('sms-content'):
                            ui.label(contact[0]).classes('sms-name')
                            cursor.execute('SELECT message_text FROM SMS WHERE phone_number = ? ORDER BY message_time DESC LIMIT 1', (contact[0],))
                            last_message = cursor.fetchone()
                            ui.label(last_message[0] if last_message else 'No messages').classes('sms-message')

        with ui.column().bind_visibility_from(current_section, lambda x: x == 'calls'):
            ui.label('Calls').classes('text-h5 q-mb-md')
            with ui.column().classes('call-list'):
                cursor.execute('SELECT call_type, time, from_to, duration_sec FROM Calls ORDER BY time DESC LIMIT 20')
                calls = cursor.fetchall()
                for call in calls:
                    with ui.row().classes('call-item'):
                        ui.icon('phone_callback' if call[0] == 'Incoming' else 'phone_forwarded').classes('call-icon')
                        with ui.column().classes('call-details'):
                            ui.label(call[2]).classes('call-name')
                            ui.label(f"{call[0]} • {call[1]}").classes('call-info')
                            ui.label(f"Duration: {call[3]} seconds").classes('call-info')

        with ui.column().bind_visibility_from(current_section, lambda x: x == 'contacts'):
            ui.label('Contacts').classes('text-h5 q-mb-md')
            with ui.column().classes('contact-list'):
                cursor.execute('SELECT name, phone_number, email FROM Contacts ORDER BY name')
                contacts = cursor.fetchall()
                for contact in contacts:
                    with ui.row().classes('contact-item contact-list-item').on('click', lambda _, c=contact[0]: show_chat(c, 'chats')):
                        ui.label().classes('contact-avatar')
                        with ui.column().classes('contact-details'):
                            ui.label(contact[0]).classes('contact-name')
                            ui.label(contact[1]).classes('contact-info')
                            ui.label(contact[2]).classes('contact-info')

        with ui.column().bind_visibility_from(current_section, lambda x: x.startswith('individual_')):
            ui.button('Back', on_click=lambda: show_section(current_section.value.split('_')[1])).classes('back-button')
            ui.label().bind_text_from(current_chat).classes('text-h5 q-mb-md')
            with ui.column().classes('chat-messages'):
                @ui.refreshable
                def display_messages():
                    table = 'Messenger' if current_section.value == 'individual_chats' else 'SMS'
                    id_column = 'contact_name' if table == 'Messenger' else 'phone_number'
                    cursor.execute(f'SELECT message_time, message_text FROM {table} WHERE {id_column} = ? ORDER BY message_time', (current_chat.value,))
                    messages = cursor.fetchall()
                    for message in messages:
                        with ui.row().classes('message-row'):
                            with ui.column().classes('message-bubble message-received'):
                                ui.label(message[1]).classes('message-text')
                                ui.label(message[0]).classes('message-time')
                display_messages()

            def send_message(msg):
                if msg.strip():
                    table = 'Messenger' if current_section.value == 'individual_chats' else 'SMS'
                    id_column = 'contact_name' if table == 'Messenger' else 'phone_number'
                    cursor.execute(f'INSERT INTO {table} ({id_column}, message_time, message_text) VALUES (?, ?, ?)',
                                   (current_chat.value, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))
                    conn.commit()
                    display_messages.refresh()
                    new_message.set_value('')

            new_message = ui.input(placeholder='Type a message...').classes('message-input')
            ui.button('Send', on_click=lambda: send_message(new_message.value)).classes('send-button')

    with ui.footer().classes('bottom-nav'):
        ui.button(on_click=lambda: show_section('chats')).props('flat color=primary icon=chat')
        ui.button(on_click=lambda: show_section('sms')).props('flat color=primary icon=sms')
        ui.button(on_click=lambda: show_section('calls')).props('flat color=primary icon=call')
        ui.button(on_click=lambda: show_section('contacts')).props('flat color=primary icon=contacts')

ui.run(title='Messenger App', host='0.0.0.0', port=8080)
