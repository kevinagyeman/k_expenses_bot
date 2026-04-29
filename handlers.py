from datetime import date as date_type
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import db
import formatting
from parser import parse_message


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    parsed = parse_message(text)
    if parsed is None:
        return

    action = parsed["action"]

    if action == "add":
        today = date_type.today().isoformat()
        short_id = db.add_transaction(
            type_=parsed["type"],
            amount=parsed["amount"],
            category=parsed.get("category", "general"),
            date=today,
        )
        reply = formatting.confirm_add(
            parsed["type"], parsed["amount"], parsed.get("category", "general"), short_id, today
        )
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

    elif action == "delete":
        ok = db.delete_transaction(parsed["short_id"])
        if ok:
            await update.message.reply_text(f"`{parsed['short_id']}` deleted.", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"ID `{parsed['short_id']}` not found.", parse_mode=ParseMode.MARKDOWN)

    elif action == "edit":
        row = db.get_transaction(parsed["short_id"])
        if not row:
            await update.message.reply_text(
                f"ID `{parsed['short_id']}` not found.", parse_mode=ParseMode.MARKDOWN
            )
            return
        category = row["category"] if parsed["type"] == "expense" else parsed["type"]
        db.update_transaction(parsed["short_id"], parsed["amount"], parsed["type"], category)
        updated = dict(db.get_transaction(parsed["short_id"]))
        await update.message.reply_text(formatting.confirm_edit(updated), parse_mode=ParseMode.MARKDOWN)


async def cmd_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_date, rows = db.get_current_cycle()
    expense_rows = [r for r in rows if r["type"] == "expense"]
    await update.message.reply_text(formatting.cycle_expenses(start_date, expense_rows), parse_mode=ParseMode.MARKDOWN)


async def cmd_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cycles = db.get_all_cycles()
    await update.message.reply_text(formatting.all_cycles_summary(cycles), parse_mode=ParseMode.MARKDOWN)


async def cmd_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_date, rows = db.get_current_cycle()
    await update.message.reply_text(formatting.month_summary(start_date, rows), parse_mode=ParseMode.MARKDOWN)


async def cmd_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(formatting.GUIDE, parse_mode=ParseMode.MARKDOWN)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Welcome to your Expense Tracker*\n\n"
        "Quick start:\n"
        "`42.50` — add expense\n"
        "`food:15` — add categorised expense\n"
        "`salary:3000` — add salary (starts new cycle)\n"
        "`+50` — add extra income\n\n"
        "Type /guide for full help.",
        parse_mode=ParseMode.MARKDOWN,
    )
