from nicegui import ui
import main
import io
import pandas as pd

# Test the process_and_insert function
class MockUploadFile:
    def __init__(self, filename, content):
        self.name = filename
        self.content = io.BytesIO(content)

    def read(self):
        return self.content.getvalue()

# Create a mock CSV file content
mock_csv_content = b'''call_type,time,from_to,duration_sec,location
Incoming,Jan 1, 10:00 AM,John Doe,5 Min & 30 Sec,New York
Outgoing,Jan 2, 2:00 PM,Jane Smith,2 Min & 15 Sec,Los Angeles
'''

mock_file = MockUploadFile('test_calls.csv', mock_csv_content)

try:
    # Create tables before running the test
    main.create_tables()

    # Call the process_and_insert function
    main.process_and_insert(mock_file)

    # Verify that the data was inserted correctly
    conn = main.conn
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Calls')
    rows = cursor.fetchall()

    print('Inserted data:')
    for row in rows:
        print(row)

    print("Test completed successfully!")
except Exception as e:
    print(f"Error during test: {str(e)}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
