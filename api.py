import os
from datetime import date as date_type

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

import db
import formatting
from parser import parse_message

app = FastAPI()


class AddRequest(BaseModel):
    text: str


def _get_config():
    token = os.environ.get("API_TOKEN")
    user_id = os.environ.get("API_USER_ID")
    if not token or not user_id:
        raise HTTPException(status_code=503, detail="API not configured")
    return token, int(user_id)


@app.post("/add")
async def add(body: AddRequest, authorization: str = Header(None)):
    token, user_id = _get_config()
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    parsed = parse_message(body.text)
    if parsed is None:
        raise HTTPException(status_code=400, detail="Wrong input")
    if parsed["action"] != "add":
        raise HTTPException(status_code=400, detail="Only add actions supported via API")

    today = date_type.today().isoformat()
    _, cycle_seq = db.add_transaction(
        user_id=user_id,
        type_=parsed["type"],
        amount=parsed["amount"],
        category=parsed.get("category", "general"),
        date=today,
    )
    return {
        "ref": f"e{cycle_seq}",
        "type": parsed["type"],
        "amount": parsed["amount"],
        "category": parsed.get("category", "general"),
        "date": today,
    }
