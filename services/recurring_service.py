import pandas as pd
import uuid
from datetime import datetime, timedelta
import streamlit as st
from database import db


@st.cache_data(ttl=60, show_spinner=False)
def _cached_subscriptions(user_id: str, v: int):
    res = db.execute(
        "SELECT id, name, amount, billing_cycle, start_date, next_billing_date, category, icon "
        "FROM subscriptions WHERE user_id = ? ORDER BY name", (user_id,)
    )
    cols = ["id", "Name", "Amount", "Cycle", "Start Date", "Next Date", "Category", "Icon"]
    if res and res.rows:
        return pd.DataFrame(res.rows, columns=cols)
    return pd.DataFrame(columns=cols)


class RecurringService:
    """Subscription tracking with automatic next-date projection."""

    @staticmethod
    def get_subscriptions(user_id):
        return _cached_subscriptions(user_id, db.version)

    @staticmethod
    def add_subscription(user_id, name, amount, cycle, bill_date, icon="💳", category="Subscriptions"):
        next_date = RecurringService._next_cycle(bill_date, cycle)
        sid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO subscriptions "
            "(id, user_id, name, amount, billing_cycle, start_date, next_billing_date, category, icon) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (sid, user_id, name, amount, cycle, str(bill_date), str(next_date), category, icon),
        )

    @staticmethod
    def delete_subscription(sub_id, user_id):
        db.execute("DELETE FROM subscriptions WHERE id = ? AND user_id = ?", (sub_id, user_id))

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
        elif cycle.startswith("Custom:"):
            try:
                months = int(cycle.split(":")[1])
                return RecurringService._add_months(start, months)
            except (ValueError, IndexError):
                return start
        return start

    @staticmethod
    def _add_months(start_date, months):
        m = (start_date.month + months - 1) % 12 + 1
        y = start_date.year + (start_date.month + months - 1) // 12
        try:
            return start_date.replace(year=y, month=m)
        except ValueError:
            return (start_date.replace(day=1, month=m, year=y) + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    @staticmethod
    def _project_next_date(next_date, cycle, today):
        """Roll a past renewal date forward by its billing cycle until it reaches today or later."""
        guard = 0
        while next_date < today and guard < 240:
            stepped = RecurringService._next_cycle(next_date, cycle)
            if stepped <= next_date:
                break
            next_date = stepped
            guard += 1
        return next_date

    @staticmethod
    def get_upcoming_renewals(user_id, days_ahead=30):
        """Return subscriptions for a user with days left until next billing."""
        res = db.execute(
            "SELECT id, name, amount, billing_cycle, next_billing_date FROM subscriptions WHERE user_id = ?", (user_id,)
        )
        if not res or not res.rows:
            return []
        alerts = []
        today = datetime.now().date()
        for row in res.rows:
            sid, name, amount, cycle, next_date_str = row[0], row[1], row[2], row[3], row[4]
            try:
                next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
                # Roll past renewal dates forward to the next upcoming cycle date
                next_date = RecurringService._project_next_date(next_date, cycle, today)
                days_left = (next_date - today).days
                if 0 <= days_left <= days_ahead:
                    alerts.append({
                        "id": sid, "name": name, "amount": amount,
                        "cycle": cycle, "days_left": days_left, "next_date": next_date
                    })
            except Exception: continue
        return sorted(alerts, key=lambda x: x['days_left'])

    @staticmethod
    def get_monthly_recurring_total(user_id):
        res = db.execute("SELECT amount, billing_cycle FROM subscriptions WHERE user_id = ?", (user_id,))
        if not res or not res.rows: return 0.0
        total = 0.0
        for amt, cycle in res.rows:
            if cycle == "Monthly": total += amt
            elif cycle == "Quarterly": total += amt / 3
            elif cycle == "6 Months": total += amt / 6
            elif cycle == "Yearly": total += amt / 12
            elif cycle.startswith("Custom:"):
                try:
                    months = int(cycle.split(":")[1])
                    total += amt / months
                except: pass
        return total

    @staticmethod
    def get_monthly_recurring_total_for_period(user_id, year, month):
        if month == 12: next_month = f"{year + 1}-01-01"
        else: next_month = f"{year}-{month + 1:02d}-01"

        res = db.execute(
            "SELECT amount, billing_cycle FROM subscriptions WHERE user_id = ? AND start_date < ?",
            (user_id, next_month)
        )
        if not res or not res.rows: return 0.0
        total = 0.0
        for amt, cycle in res.rows:
            if cycle == "Monthly": total += amt
            elif cycle == "Quarterly": total += amt / 3
            elif cycle == "6 Months": total += amt / 6
            elif cycle == "Yearly": total += amt / 12
            elif cycle.startswith("Custom:"):
                try:
                    months = int(cycle.split(":")[1])
                    total += amt / months
                except: pass
        return total

    @staticmethod
    def format_cycle(cycle):
        if cycle == "Monthly": return "Monthly"
        elif cycle == "Quarterly": return "Quarterly"
        elif cycle == "6 Months": return "6 Months"
        elif cycle == "Yearly": return "Yearly"
        elif cycle.startswith("Custom:"):
            try: return f"{cycle.split(':')[1]} Months"
            except: return "Custom"
        return cycle
