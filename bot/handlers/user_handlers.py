# bot/handlers/user_handlers.py
import os
import logging
from telegraph import Telegraph, exceptions as telegraph_exceptions

from telegram import Update, InputFile
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.config import LOG_CHANNEL, TELEGRAPH_SHORT_NAME, DEFAULT_START_MESSAGE
from bot.database import add_user, get_setting
from bot.utils import convert_with_calibre, convert_pdf_to_cbz

# Setup Telegraph
telegraph = Telegraph()
telegraph.create_account(short_name=TELEGRAPH_SHORT_NAME)

# --- User-facing Commands ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new_user = await add_user(user.id)
    
    if is_new_user and LOG_CHANNEL != 0:
        try:
            await context.bot.send_message(
                chat_id=LOG_CHANNEL,
                text=(
                    f"🎉 New User Alert!\n\n"
                    f"**ID:** `{user.id}`\n"
                    f"**Name:** {user.first_name}\n"
                    f"**Username:** @{user.username or 'N/A'}"
                ),
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logging.error(f"Failed to send new user log: {e}")
            
    # Fetch custom start message and image from DB
    start_message = await get_setting("start_message") or DEFAULT_START_MESSAGE
    start_image_id = await get_setting("start_image_file_id")
    
    formatted_message = start_message.format(first_name=user.first_name)

    if start_image_id:
        try:
            await update.message.reply_photo(
                photo=start_image_id,
                caption=formatted_message,
                parse_mode=ParseMode.HTML
            )
        except Exception: # Fallback if image is invalid
            await update.message.reply_html(formatted_message)
    else:
        await update.message.reply_html(formatted_message)

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.document: return

    file_name = message.document.file_name
    file_id = message.document.file_id
    file_ext = os.path.splitext(file_name)[1].lower()
    
    supported_to_pdf = ['.epub', '.mobi', '.azw3', '.fb2', '.cbz']
    
    if file_ext not in supported_to_pdf and file_ext != '.pdf':
        await message.reply_text("Unsupported file type. I can handle: EPUB, MOBI, AZW3, FB2, CBZ, and PDF.")
        return

    processing_msg = await message.reply_text(f"⏳ Processing `{file_name}`...")
    
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    input_path = os.path.join(download_dir, f"{file_id}{file_ext}")
    
    try:
        file_object = await context.bot.get_file(file_id)
        await file_object.download_to_drive(input_path)

        output_path = ""
        caption = ""

        if file_ext in supported_to_pdf:
            output_path = input_path.rsplit('.', 1)[0] + ".pdf"
            await convert_with_calibre(input_path, output_path)
            caption = "Converted to PDF ✨"
        elif file_ext == '.pdf':
            output_path = input_path.rsplit('.', 1)[0] + ".cbz"
            await convert_pdf_to_cbz(input_path, output_path)
            caption = "Converted to CBZ ✨"

        await message.reply_document(document=InputFile(output_path), caption=caption)
        
    except Exception as e:
        logging.error(f"File handling error: {e}")
        await processing_msg.edit_text(f"An error occurred: {str(e)}")
    finally:
        await processing_msg.delete()
        if os.path.exists(input_path): os.remove(input_path)
        if 'output_path' in locals() and os.path.exists(output_path): os.remove(output_path)


async def telegraph_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    photo_message = message.reply_to_message or message

    if not photo_message or not photo_message.photo:
        return

    status_msg = await message.reply_text("Uploading to Telegraph...")
    
    try:
        photo_file = await photo_message.photo[-1].get_file()
        temp_photo_path = f"temp_{photo_file.file_id}.jpg"
        await photo_file.download_to_drive(temp_photo_path)
        
        response = telegraph.upload_file(temp_photo_path)
        link = f"https://telegra.ph{response[0]['src']}"
        
        await status_msg.edit_text(f"Image uploaded!\n\n🔗 **Link:** {link}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"An error occurred: {e}")
    finally:
        if 'temp_photo_path' in locals() and os.path.exists(temp_photo_path):
            os.remove(temp_photo_path)
