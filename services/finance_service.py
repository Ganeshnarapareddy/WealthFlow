import pandas as pd
import uuid
from datetime import datetime
from database import db


class FinanceService:
    """Core financial operations — transactions, categories, analytics."""

    @staticmethod
    def get_categories():
        res = db.execute("SELECT id, name, type, icon FROM categories ORDER BY name")
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "name", "type", "icon"])
        return pd.DataFrame(columns=["id", "name", "type", "icon"])

    @staticmethod
    def add_transaction(amount, category_id, description, date_obj, txn_type):
        """
        Insert a transaction. `txn_type` is 'Income' or 'Expense'.
        The `date` column stores 'YYYY-MM-DD HH:MM' for display.
        """
        tid = str(uuid.uuid4())
        date_str = date_obj.strftime("%Y-%m-%d %H:%M")

        db.execute(
            "INSERT INTO transactions (id, user_id, account_id, category_id, amount, type, date, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tid, "default_user", "default_account", category_id,
             amount, txn_type, date_str, description),
        )

        # Update account balance
        adj = amount if txn_type == "Income" else -amount
        db.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (adj, "default_account"),
        )

    @staticmethod
    def get_recent_transactions(limit=50):
        query = """
            SELECT t.date, t.description, t.amount,
                   COALESCE(c.name, 'Other') AS category,
                   COALESCE(c.icon, '❔')    AS icon,
                   COALESCE(t.type, 'Expense') AS type
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            ORDER BY t.date DESC
            LIMIT ?
        """
        res = db.execute(query, (limit,))
        if res and res.rows:
            return pd.DataFrame(
                res.rows,
                columns=["Date", "Description", "Amount", "Category", "Icon", "Type"],
            )
        return pd.DataFrame(
            columns=["Date", "Description", "Amount", "Category", "Icon", "Type"]
        )

    @staticmethod
    def get_net_worth():
        res_acc = db.execute("SELECT SUM(balance) FROM accounts")
        acc = float(res_acc.rows[0][0]) if res_acc and res_acc.rows and res_acc.rows[0][0] else 0.0

        res_ast = db.execute("SELECT SUM(value) FROM assets")
        ast = float(res_ast.rows[0][0]) if res_ast and res_ast.rows and res_ast.rows[0][0] else 0.0

        return acc + ast

    @staticmethod
    def get_spending_by_category():
        query = """
            SELECT COALESCE(c.name, 'Other'), SUM(t.amount)
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.type = 'Expense'
            GROUP BY c.name
        """
        res = db.execute(query)
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["Category", "Amount"])
        return pd.DataFrame(columns=["Category", "Amount"])

    @staticmethod
    def get_monthly_income_vs_expense():
        """Returns total income and total expense for the current month."""
        now = datetime.now()
        pattern = f"{now.year}-{now.month:02d}%"

        res_inc = db.execute(
            "SELECT SUM(amount) FROM transactions WHERE type='Income' AND date LIKE ?",
            (pattern,),
        )
        res_exp = db.execute(
            "SELECT SUM(amount) FROM transactions WHERE type='Expense' AND date LIKE ?",
            (pattern,),
        )
        income = float(res_inc.rows[0][0]) if res_inc and res_inc.rows and res_inc.rows[0][0] else 0.0
        expense = float(res_exp.rows[0][0]) if res_exp and res_exp.rows and res_exp.rows[0][0] else 0.0
        return income, expense
