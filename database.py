# database.py

from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# Initialize client and database
client = AsyncIOMotorClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

# Collections
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
    settings = await settings_col.find_one({"_id": "bot_settings"})
    if not settings:
        return {
            "start_message": Config.DEFAULT_START_MESSAGE,
            "start_pic": Config.START_PIC
        }
    return settings

async def update_setting(key: str, value: str):
    await settings_col.update_one(
        {"_id": "bot_settings"},
        {"$set": {key: value}},
        upsert=True
    )
    
