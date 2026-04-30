import pandas as pd
import uuid
from datetime import datetime, timedelta
from database import db


class RecurringService:
    """Subscription tracking with automatic next-date projection."""

    @staticmethod
    def get_subscriptions():
        res = db.execute(
            "SELECT id, name, amount, billing_cycle, start_date, next_billing_date, category, icon "
            "FROM subscriptions ORDER BY name"
        )
        if res and res.rows:
            return pd.DataFrame(
                res.rows,
                columns=["id", "Name", "Amount", "Cycle", "Start Date", "Next Date", "Category", "Icon"],
            )
        return pd.DataFrame(
            columns=["id", "Name", "Amount", "Cycle", "Start Date", "Next Date", "Category", "Icon"]
        )

    @staticmethod
    def add_subscription(name, amount, cycle, bill_date, icon="💳", category="Subscriptions"):
        next_date = RecurringService._next_cycle(bill_date, cycle)
        sid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO subscriptions "
            "(id, name, amount, billing_cycle, start_date, next_billing_date, category, icon) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (sid, name, amount, cycle, str(bill_date), str(next_date), category, icon),
        )

    @staticmethod
    def delete_subscription(sub_id):
        db.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))

    @staticmethod
    def _next_cycle(start, cycle):
        if cycle == "Monthly":
            return RecurringService._add_months(start, 1)
        elif cycle == "Quarterly":
            return RecurringService._add_months(start, 3)
        elif cycle == "6 Months":
            return RecurringService._add_months(start, 6)
        elif cycle == "Yearly":
            return start.replace(year=start.year + 1)
        return start

    @staticmethod
    def _add_months(start_date, months):
        m = (start_date.month + months - 1) % 12 + 1
        y = start_date.year + (start_date.month + months - 1) // 12
        try:
            return start_date.replace(year=y, month=m)
        except ValueError:
            # Handle end of month issues
            return (start_date.replace(day=1, month=m, year=y) + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    @staticmethod
    def get_monthly_recurring_total():
        res = db.execute("SELECT amount, billing_cycle FROM subscriptions")
        if not res or not res.rows:
            return 0.0
            
        total = 0.0
        for amt, cycle in res.rows:
            if cycle == "Monthly":
                total += amt
            elif cycle == "Quarterly":
                total += amt / 3
            elif cycle == "6 Months":
                total += amt / 6
            elif cycle == "Yearly":
                total += amt / 12
        return total
