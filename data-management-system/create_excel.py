import pandas as pd

df = pd.read_csv('test_messages.csv')
df.to_excel('test_messages.xlsx', index=False)
print("Excel file created successfully.")
