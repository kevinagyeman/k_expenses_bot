from datetime import date as date_type
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import db
import formatting
from parser import parse_message


def _resolve_ref(user_id: int, parsed: dict):
    if "cycle_seq" in parsed:
        row = db.get_transaction_by_seq(user_id, parsed["cycle_seq"])
        ref = f"e{parsed['cycle_seq']}"
    else:
        row = db.get_transaction(user_id, parsed["short_id"])
        ref = parsed["short_id"]
    return (dict(row) if row else None), ref


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    user_id = update.effective_user.id

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    valid = [(p, l) for l in lines for p in [parse_message(l)] if p is not None]

    if not valid:
        await update.message.reply_text("Wrong input. Type /guide for help.")
        return

    if len(valid) == 1:
        await _handle_single(update, user_id, valid[0][0])
    else:
        await _handle_batch(update, user_id, [p for p, _ in valid])


async def _handle_single(update: Update, user_id: int, parsed: dict):
    action = parsed["action"]

    if action == "add":
        today = date_type.today().isoformat()
        _, cycle_seq = db.add_transaction(
            user_id=user_id,
            type_=parsed["type"],
            amount=parsed["amount"],
            category=parsed.get("category", "general"),
            date=today,
        )
        reply = formatting.confirm_add(
            parsed["type"], parsed["amount"], parsed.get("category", "general"), cycle_seq, today
        )
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

    elif action == "delete_last":
        row = db.delete_last_transaction(user_id)
        if row:
            ref = f"e{row['cycle_seq']}" if row.get("cycle_seq") else row["short_id"]
            await update.message.reply_text(f"`{ref}` deleted.", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Nothing to delete.", parse_mode=ParseMode.MARKDOWN)

    elif action == "delete":
        row, ref = _resolve_ref(user_id, parsed)
        if row:
            db.delete_transaction(user_id, row["short_id"])
            await update.message.reply_text(f"`{ref}` deleted.", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"`{ref}` not found.", parse_mode=ParseMode.MARKDOWN)

    elif action == "edit":
        row, ref = _resolve_ref(user_id, parsed)
        if not row:
            await update.message.reply_text(f"`{ref}` not found.", parse_mode=ParseMode.MARKDOWN)
            return
        category = row["category"] if parsed["type"] == "expense" else parsed["type"]
        db.update_transaction(user_id, row["short_id"], parsed["amount"], parsed["type"], category)
        updated = dict(db.get_transaction(user_id, row["short_id"]))
        await update.message.reply_text(formatting.confirm_edit(updated), parse_mode=ParseMode.MARKDOWN)


async def _handle_batch(update: Update, user_id: int, parsed_list: list[dict]):
    today = date_type.today().isoformat()
    results = []

    for parsed in parsed_list:
        action = parsed["action"]

        if action == "add":
            _, cycle_seq = db.add_transaction(
                user_id=user_id,
                type_=parsed["type"],
                amount=parsed["amount"],
                category=parsed.get("category", "general"),
                date=today,
            )
            results.append({
                "action": "add",
                "ref": f"e{cycle_seq}",
                "type": parsed["type"],
                "amount": parsed["amount"],
                "category": parsed.get("category", "general"),
            })

        elif action == "delete":
            row, ref = _resolve_ref(user_id, parsed)
            if row:
                db.delete_transaction(user_id, row["short_id"])
                results.append({"action": "delete", "ref": ref})

        elif action == "edit":
            row, ref = _resolve_ref(user_id, parsed)
            if row:
                category = row["category"] if parsed["type"] == "expense" else parsed["type"]
                db.update_transaction(user_id, row["short_id"], parsed["amount"], parsed["type"], category)
                updated = dict(db.get_transaction(user_id, row["short_id"]))
                results.append({
                    "action": "edit",
                    "ref": ref,
                    "type": updated["type"],
                    "amount": updated["amount"],
                    "category": updated["category"],
                })

    if results:
        await update.message.reply_text(formatting.batch_confirm(results), parse_mode=ParseMode.MARKDOWN)


async def cmd_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    start_date, rows = db.get_current_cycle(user_id)
    expense_rows = [r for r in rows if r["type"] == "expense"]
    await update.message.reply_text(formatting.cycle_expenses(start_date, expense_rows), parse_mode=ParseMode.MARKDOWN)


async def cmd_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cycles = db.get_all_cycles(user_id)
    await update.message.reply_text(formatting.all_cycles_summary(cycles), parse_mode=ParseMode.MARKDOWN)


async def cmd_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    start_date, rows = db.get_current_cycle(user_id)
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
