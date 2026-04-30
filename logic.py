import pandas as pd
from database import db

class FinanceLogic:
    @staticmethod
    def get_total_balance():
        res = db.execute("SELECT SUM(balance) as total FROM accounts")
        row = res.rows[0]
        return row[0] if row[0] else 0.0

    @staticmethod
    def get_net_worth():
        # Simplified as sum of balances for this version
        return FinanceLogic.get_total_balance()

    @staticmethod
    def calculate_safe_to_spend():
        total_balance = FinanceLogic.get_total_balance()

        # Get upcoming subscriptions for the current month
        # In a real app, we'd check the current date
        res_subs = db.execute("SELECT SUM(amount) as total FROM subscriptions")
        sub_total = res_subs.rows[0][0] if res_subs.rows and res_subs.rows[0][0] else 0.0

        # Get budgeted amounts for the current month
        res_budgets = db.execute("SELECT SUM(amount_limit) as total FROM budgets")
        budget_total = res_budgets.rows[0][0] if res_budgets.rows and res_budgets.rows[0][0] else 0.0

        return total_balance - sub_total - budget_total

    @staticmethod
    def get_spending_by_category():
        query = """
            SELECT c.name, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE c.type = 'Expense'
            GROUP BY c.name
        """
        res = db.execute(query)
        if not res.rows:
            return pd.DataFrame(columns=['Category', 'Amount'])
        return pd.DataFrame(res.rows, columns=['Category', 'Amount'])

    @staticmethod
    def get_recent_transactions(limit=10):
        query = """
            SELECT t.date, t.description, t.amount, c.name
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            ORDER BY t.date DESC LIMIT ?
        """
        res = db.execute(query, (limit,))
        return pd.DataFrame(res.rows, columns=['Date', 'Description', 'Amount', 'Category'])

logic = FinanceLogic()
