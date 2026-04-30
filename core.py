from datetime import date as date_type

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


def process_text(user_id: int, text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    valid = [p for l in lines for p in [parse_message(l)] if p is not None]

    if not valid:
        return "Wrong input. Type /guide for help."

    if len(valid) == 1:
        return _process_single(user_id, valid[0])
    return _process_batch(user_id, valid)


def _process_single(user_id: int, parsed: dict) -> str:
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
        return formatting.confirm_add(
            parsed["type"], parsed["amount"], parsed.get("category", "general"), cycle_seq, today
        )

    if action == "delete_last":
        row = db.delete_last_transaction(user_id)
        if not row:
            return "Nothing to delete."
        ref = f"e{row['cycle_seq']}" if row.get("cycle_seq") else row["short_id"]
        sign = "+" if row["type"] in ("salary", "income") else "-"
        return f"`{ref}` {sign}{row['amount']:.2f} | {row['category']} deleted."

    if action == "delete":
        row, ref = _resolve_ref(user_id, parsed)
        if not row:
            return f"`{ref}` not found."
        db.delete_transaction(user_id, row["short_id"])
        sign = "+" if row["type"] in ("salary", "income") else "-"
        return f"`{ref}` {sign}{row['amount']:.2f} | {row['category']} deleted."

    if action == "edit":
        row, ref = _resolve_ref(user_id, parsed)
        if not row:
            return f"`{ref}` not found."
        category = row["category"] if parsed["type"] == "expense" else parsed["type"]
        db.update_transaction(user_id, row["short_id"], parsed["amount"], parsed["type"], category)
        updated = dict(db.get_transaction(user_id, row["short_id"]))
        return formatting.confirm_edit(updated)

    return "Wrong input. Type /guide for help."


def _process_batch(user_id: int, parsed_list: list[dict]) -> str:
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
                results.append({"action": "delete", "ref": ref, "type": row["type"], "amount": row["amount"], "category": row["category"]})

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

    return formatting.batch_confirm(results) if results else "Nothing processed."
