import pandas as pd

# Create CSV file
csv_data = {
    'message_type': ['SMS', 'MMS', 'SMS'],
    'time': ['2023-10-07 14:30:00', '2023-10-07 15:00:00', '2023-10-07 16:15:00'],
    'from_to': ['+1234567890', '+9876543210', '+1122334455'],
    'message': ['Hello world', 'Check out this image!', 'How are you doing?']
}

df = pd.DataFrame(csv_data)
df.to_csv('test_messages.csv', index=False)
print("CSV file created successfully.")

# Create Excel file
df.to_excel('test_messages.xlsx', index=False)
print("Excel file created successfully.")
