from datetime import date as date_type
from collections import defaultdict


def _fmt_date(iso: str) -> str:
    d = date_type.fromisoformat(iso)
    return d.strftime("%d/%m/%y")


def _fmt_amount(amount: float) -> str:
    return f"{amount:.2f}"


def confirm_add(type_: str, amount: float, category: str, short_id: str, date: str) -> str:
    if type_ == "salary":
        return f"Salary added — new cycle started\n+{_fmt_amount(amount)} | {_fmt_date(date)} | `{short_id}`"
    if type_ == "income":
        return f"Income added\n+{_fmt_amount(amount)} | {_fmt_date(date)} | `{short_id}`"
    return f"Expense added\n-{_fmt_amount(amount)} | {category} | {_fmt_date(date)} | `{short_id}`"


def confirm_edit(row: dict) -> str:
    sign = "+" if row["type"] in ("income", "salary") else "-"
    return (
        f"Updated\n"
        f"{sign}{_fmt_amount(row['amount'])} | {row['category']} | "
        f"{_fmt_date(row['date'])} | `{row['short_id']}`"
    )


def cycle_expenses(start_date: str | None, rows: list) -> str:
    if not rows:
        return "No expenses in the current cycle yet."
    today = date_type.today().strftime("%d/%m/%y")
    period = f"{_fmt_date(start_date)} → {today}" if start_date else today
    lines = [f"*Expenses — {period}*\n"]
    for r in rows:
        lines.append(
            f"`{r['short_id']}` | {_fmt_amount(r['amount'])} | {r['category']} | {_fmt_date(r['date'])}"
        )
    return "\n".join(lines)


def month_summary(start_date: str | None, rows: list) -> str:
    today = date_type.today().strftime("%d/%m/%y")
    period = f"{_fmt_date(start_date)} → {today}" if start_date else f"All time → {today}"

    total_income = sum(r["amount"] for r in rows if r["type"] in ("salary", "income"))
    expenses_by_cat: dict[str, float] = defaultdict(float)
    for r in rows:
        if r["type"] == "expense":
            expenses_by_cat[r["category"]] += r["amount"]

    total_expenses = sum(expenses_by_cat.values())
    saved = total_income - total_expenses
    pct = (saved / total_income * 100) if total_income > 0 else 0.0

    lines = [f"*Cycle: {period}*\n"]
    lines.append(f"Income:    {_fmt_amount(total_income)}")
    lines.append(f"Expenses:  {_fmt_amount(total_expenses)}")
    for cat, amt in sorted(expenses_by_cat.items()):
        lines.append(f"  {cat}: {_fmt_amount(amt)}")
    lines.append("")
    lines.append(f"Saved: {_fmt_amount(saved)} ({pct:.0f}%)")
    return "\n".join(lines)


def all_cycles_summary(cycles: list) -> str:
    if not cycles:
        return "No data yet."

    today = date_type.today().strftime("%d/%m/%y")
    lines = ["*All Cycles*\n"]

    total_income_all = 0.0
    total_spent_all = 0.0

    for i, cycle in enumerate(cycles):
        rows = cycle["transactions"]
        start = _fmt_date(cycle["start_date"]) if cycle["start_date"] else "start"
        end = _fmt_date(cycle["end_date"]) if cycle["end_date"] else today

        income = sum(r["amount"] for r in rows if r["type"] in ("salary", "income"))
        spent = sum(r["amount"] for r in rows if r["type"] == "expense")
        saved = income - spent
        pct = (saved / income * 100) if income > 0 else 0.0

        total_income_all += income
        total_spent_all += spent

        label = f"Cycle {i + 1}: {start} → {end}"
        lines.append(f"*{label}*")
        lines.append(f"  Income:  {_fmt_amount(income)}")
        lines.append(f"  Spent:   {_fmt_amount(spent)}")
        lines.append(f"  Saved:   {_fmt_amount(saved)} ({pct:.0f}%)")
        lines.append("")

    total_saved = total_income_all - total_spent_all
    total_pct = (total_saved / total_income_all * 100) if total_income_all > 0 else 0.0
    lines.append("*Overall*")
    lines.append(f"  Income:  {_fmt_amount(total_income_all)}")
    lines.append(f"  Spent:   {_fmt_amount(total_spent_all)}")
    lines.append(f"  Saved:   {_fmt_amount(total_saved)} ({total_pct:.0f}%)")

    return "\n".join(lines)


GUIDE = """\
*Expense Tracker — Guide*

*Add expense*
`33.44` → general category
`hobby:23.78` → specific category

*Add salary* (starts a new cycle)
`salary:3333`

*Add extra income* (stays in current cycle)
`+500`

*Edit a transaction* (use the ID shown after each entry)
`uhueYe 45` → change amount to 45 (expense)
`uhueYe +45` → change to income of 45
`uhueYe delete` → remove it

*Commands*
/expenses — list expenses in current cycle
/month — current salary cycle summary
/all — summary of all cycles + overall total
/guide — show this help
"""
