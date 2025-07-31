# bot/handlers/admin_handlers.py
import asyncio
import logging
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

from bot.config import SUDO_ADMINS
from bot.database import is_admin, add_admin, remove_admin, get_total_users, get_all_user_ids, set_setting

# --- States for ConversationHandler ---
(AWAIT_START_MSG, AWAIT_START_IMG, AWAIT_BROADCAST_MSG) = range(3)

# --- Decorators ---
def sudo_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id not in SUDO_ADMINS:
            await update.callback_query.answer("Permission denied.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not await is_admin(update.effective_user.id):
            if update.callback_query: await update.callback_query.answer("Admins only.", show_alert=True)
            else: await update.message.reply_text("This command is for admins only.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- Settings Panel ---
@admin_only
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Set Start Message", callback_data="set_start_msg")],
        [InlineKeyboardButton("🖼️ Set Start Image", callback_data="set_start_img")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("✖️ Close", callback_data="close_settings")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ **Admin Settings**", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# --- Callback Handlers for Settings ---
async def settings_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "set_start_msg":
        await query.message.reply_text("Please send the new start message. Use HTML for formatting.\n\nExample: `<b>Welcome!</b>`")
        return AWAIT_START_MSG
    elif data == "set_start_img":
        await query.message.reply_text("Please send the new start image.")
        return AWAIT_START_IMG
    elif data == "broadcast":
        await query.message.reply_text("Please reply to this message with the content you want to broadcast.")
        return AWAIT_BROADCAST_MSG
    elif data == "stats":
        total_users = await get_total_users()
        await query.message.reply_text(f"📊 **Bot Stats**\n\nTotal Users: {total_users}")
    elif data == "close_settings":
        await query.message.delete()

# --- Conversation Handlers for Settings ---
async def set_start_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_setting("start_message", update.message.text_html)
    await update.message.reply_text("✅ Start message updated successfully!")
    return ConversationHandler.END

async def set_start_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await set_setting("start_image_file_id", file_id)
        await update.message.reply_text("✅ Start image updated successfully!")
    else:
        await update.message.reply_text("That's not an image. Operation cancelled.")
    return ConversationHandler.END

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_to_broadcast = update.message
    user_ids_cursor = get_all_user_ids()
    success, failed = 0, 0
    
    status_msg = await update.message.reply_text("Broadcasting...")
    
    async for user in user_ids_cursor:
        try:
            await context.bot.copy_message(chat_id=user['user_id'], from_chat_id=update.message.chat_id, message_id=message_to_broadcast.message_id)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.1)

    await status_msg.edit_text(f"📢 Broadcast complete!\n\n✅ Sent to: {success}\n❌ Failed for: {failed}")
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# --- Sudo Commands ---
@sudo_only
async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This is a command, not a callback, so it gets user from message
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        return await update.message.reply_text("Sudo admins only.")
    try:
        target_id = int(context.args[0])
        await add_admin(target_id)
        await update.message.reply_text(f"User `{target_id}` promoted to admin.", parse_mode=ParseMode.MARKDOWN)
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addadmin <user_id>")

@sudo_only
async def rm_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        return await update.message.reply_text("Sudo admins only.")
    try:
        target_id = int(context.args[0])
        await remove_admin(target_id)
        await update.message.reply_text(f"User `{target_id}` demoted.", parse_mode=ParseMode.MARKDOWN)
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /rmadmin <user_id>")
        
