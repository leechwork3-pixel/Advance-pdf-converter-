# database.py

from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import sys

client = None
db = None
users_col = None
admins_col = None
settings_col = None

async def connect_db():
    """Initializes the database connection and collections."""
    global client, db, users_col, admins_col, settings_col
    
    print("Attempting to connect to MongoDB...")
    client = AsyncIOMotorClient(Config.MONGO_URI)
    
    try:
        # The ismaster command is cheap and does not require auth.
        await client.admin.command('ismaster')
        print("✅ MongoDB connection successful.")
    except Exception as e:
        print(f"❌ Could not connect to MongoDB: {e}", file=sys.stderr)
        # Exit the application if DB connection fails
        sys.exit(1)

    db = client[Config.DB_NAME]
    users_col = db["users"]
    admins_col = db["admins"]
    settings_col = db["settings"]


# --- User Management ---
async def add_user(user_id: int):
    if not await users_col.find_one({"user_id": user_id}):
        await users_col.insert_one({"user_id": user_id})
        return True
    return False

async def get_all_user_ids():
    cursor = users_col.find({}, {"_id": 0, "user_id": 1})
    return [doc["user_id"] for doc in await cursor.to_list(length=None)]

async def get_user_count():
    return await users_col.count_documents({})

# --- Admin Management ---
async def is_sudo_admin(user_id: int) -> bool:
    return user_id in Config.SUDO_ADMINS

async def add_admin(user_id: int):
    if not await admins_col.find_one({"admin_id": user_id}):
        await admins_col.insert_one({"admin_id": user_id})

async def remove_admin(user_id: int):
    await admins_col.delete_one({"admin_id": user_id})

async def get_all_admin_ids():
    sudo_admins = Config.SUDO_ADMINS
    db_admins_cursor = admins_col.find({}, {"_id": 0, "admin_id": 1})
    db_admins = [doc["admin_id"] for doc in await db_admins_cursor.to_list(length=None)]
    return list(set(sudo_admins + db_admins))

# --- Bot Settings Management ---
async def get_settings():
    """Fetches all settings from the database."""
    settings = await settings_col.find_one({"_id": "bot_settings"})
    if not settings:
        return {
            "start_message": Config.DEFAULT_START_MESSAGE,
            "start_pic": Config.START_PIC
        }
    return settings

async def update_setting(key: str, value: str):
    """Updates a specific setting."""
    await settings_col.update_one(
        {"_id": "bot_settings"},
        {"$set": {key: value}},
        upsert=True
    )
    
