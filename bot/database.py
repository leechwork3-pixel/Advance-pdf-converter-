# bot/database.py

from pymongo import MongoClient
from bot.config import MONGO_URI, DB_NAME, SUDO_ADMINS

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_collection = db["users"]
admins_collection = db["admins"]
settings_collection = db["settings"]

# --- User Management ---
async def add_user(user_id: int) -> bool:
    if await users_collection.find_one({"user_id": user_id}):
        return False
    await users_collection.insert_one({"user_id": user_id})
    return True

async def get_total_users() -> int:
    return await users_collection.count_documents({})

async def get_all_user_ids():
    return users_collection.find({}, {"user_id": 1})

# --- Admin Management ---
async def is_admin(user_id: int) -> bool:
    if user_id in SUDO_ADMINS:
        return True
    return bool(await admins_collection.find_one({"admin_id": user_id}))

async def add_admin(user_id: int):
    if not await is_admin(user_id):
        await admins_collection.insert_one({"admin_id": user_id})

async def remove_admin(user_id: int):
    await admins_collection.delete_one({"admin_id": user_id})

# --- Bot Settings Management ---
async def set_setting(key: str, value):
    """Saves a setting to the database."""
    await settings_collection.update_one(
        {"_id": key},
        {"$set": {"value": value}},
        upsert=True
    )

async def get_setting(key: str):
    """Retrieves a setting from the database."""
    setting = await settings_collection.find_one({"_id": key})
    return setting['value'] if setting else None
    
