import asyncio
import os

import uvicorn
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

import db
from api import app as api_app
from handlers import (
    handle_message,
    cmd_expenses,
    cmd_all,
    cmd_month,
    cmd_guide,
    cmd_start,
)

load_dotenv()


async def main():
    db.init_db()

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Copy .env.example to .env and add your token.")

    tg_app = ApplicationBuilder().token(token).build()
    tg_app.add_handler(CommandHandler("start", cmd_start))
    tg_app.add_handler(CommandHandler("guide", cmd_guide))
    tg_app.add_handler(CommandHandler("expenses", cmd_expenses))
    tg_app.add_handler(CommandHandler("all", cmd_all))
    tg_app.add_handler(CommandHandler("month", cmd_month))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    api_port = int(os.environ.get("API_PORT", 8080))
    server = uvicorn.Server(uvicorn.Config(api_app, host="0.0.0.0", port=api_port, log_level="warning"))

    async with tg_app:
        await tg_app.start()
        await tg_app.updater.start_polling()
        print(f"Bot started. API listening on port {api_port}. Press Ctrl+C to stop.")
        await server.serve()
        await tg_app.updater.stop()
        await tg_app.stop()


if __name__ == "__main__":
    asyncio.run(main())
