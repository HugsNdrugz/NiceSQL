from nicegui import ui

# Add this to your main.py imports
from replit_config import configure_for_replit

# Add this function to configure the app for Replit
def configure_for_replit():
    ui.run(title='Data Management System', host='0.0.0.0', port=8080)

if __name__ == '__main__':
    configure_for_replit()
