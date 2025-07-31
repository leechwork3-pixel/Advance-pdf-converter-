# bot/database.py

from pymongo import MongoClient
from bot.config import MONGO_URI, DB_NAME, SUDO_ADMINS

# Establish connection to the database
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_collection = db["users"]
admins_collection = db["admins"]

# --- User Management ---
async def add_user(user_id: int) -> bool:
    """Adds a new user to the database. Returns True if new, False if existing."""
    if await users_collection.find_one({"user_id": user_id}):
        return False
    await users_collection.insert_one({"user_id": user_id})
    return True

async def get_total_users() -> int:
    """Returns the total number of users."""
    return await users_collection.count_documents({})

async def get_all_user_ids():
    """Returns a cursor for all user IDs."""
    return users_collection.find({}, {"user_id": 1})

# --- Admin Management ---
async def is_admin(user_id: int) -> bool:
    """Checks if a user is a Sudo Admin or a database admin."""
    if user_id in SUDO_ADMINS:
        return True
    return bool(await admins_collection.find_one({"admin_id": user_id}))

async def add_admin(user_id: int):
    """Adds a user to the admin list."""
    if not await is_admin(user_id):
        await admins_collection.insert_one({"admin_id": user_id})

async def remove_admin(user_id: int):
    """Removes a user from the admin list."""
    await admins_collection.delete_one({"admin_id": user_id})

async def get_all_admin_ids() -> list:
    """Gets all admin IDs from the database."""
    admins_cursor = admins_collection.find({}, {"admin_id": 1})
    return [admin['admin_id'] async for admin in admins_cursor]
