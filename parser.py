import re

SHORT_ID_RE = re.compile(r"^[A-Za-z0-9]{6}$")

# income: 3333  or  income:3333
_INCOME_RE = re.compile(r"^income\s*:\s*(\d+(?:\.\d+)?)$", re.IGNORECASE)

# +21  or  +21.50
_INCOME_PLUS_RE = re.compile(r"^\+(\d+(?:\.\d+)?)$")

# 33.44  (bare number)
_EXPENSE_BARE_RE = re.compile(r"^(\d+(?:\.\d+)?)$")

# hobby:23.78  (category:amount)
_EXPENSE_CAT_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)\s*:\s*(\d+(?:\.\d+)?)$")

# uhueYe delete
_EDIT_DELETE_RE = re.compile(r"^([A-Za-z0-9]{6})\s+delete$", re.IGNORECASE)

# uhueYe 23  (edit amount → expense)
_EDIT_AMOUNT_RE = re.compile(r"^([A-Za-z0-9]{6})\s+(\d+(?:\.\d+)?)$")

# uhueYe +12  (edit → income)
_EDIT_INCOME_RE = re.compile(r"^([A-Za-z0-9]{6})\s+\+(\d+(?:\.\d+)?)$")


def parse_message(text: str) -> dict | None:
    text = text.strip()

    m = _INCOME_RE.match(text)
    if m:
        return {"action": "add", "type": "income", "amount": float(m.group(1)), "category": "income"}

    m = _INCOME_PLUS_RE.match(text)
    if m:
        return {"action": "add", "type": "income", "amount": float(m.group(1)), "category": "income"}

    m = _EDIT_DELETE_RE.match(text)
    if m:
        return {"action": "delete", "short_id": m.group(1)}

    m = _EDIT_INCOME_RE.match(text)
    if m:
        return {"action": "edit", "short_id": m.group(1), "amount": float(m.group(2)), "type": "income"}

    m = _EDIT_AMOUNT_RE.match(text)
    if m:
        return {"action": "edit", "short_id": m.group(1), "amount": float(m.group(2)), "type": "expense"}

    m = _EXPENSE_CAT_RE.match(text)
    if m:
        return {"action": "add", "type": "expense", "amount": float(m.group(2)), "category": m.group(1).lower()}

    m = _EXPENSE_BARE_RE.match(text)
    if m:
        return {"action": "add", "type": "expense", "amount": float(m.group(1)), "category": "general"}

    return None
