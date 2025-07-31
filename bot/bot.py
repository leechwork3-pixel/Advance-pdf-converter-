# bot/bot.py
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

from bot.config import BOT_TOKEN
from bot.handlers.user_handlers import start_command, file_handler, telegraph_handler
from bot.handlers.admin_handlers import (
    settings_command, settings_callback_handler,
    set_start_message_handler, set_start_image_handler, broadcast_handler,
    cancel_conversation, add_admin_command, rm_admin_command,
    AWAIT_START_MSG, AWAIT_START_IMG, AWAIT_BROADCAST_MSG
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for settings
    settings_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(settings_callback_handler)],
        states={
            AWAIT_START_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_start_message_handler)],
            AWAIT_START_IMG: [MessageHandler(filters.PHOTO, set_start_image_handler)],
            AWAIT_BROADCAST_MSG: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_message=False
    )

    # --- Register Handlers ---
    # Sudo Commands
    application.add_handler(CommandHandler("addadmin", add_admin_command))
    application.add_handler(CommandHandler("rmadmin", rm_admin_command))

    # Admin Commands
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(settings_conv_handler)

    # User Commands & Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("telegraph", telegraph_handler))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, telegraph_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    
    logging.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
    
