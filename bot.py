# bot.py

import os
import shutil
import zipfile
import asyncio
import subprocess
from functools import wraps
from telegraph import Telegraph, upload_file
import fitz  # PyMuPDF

from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait

from config import Config
import database as db

# Initialize services that don't require immediate network connection
telegraph = Telegraph()
app = Client(
    "EbookBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    in_memory=True
)


# --- Decorators for Admin Checks ---
def admin_required(func):
    @wraps(func)
    async def wrapped(client, message: Message, *args, **kwargs):
        user_id = message.from_user.id
        if user_id not in await db.get_all_admin_ids():
            return await message.reply_text("🚫 You are not authorized to use this command.")
        return await func(client, message, *args, **kwargs)
    return wrapped

def sudo_required(func):
    @wraps(func)
    async def wrapped(client, message: Message, *args, **kwargs):
        if not await db.is_sudo_admin(message.from_user.id):
            return await message.reply_text("⛔️ Only Sudo Admins can use this command.")
        return await func(client, message, *args, **kwargs)
    return wrapped


# --- Helper Functions ---
async def run_command(command: str):
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f"Command failed:\n{stderr.decode().strip()}")
    return stdout.decode().strip()

def get_conversion_options(input_ext: str) -> list:
    options = {
        "pdf": ["epub", "mobi", "azw3", "fb2", "cbz"],
        "epub": ["pdf", "mobi", "azw3", "fb2"],
        "mobi": ["pdf", "epub", "azw3", "fb2"],
        "azw3": ["pdf", "epub", "mobi", "fb2"],
        "fb2": ["pdf", "epub", "mobi", "azw3"],
        "cbz": ["pdf"]
    }
    return options.get(input_ext, [])


# --- Document Handler (Presents Buttons) ---
@app.on_message(filters.document)
async def document_handler(client, message: Message):
    if not message.document.file_name:
        return await message.reply_text("File must have a name.")
    input_ext = message.document.file_name.split('.')[-1].lower()
    output_options = get_conversion_options(input_ext)
    if not output_options:
        return await message.reply_text(
            f"Sorry, conversion from `.{input_ext}` is not supported.",
            quote=True
        )
    buttons = [
        InlineKeyboardButton(
            text=f"Convert to {out_ext.upper()}",
            callback_data=f"convert|{out_ext}"
        ) for out_ext in output_options
    ]
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    await message.reply_text(
        "**Choose the format you want to convert to:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        quote=True
    )


# --- Callback Handler (Performs Conversion) ---
@app.on_callback_query(filters.regex(r"^convert\|"))
async def conversion_callback(client, callback_query: CallbackQuery):
    original_message = callback_query.message.reply_to_message
    if not original_message or not original_message.document:
        return await callback_query.answer("Error: Original file not found.", show_alert=True)
    await callback_query.message.edit_text("`Downloading file...`")
    input_doc = original_message.document
    input_path = await original_message.download()
    file_name_no_ext = os.path.splitext(input_doc.file_name)[0]
    target_ext = callback_query.data.split("|")[1]
    output_path = f"{file_name_no_ext}.{target_ext}"
    try:
        await callback_query.message.edit_text(
            f"`Converting to {target_ext.upper()}... This may take a moment.`"
        )
        if input_doc.file_name.endswith(".cbz") and target_ext == "pdf":
            temp_dir = "temp_cbz_extract"
            os.makedirs(temp_dir, exist_ok=True)
            with zipfile.ZipFile(input_path, 'r') as cbz: cbz.extractall(temp_dir)
            img_files = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir)])
            if not img_files: raise ValueError("CBZ is empty.")
            pdf_doc = fitz.open()
            for img_path in img_files:
                img_doc = fitz.open(img_path)
                page = pdf_doc.new_page(width=img_doc[0].rect.width, height=img_doc[0].rect.height)
                page.insert_image(img_doc[0].rect, filename=img_path)
                img_doc.close()
            pdf_doc.save(output_path)
            pdf_doc.close()
            shutil.rmtree(temp_dir)
        elif input_doc.file_name.endswith(".pdf") and target_ext == "cbz":
            temp_dir = "temp_pdf_extract"
            os.makedirs(temp_dir, exist_ok=True)
            pdf_doc = fitz.open(input_path)
            for i, page in enumerate(pdf_doc):
                pix = page.get_pixmap()
                pix.save(os.path.join(temp_dir, f"{i:04d}.png"))
            pdf_doc.close()
            with zipfile.ZipFile(output_path, 'w') as cbz:
                for img_file in sorted(os.listdir(temp_dir)):
                    cbz.write(os.path.join(temp_dir, img_file), img_file)
            shutil.rmtree(temp_dir)
        else:
            await run_command(f'ebook-convert "{input_path}" "{output_path}"')
        await callback_query.message.edit_text("`Conversion complete! Uploading...`")
        await client.send_document(
            chat_id=callback_query.message.chat.id,
            document=output_path,
            caption=f"Converted from `{input_doc.file_name}`",
            reply_to_message_id=original_message.id
        )
        await callback_query.message.delete()
    except Exception as e:
        error_message = f"**Conversion Failed!**\n\n**Error:** `{e}`"
        await callback_query.message.edit_text(error_message)
        if Config.LOG_CHANNEL != 0:
            await client.send_message(Config.LOG_CHANNEL, f"⚠️ **Conversion Error**\n\n`{e}`")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if 'output_path' in locals() and os.path.exists(output_path): os.remove(output_path)


# --- Other Handlers (Start, Photo, Admin Commands) ---
@app.on_message(filters.command(["start", "help"]))
async def start_handler(client, message: Message):
    user_id = message.from_user.id
    if await db.add_user(user_id) and Config.LOG_CHANNEL != 0:
        try:
            await client.send_message(Config.LOG_CHANNEL, f"🎉 **New User**\n\n**Name:** {message.from_user.mention}\n**ID:** `{user_id}`")
        except Exception as e:
            print(f"Log channel error: {e}")
    settings = await db.get_settings()
    start_text = settings.get("start_message", Config.DEFAULT_START_MESSAGE)
    start_pic = settings.get("start_pic", Config.START_PIC)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Commands & Help", callback_data="show_help")]])
    try:
        await message.reply_photo(photo=start_pic, caption=start_text.format(first_name=message.from_user.first_name), reply_markup=keyboard)
    except Exception:
        await message.reply(
            text=start_text.format(first_name=message.from_user.first_name),
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML
        )

@app.on_callback_query(filters.regex("show_help"))
async def show_help_callback(client, callback_query):
    await callback_query.answer()
    help_text = """
**Here's how to use me:**

1️⃣ **Send any supported file** (`PDF`, `EPUB`, `MOBI`, `CBZ`, etc.).
2️⃣ **I will reply with buttons** for the available output formats.
3️⃣ **Click the button** for the format you want.
4️⃣ I will convert and upload the new file for you.

To upload an image to Telegraph, just send me the image.

**Admin Commands:**
- `/settings`: View current bot settings.
- `/setstart`: Reply to a message to set it as the start message.
- `/setpic`: Reply to a photo to set it as the start picture.
- `/stats`: Get bot usage statistics.
- `/broadcast`: Reply to a message to broadcast to all users (Sudo only).
- `/addadmin`: Promote a user to admin (Sudo only).
- `/rmadmin`: Demote an admin (Sudo only).
"""
    await callback_query.message.reply_text(help_text, quote=True, disable_web_page_preview=True)

@app.on_message(filters.photo)
async def telegraph_upload_handler(client, message: Message):
    msg = await message.reply_text("`Uploading to Telegraph...`", quote=True)
    try:
        photo_path = await message.download()
        response = upload_file(photo_path)
        telegraph_url = f"https://telegra.ph{response[0]}"
        await msg.edit(f"✨ **Uploaded!**\n\n🔗 **Link:** {telegraph_url}")
    except Exception as e:
        await msg.edit(f"**Error:** Could not upload image.\n`{e}`")
    finally:
        if 'photo_path' in locals() and os.path.exists(photo_path): os.remove(photo_path)

@app.on_message(filters.command("settings") & filters.private)
@admin_required
async def settings_handler(client, message: Message):
    settings = await db.get_settings()
    await message.reply_text(f"⚙️ **Bot Settings**\n\n**Start Message:**\n`{settings['start_message'][:200]}...`\n\n**Start Picture URL:**\n`{settings['start_pic']}`")

@app.on_message(filters.command("setstart") & filters.private)
@admin_required
async def set_start_handler(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.text: return await message.reply_text("Reply to text.")
    await db.update_setting("start_message", message.reply_to_message.text)
    await message.reply_text("✅ Start message updated!")

@app.on_message(filters.command("setpic") & filters.private)
@admin_required
async def set_pic_handler(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo: return await message.reply_text("Reply to a photo.")
    msg = await message.reply_text("`Processing...`")
    photo_path = await message.reply_to_message.download()
    try:
        response = upload_file(photo_path)
        telegraph_url = f"https://telegra.ph{response[0]}"
        await db.update_setting("start_pic", telegraph_url)
        await msg.edit("✅ Start picture updated!")
    except Exception as e:
        await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(photo_path): os.remove(photo_path)

@app.on_message(filters.command("stats") & filters.private)
@admin_required
async def stats_handler(client, message: Message):
    await message.reply_text(f"📊 **Total Users:** `{await db.get_user_count()}`")

@app.on_message(filters.command("broadcast") & filters.private)
@sudo_required
async def broadcast_handler(client, message: Message):
    if not message.reply_to_message: return await message.reply_text("Reply to a message to broadcast.")
    msg = await message.reply_text("📣 Broadcasting...")
    user_ids = await db.get_all_user_ids()
    success, failed = 0, 0
    for user_id in user_ids:
        try:
            await message.reply_to_message.copy(user_id)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(user_id)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.1)
    await msg.edit(f"**Broadcast Complete!**\n✅ Sent: `{success}`\n❌ Failed: `{failed}`")

async def get_user_from_message(message: Message):
    if message.reply_to_message: return message.reply_to_message.from_user.id
    if len(message.command) > 1: return message.command[1]
    return None

@app.on_message(filters.command("addadmin") & filters.private)
@sudo_required
async def add_admin_handler(client, message: Message):
    user_id = await get_user_from_message(message)
    if not user_id: return await message.reply_text("Reply to a user or give ID.")
    try:
        user = await client.get_users(user_id)
        await db.add_admin(user.id)
        await message.reply_text(f"✅ Promoted {user.mention} to admin.")
    except Exception as e: await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("rmadmin") & filters.private)
@sudo_required
async def remove_admin_handler(client, message: Message):
    user_id = await get_user_from_message(message)
    if not user_id: return await message.reply_text("Reply to a user or give ID.")
    try:
        user = await client.get_users(user_id)
        await db.remove_admin(user.id)
        await message.reply_text(f"❌ Demoted {user.mention}.")
    except Exception as e: await message.reply_text(f"Error: {e}")


# --- Main Application Execution ---
async def main():
    """Main function to start services and the bot."""
    # Connect to the database first
    await db.connect_db()

    # Create telegraph account (this is a synchronous call)
    telegraph.create_account(short_name='EbookBot')

    # Start the Pyrogram client
    await app.start()
    print("✅ Bot has started successfully!")
    
    # Keep the bot running until it's stopped
    await idle()
    
    # Stop the client when the process is interrupted
    print("Bot is stopping...")
    await app.stop()

if __name__ == "__main__":
    print("Bot instance is initializing...")
    asyncio.run(main())
    
