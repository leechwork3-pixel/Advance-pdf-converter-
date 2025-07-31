# bot/handlers.py
import os
import logging
import asyncio
from functools import wraps
from telegraph import Telegraph, exceptions as telegraph_exceptions

from telegram import Update, InputFile
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.config import LOG_CHANNEL, SUDO_ADMINS, TELEGRAPH_SHORT_NAME
from bot.database import add_user, get_total_users, is_admin, add_admin, remove_admin, get_all_user_ids
from bot.utils import convert_cbz_to_pdf, convert_pdf_to_cbz

# Setup Telegraph
telegraph = Telegraph()
telegraph.create_account(short_name=TELEGRAPH_SHORT_NAME)

# --- Decorators for permission checking ---
def sudo_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in SUDO_ADMINS:
            await update.message.reply_text("You don't have permission to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not await is_admin(user_id):
            await update.message.reply_text("You must be an admin to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new_user = await add_user(user.id)
    
    if is_new_user and LOG_CHANNEL != 0:
        try:
            log_message = (
                f"🎉 New User Alert!\n\n"
                f"**User ID:** `{user.id}`\n"
                f"**First Name:** {user.first_name}\n"
                f"**Username:** @{user.username if user.username else 'N/A'}"
            )
            await context.bot.send_message(chat_id=LOG_CHANNEL, text=log_message, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logging.error(f"Failed to send new user log: {e}")

    await update.message.reply_html(
        f"👋 Hello, <b>{user.first_name}!</b>\n\n"
        "I am your E-book and Telegraph assistant. Send me a <b>CBZ</b> or <b>PDF</b> file to convert it.\n\n"
        "To upload an image to Telegraph, simply send it to me or reply to an image with /telegraph."
    )

@sudo_only
async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addadmin <user_id>")
        return
    
    await add_admin(user_id)
    await update.message.reply_text(f"User `{user_id}` has been promoted to admin.", parse_mode=ParseMode.MARKDOWN)

@sudo_only
async def rm_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /rmadmin <user_id>")
        return

    await remove_admin(user_id)
    await update.message.reply_text(f"User `{user_id}` has been demoted.", parse_mode=ParseMode.MARKDOWN)

@admin_only
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = await get_total_users()
    await update.message.reply_text(f"📊 **Bot Stats**\n\nTotal Users: {total_users}")

@sudo_only
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_to_broadcast = update.message.reply_to_message
    if not message_to_broadcast:
        await update.message.reply_text("Please reply to a message to broadcast it.")
        return

    user_ids = get_all_user_ids()
    success_count = 0
    fail_count = 0
    
    status_msg = await update.message.reply_text("Broadcasting... this may take a while.")
    
    async for user in user_ids:
        try:
            await context.bot.copy_message(chat_id=user['user_id'], from_chat_id=update.message.chat_id, message_id=message_to_broadcast.message_id)
            success_count += 1
        except Exception:
            fail_count += 1
        await asyncio.sleep(0.1) # To avoid API rate limits

    await status_msg.edit_text(f"📢 Broadcast complete!\n\n✅ Sent to: {success_count} users\n❌ Failed for: {fail_count} users")

# --- Message Handlers ---
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.document:
        return

    file_name = message.document.file_name.lower()
    file_id = message.document.file_id
    
    processing_msg = await message.reply_text("⏳ Processing your file...")
    
    downloaded_file_path = f"downloads/{file_id}_{file_name}"
    os.makedirs("downloads", exist_ok=True)
    
    try:
        file_object = await context.bot.get_file(file_id)
        await file_object.download_to_drive(downloaded_file_path)

        if file_name.endswith(".cbz"):
            output_path = downloaded_file_path.replace(".cbz", ".pdf")
            await convert_cbz_to_pdf(downloaded_file_path, output_path)
            await message.reply_document(document=InputFile(output_path), caption="Converted CBZ to PDF ✨")
        elif file_name.endswith(".pdf"):
            output_path = downloaded_file_path.replace(".pdf", ".cbz")
            await convert_pdf_to_cbz(downloaded_file_path, output_path)
            await message.reply_document(document=InputFile(output_path), caption="Converted PDF to CBZ ✨")
        else:
            await processing_msg.edit_text("Unsupported file type. Please send a PDF or CBZ file.")
            return

    except Exception as e:
        logging.error(f"File handling error: {e}")
        await processing_msg.edit_text(f"An error occurred: {e}")
    finally:
        await processing_msg.delete()
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)

async def telegraph_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    photo_message = message.reply_to_message if message.reply_to_message else message

    if not photo_message or not photo_message.photo:
        if message.reply_to_message:
            await message.reply_text("Please reply to an image.")
        return

    status_msg = await message.reply_text("Uploading to Telegraph...")
    
    try:
        photo = photo_message.photo[-1] # Get the highest resolution
        photo_file = await context.bot.get_file(photo.file_id)
        
        # Download the photo to a temporary path
        temp_photo_path = f"temp_{photo.file_id}.jpg"
        await photo_file.download_to_drive(temp_photo_path)
        
        # Upload to Telegraph
        response = telegraph.upload_file(temp_photo_path)
        link = f"https://telegra.ph{response[0]['src']}"
        
        await status_msg.edit_text(
            f"Image uploaded successfully!\n\n🔗 **Link:** {link}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=False
        )
    except telegraph_exceptions.TelegraphException as e:
        await status_msg.edit_text(f"Telegraph error: {e}")
    except Exception as e:
        await status_msg.edit_text(f"An error occurred: {e}")
    finally:
        if 'temp_photo_path' in locals() and os.path.exists(temp_photo_path):
            os.remove(temp_photo_path)
