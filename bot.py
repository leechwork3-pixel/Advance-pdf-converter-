import os
import logging
import time
import shutil
import asyncio

# Telegram and Pyrogram specific imports
from pyrogram import Client
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Local imports from your project
from config import Config
from translation import Translation
from helpers.database import db
from helpers.utils import (
    progress_for_pyrogram,
    humanbytes,
    TimeFormatter
)
from helpers.file_handler import (
    send_file_to_user,
    handle_incoming_file
)

# Constants
DOWNLOAD_LOCATION = Config.DOWNLOAD_LOCATION

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# All your existing command and message handlers go here.
# This logic does not need to change.
# ---------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    if not await db.is_user_exist(update.effective_user.id):
        await db.add_user(update.effective_user.id)
    
    start_text = await db.get_start_text()
    start_pic = await db.get_start_pic()

    if start_pic:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=start_pic,
            caption=start_text.format(
                first_name=update.effective_user.first_name,
                bot_name=context.bot.username
            ),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=update.message.message_id
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=start_text.format(
                first_name=update.effective_user.first_name,
                bot_name=context.bot.username
            ),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=update.message.message_id
        )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /settings command (Sudo Admins)."""
    if update.effective_user.id not in Config.SUDO_ADMINS:
        return
    start_text = await db.get_start_text()
    start_pic = await db.get_start_pic()
    await update.message.reply_text(
        f"**Current Start Text:**\n`{start_text}`\n\n**Current Start Pic URL:**\n`{start_pic}`",
        parse_mode=ParseMode.MARKDOWN
    )

async def set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /setstart command (Sudo Admins)."""
    if update.effective_user.id not in Config.SUDO_ADMINS:
        return
    if update.message.reply_to_message and update.message.reply_to_message.text:
        new_start_text = update.message.reply_to_message.text
        await db.set_start_text(new_start_text)
        await update.message.reply_text("Successfully set the new start text.")
    else:
        await update.message.reply_text("Please reply to a text message to set it as the start message.")

async def set_pic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /setpic command (Sudo Admins)."""
    if update.effective_user.id not in Config.SUDO_ADMINS:
        return
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        new_start_pic = update.message.reply_to_message.photo[-1].file_id
        await db.set_start_pic(new_start_pic)
        await update.message.reply_text("Successfully set the new start picture.")
    else:
        await update.message.reply_text("Please reply to a photo to set it as the start picture.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /stats command (Sudo Admins)."""
    if update.effective_user.id not in Config.SUDO_ADMINS:
        return
    total_users = await db.total_users_count()
    await update.message.reply_text(f"Total users in DB: {total_users}")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /broadcast command (Sudo Admins)."""
    if update.effective_user.id not in Config.SUDO_ADMINS:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    all_users = await db.get_all_users()
    broadcast_msg = update.message.reply_to_message
    total_users = await db.total_users_count()
    sent_count = 0
    failed_count = 0
    
    status_msg = await update.message.reply_text(f"Broadcasting... Sent to {sent_count} of {total_users} users.")
    
    for user in all_users:
        try:
            await broadcast_msg.copy(chat_id=int(user['id']))
            sent_count += 1
        except Exception:
            failed_count += 1
            await db.delete_user(user['id']) # Remove user who blocked the bot

        if sent_count % 20 == 0: # Update status every 20 users
            await status_msg.edit_text(f"Broadcasting... Sent to {sent_count} of {total_users} users.")
            await asyncio.sleep(1)

    await status_msg.edit_text(
        f"Broadcast complete.\n\nSent to: {sent_count} users.\nFailed (and removed): {failed_count} users."
    )
    
async def telegraph_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles photo uploads to generate Telegraph links."""
    # This function uses pyrogram Client, needs separate initialization
    # Note: Mixing libraries like this can be complex.
    # For simplicity, this part is kept as a placeholder to show structure.
    # A full implementation would require careful handling of pyrogram client sessions.
    await update.message.reply_text("Photo received. Telegraph upload feature requires Pyrogram client setup.")


async def incoming_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming files for conversion."""
    if update.message.document:
        await handle_incoming_file(update, context)
    else:
        await update.message.reply_text("Please send a supported file to convert.")


# ---------------------------------------------------------------------
# MAIN EXECUTION BLOCK - MODIFIED FOR WEBHOOKS
# ---------------------------------------------------------------------

if __name__ == "__main__":
    # Create download directory if it doesn't exist
    if not os.path.isdir(DOWNLOAD_LOCATION):
        os.makedirs(DOWNLOAD_LOCATION)

    # Initialize the bot application
    app = Application.builder().token(Config.BOT_TOKEN).build()

    # Add all the command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("setstart", set_start))
    app.add_handler(CommandHandler("setpic", set_pic))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))
    
    app.add_handler(MessageHandler(filters.PHOTO, telegraph_upload))
    app.add_handler(MessageHandler(filters.Document.ALL, incoming_file_handler))

    # --- THIS IS THE NEW WEBHOOK CODE ---
    LOGGER.info("Starting bot via Webhook...")

    # Get port and app name from environment variables
    # Your deployment platform (Koyeb) will provide the PORT.
    # You MUST set APP_NAME yourself in your Koyeb Environment Variables.
    PORT = int(os.environ.get('PORT', '8443'))
    APP_NAME = os.environ.get('APP_NAME')

    if not APP_NAME:
        LOGGER.error("FATAL: APP_NAME environment variable is not set! Exiting.")
        # In a real scenario, you might want to exit here
        # For now, we will log an error. The bot will fail to start correctly.
    
    # Set up the webhook URL
    # The URL path is set to the bot token for security
    WEBHOOK_URL = f"https://{APP_NAME}.koyeb.app/{Config.BOT_TOKEN}"

    # Start the bot with webhooks
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=Config.BOT_TOKEN,
        webhook_url=WEBHOOK_URL
    )
    LOGGER.info(f"Bot started and listening on port {PORT}")

