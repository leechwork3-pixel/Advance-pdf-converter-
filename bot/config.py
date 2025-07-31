# bot/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot API credentials from my.telegram.org
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# MongoDB Database URI
MONGO_URI = os.environ.get("MONGO_URI", "")
DB_NAME = os.environ.get("DB_NAME", "EbookConverterBot")

# Sudo Admins: User IDs of bot owners who can grant/revoke admin rights.
# Add your own Telegram user ID here.
SUDO_ADMINS = [int(admin_id) for admin_id in os.environ.get("SUDO_ADMINS", "123456789").split()]

# Log Channel: A public/private channel ID to send logs and new user notifications.
# Make sure your bot is an admin in this channel.
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0")) # Example: -1001234567890

# Telegraph account name
TELEGRAPH_SHORT_NAME = os.environ.get("TELEGRAPH_SHORT_NAME", "ImageUploader")
