from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import db
import formatting
import core


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""
    reply = core.process_text(user_id, text)
    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


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
        "`+50` — add extra income\n"
        "`e2 delete` — delete expense #2\n"
        "`delete` — delete last added\n\n"
        "Type /guide for full help.",
        parse_mode=ParseMode.MARKDOWN,
    )
