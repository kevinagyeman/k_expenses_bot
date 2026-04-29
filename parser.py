import re

SHORT_ID_RE = re.compile(r"^[A-Za-z0-9]{6}$")

_SALARY_RE = re.compile(r"^salary\s*:\s*(\d+(?:\.\d+)?)$", re.IGNORECASE)
_INCOME_PLUS_RE = re.compile(r"^\+(\d+(?:\.\d+)?)$")
_EXPENSE_BARE_RE = re.compile(r"^(\d+(?:\.\d+)?)$")

_RESERVED = {"salary", "income"}
_EXPENSE_CAT_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)\s*:\s*(\d+(?:\.\d+)?)$")

# e-ref patterns: e1 delete / e1 23 / e1 +23
_E_DELETE_RE = re.compile(r"^e(\d+)\s+delete$", re.IGNORECASE)
_E_AMOUNT_RE = re.compile(r"^e(\d+)\s+(\d+(?:\.\d+)?)$", re.IGNORECASE)
_E_INCOME_RE = re.compile(r"^e(\d+)\s+\+(\d+(?:\.\d+)?)$", re.IGNORECASE)

# legacy short_id patterns kept for backward compat
_EDIT_DELETE_RE = re.compile(r"^([A-Za-z0-9]{6})\s+delete$", re.IGNORECASE)
_EDIT_AMOUNT_RE = re.compile(r"^([A-Za-z0-9]{6})\s+(\d+(?:\.\d+)?)$")
_EDIT_INCOME_RE = re.compile(r"^([A-Za-z0-9]{6})\s+\+(\d+(?:\.\d+)?)$")

_DELETE_LAST_RE = re.compile(r"^delete$", re.IGNORECASE)


def parse_message(text: str) -> dict | None:
    text = text.strip()

    m = _SALARY_RE.match(text)
    if m:
        return {"action": "add", "type": "salary", "amount": float(m.group(1)), "category": "salary"}

    m = _INCOME_PLUS_RE.match(text)
    if m:
        return {"action": "add", "type": "income", "amount": float(m.group(1)), "category": "income"}

    if _DELETE_LAST_RE.match(text):
        return {"action": "delete_last"}

    m = _E_DELETE_RE.match(text)
    if m:
        return {"action": "delete", "cycle_seq": int(m.group(1))}

    m = _E_INCOME_RE.match(text)
    if m:
        return {"action": "edit", "cycle_seq": int(m.group(1)), "amount": float(m.group(2)), "type": "income"}

    m = _E_AMOUNT_RE.match(text)
    if m:
        return {"action": "edit", "cycle_seq": int(m.group(1)), "amount": float(m.group(2)), "type": "expense"}

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
    if m and m.group(1).lower() not in _RESERVED:
        return {"action": "add", "type": "expense", "amount": float(m.group(2)), "category": m.group(1).lower()}

    m = _EXPENSE_BARE_RE.match(text)
    if m:
        return {"action": "add", "type": "expense", "amount": float(m.group(1)), "category": "general"}

    return None
