import sqlite3

try:
    DATABASE_FILE = 'data.db'
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    print('Successfully connected to the database.')

    # Test the connection by executing a simple query
    cursor.execute('SELECT sqlite_version();')
    version = cursor.fetchone()
    print(f'SQLite version: {version[0]}')

    # List all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print('Tables in the database:')
    for table in tables:
        print(f'- {table[0]}')

    conn.close()
    print('Database connection closed.')
except sqlite3.Error as e:
    print(f'An error occurred: {e}')
