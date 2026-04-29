import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import db
from handlers import (
    handle_message,
    cmd_all_expenses,
    cmd_month,
    cmd_guide,
    cmd_start,
)

load_dotenv()


def main():
    db.init_db()

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Copy .env.example to .env and add your token.")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("guide", cmd_guide))
    app.add_handler(CommandHandler("all_expenses", cmd_all_expenses))
    app.add_handler(CommandHandler("month", cmd_month))
    # Telegram commands can't have hyphens; support /all-expenses via text fallback
    app.add_handler(MessageHandler(filters.Regex(r"^/all-expenses$"), cmd_all_expenses))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
