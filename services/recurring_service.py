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
            # Handle end of month issues
            return (start_date.replace(day=1, month=m, year=y) + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    @staticmethod
    def get_upcoming_renewals(days_ahead=30):
        """Return subscriptions with days left until next billing."""
        res = db.execute(
            "SELECT id, name, amount, billing_cycle, next_billing_date FROM subscriptions"
        )
        if not res or not res.rows:
            return []
        alerts = []
        today = datetime.now().date()
        for row in res.rows:
            sid, name, amount, cycle, next_date_str = row[0], row[1], row[2], row[3], row[4]
            try:
                next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
                days_left = (next_date - today).days
                if 0 <= days_left <= days_ahead:
                    alerts.append({
                        "id": sid, "name": name, "amount": amount,
                        "cycle": cycle, "days_left": days_left, "next_date": next_date
                    })
            except Exception:
                continue
        return sorted(alerts, key=lambda x: x['days_left'])

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
            elif cycle.startswith("Custom:"):
                try:
                    months = int(cycle.split(":")[1])
                    total += amt / months
                except (ValueError, IndexError):
                    pass
        return total

    @staticmethod
    def get_monthly_recurring_total_for_period(year, month):
        """Get monthly recurring total for a specific period (based on subscriptions active at that time)."""
        # Get the end date of the period
        if month == 12:
            next_month = f"{year + 1}-01-01"
        else:
            next_month = f"{year}-{month + 1:02d}-01"

        res = db.execute(
            "SELECT amount, billing_cycle FROM subscriptions WHERE start_date < ?",
            (next_month,)
        )
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
            elif cycle.startswith("Custom:"):
                try:
                    months = int(cycle.split(":")[1])
                    total += amt / months
                except (ValueError, IndexError):
                    pass
        return total

    @staticmethod
    def format_cycle(cycle):
        """Format billing cycle for display."""
        if cycle == "Monthly":
            return "Monthly"
        elif cycle == "Quarterly":
            return "Quarterly"
        elif cycle == "6 Months":
            return "6 Months"
        elif cycle == "Yearly":
            return "Yearly"
        elif cycle.startswith("Custom:"):
            try:
                months = cycle.split(":")[1]
                return f"{months} Months"
            except IndexError:
                return "Custom"
        return cycle
