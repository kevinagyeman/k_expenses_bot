import os

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from telegram import Bot
from telegram.constants import ParseMode

import db
import core

app = FastAPI()


class MessageRequest(BaseModel):
    text: str


def _get_config():
    token = os.environ.get("API_TOKEN")
    user_id = os.environ.get("API_USER_ID")
    if not token or not user_id:
        raise HTTPException(status_code=503, detail="API not configured")
    return token, int(user_id)


@app.post("/message")
async def message(body: MessageRequest, authorization: str = Header(None)):
    token, user_id = _get_config()
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    reply = core.process_text(user_id, body.text)

    bot_token = os.environ.get("BOT_TOKEN")
    if bot_token:
        async with Bot(token=bot_token) as bot:
            await bot.send_message(chat_id=user_id, text=reply, parse_mode=ParseMode.MARKDOWN)

    return {"reply": reply}
