import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your Telegram Bot Token
TOKEN = "8058616440:AAGU2lHCA2fb1f6o0mcYmfAok8R8UMLDAho"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Hi! I will echo your text messages and identify other media types."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles different message types and replies accordingly."""
    message = update.message

    # 1. Check for a text message
    if message.text:
        # Echo the text message back to the user
        await message.reply_text(message.text)

    # 2. Check for a photo
    elif message.photo:
        await message.reply_text('photo')

    # 3. Check for a video
    elif message.video:
        await message.reply_text('video')

    # 4. Check for a voice message
    elif message.voice:
        await message.reply_text('voice')

	# 5. Check for a document (like PDF)
    elif message.document and message.document.mime_type == "application/pdf":
        await message.reply_text('pdf')

    # 6. Handle any other type of message
    else:
        await message.reply_text("I can only handle text, photo, video, voice messages and pdf.")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - handle_message
    # We use filters.ALL to catch any type of message
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
