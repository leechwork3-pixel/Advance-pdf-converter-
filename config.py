# config.py

import os

class Config:
    # Get values from environment variables
    API_ID = int(os.environ.get("API_ID", "24171111"))
    API_HASH = os.environ.get("API_HASH", "c850cb56b64b6c3b10ade9c28ef7966a")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "7804274444:AAESKpYJQVhftykvv5cKZP2uyCYvxlwQvow")

    # Database Configuration
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://pankaj1123r:IudexNeuvillette@iudexneuvillette.voopvck.mongodb.net/?retryWrites=true&w=majority&appName=IudexNeuvillette")
    DB_NAME = os.environ.get("DB_NAME", "ebook_bot_db")

    # Admin and Channel Configuration
    SUDO_ADMINS = [int(admin_id) for admin_id in os.environ.get("SUDO_ADMINS", "1335306418").split()]
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002585029413"))

    # Bot Settings
    START_PIC = os.environ.get("START_PIC", "https://i.ibb.co/RTnxJTPK/thumb.jpg")
    
    DEFAULT_START_MESSAGE = """
Hello {first_name}! 🤖

I am an advanced E-Book and Image converter bot.

<b><u>Features:</u></b>
- Convert between <b>EPUB, MOBI, AZW3, FB2, CBZ,</b> and <b>PDF</b>.
- Upload images to <b>Telegraph</b>.

Send me a file, and I will show you the available conversion options!
"""
