# config.py

import os

class Config:
    # Get values from environment variables
    API_ID = int(os.environ.get("API_ID", "12345"))
    API_HASH = os.environ.get("API_HASH", "your_api_hash")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

    # Database Configuration
    MONGO_URI = os.environ.get("MONGO_URI", "your_mongodb_uri")
    DB_NAME = os.environ.get("DB_NAME", "ebook_bot_db")

    # Admin and Channel Configuration
    SUDO_ADMINS = [int(admin_id) for admin_id in os.environ.get("SUDO_ADMINS", "100100100").split()]
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-100123456789"))

    # Bot Settings
    START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/example.jpg")
    
    DEFAULT_START_MESSAGE = """
Hello {first_name}! 🤖

I am an advanced E-Book and Image converter bot.

<b><u>Features:</u></b>
- Convert between <b>EPUB, MOBI, AZW3, FB2, CBZ,</b> and <b>PDF</b>.
- Upload images to <b>Telegraph</b>.

Send me a file, and I will show you the available conversion options!
"""
