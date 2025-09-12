"""Main entry point for Telegram bot."""

import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from mega_bot.config import Config
from mega_bot.logger import LOGGER
from mega_bot.bot.handlers import (
    start_command,
    mega_command,
    status_command,
    cancel_command,
    handle_text,
)


async def main():
    """Main function to run the Telegram bot."""
    # Validate configuration
    Config.validate()

    LOGGER.info("Starting MEGA Downloader Bot...")

    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("mega", mega_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    # Handle plain text messages (for MEGA links)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    LOGGER.info("Bot handlers registered")

    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    LOGGER.info("Bot is running! Press Ctrl+C to stop.")

    try:
        # Keep the bot running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        LOGGER.info("Received stop signal")
    finally:
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
