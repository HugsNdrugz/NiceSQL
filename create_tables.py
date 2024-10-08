import sqlite3

DATABASE_FILE = 'your_database.db'
conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

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
    print('Tables created successfully!')

create_tables()
conn.close()
