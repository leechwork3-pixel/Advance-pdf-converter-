# Advance-pdf-converter-
List of Bot Commands
Here is a quick reference for all the commands you will use on Telegram.
User Commands
 * /start or /help: Shows the main welcome message and command list.
 * Send a file: Send any supported ebook (EPUB, MOBI, AZW3, FB2, CBZ, PDF) to convert it.
 * Send an image: Send any photo to get a permanent Telegraph link for it.
Admin Commands
 * /settings: Displays the current start message and picture URL.
 * /setstart: Reply to a text message to make it the new start message. Supports HTML.
 * /setpic: Reply to a photo to make it the new start picture.
 * /stats: Shows the total number of users in the database.
 * /broadcast: Reply to any message (text, photo, file, etc.) to send a copy to all bot users. (Sudo Admin only).
Sudo Admin Commands
 * /addadmin: Reply to a user's message or provide their Telegram ID to grant them admin privileges.
 * /rmadmin: Reply to a user's message or provide their Telegram ID to revoke their admin privileges.
9. Deployment on Koyeb
 * Get Credentials: Collect API_ID, API_HASH, BOT_TOKEN, MONGO_URI, your user ID for SUDO_ADMINS, and the LOG_CHANNEL ID.
 * Push to GitHub: Create a GitHub repository and push all 6 files to it.
 * Deploy on Koyeb:
   * In Koyeb, click Create App.
   * Select GitHub and your repository.
   * Koyeb will automatically detect the Dockerfile.
   * Go to the Environment variables section.
   * Add each variable from your config.py file (e.g., API_ID, BOT_TOKEN, MONGO_URI, SUDO_ADMINS, etc.) with its corresponding value.
   * Click Deploy.
Koyeb will build the Docker container, which includes installing Calibre, and then start your bot. The initial build may take a few minutes due to the Calibre installation.
How to Use the Bot
The user experience is now more intuitive:
 * Send a File: A user sends any supported file (e.g., my-book.epub).
 * Choose Format: The bot replies with buttons: "Convert to PDF," "Convert to MOBI," etc.
 * Click a Button: The user clicks their desired format.
 * Receive Converted File: The bot processes the request and sends back the new file (e.g., my-book.pdf).
All other admin commands and features work exactly as before. Deploy this updated code to Koyeb using the same method, and your bot will have this powerful new interactive feature.
