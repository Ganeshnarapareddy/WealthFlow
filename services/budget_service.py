import pandas as pd
import uuid
from database import db


class BudgetService:
    """Monthly budget limits with smart-alert progress tracking."""

    @staticmethod
    def get_monthly_budgets(month=None, year=None):
        from datetime import datetime
        now = datetime.now()
        month = month or now.month
        year = year or now.year
        pattern = f"{year}-{month:02d}%"

        query = """
            SELECT b.id, c.name, c.icon, b.amount_limit,
                   COALESCE(
                       (SELECT SUM(t.amount) FROM transactions t
                        WHERE t.category_id = c.id AND t.type='Expense' AND t.date LIKE ?), 0
                   ) AS spent
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.month = ? AND b.year = ?
        """
        res = db.execute(query, (pattern, month, year))
        if res and res.rows:
            rows = []
            for r in res.rows:
                bid, name, icon, limit_val, spent = r
                spent = spent or 0.0
                rows.append({
                    "id": bid, "Category": f"{icon} {name}",
                    "Limit": limit_val, "Spent": spent,
                    "Remaining": max(0, limit_val - spent),
                    "Progress": min(1.0, spent / limit_val) if limit_val > 0 else 0,
                })
            return pd.DataFrame(rows)
        return pd.DataFrame(columns=["id", "Category", "Limit", "Spent", "Remaining", "Progress"])

    @staticmethod
    def add_budget(category_id, amount_limit, month, year):
        bid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO budgets (id, category_id, amount_limit, month, year) VALUES (?, ?, ?, ?, ?)",
            (bid, category_id, amount_limit, month, year),
        )

    @staticmethod
    def delete_budget(budget_id):
        db.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
