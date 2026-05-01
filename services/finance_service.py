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

        try:
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
        except Exception as e:
            print(f"Error adding transaction: {e}")
            raise

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
    def get_today_vs_yesterday():
        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        res_today = db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Expense' AND date LIKE ?",
            (f"{today_str}%",)
        )
        res_yest = db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Expense' AND date LIKE ?",
            (f"{yesterday_str}%",)
        )
        today = float(res_today.rows[0][0]) if res_today and res_today.rows else 0.0
        yesterday = float(res_yest.rows[0][0]) if res_yest and res_yest.rows else 0.0
        return today, yesterday

    @staticmethod
    def get_income_expense_by_month(year=None, month=None):
        """Get income and expense by month, optionally filtered by year/month."""
        query = """
            SELECT SUBSTR(date, 1, 7) as Month,
                   SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as Income,
                   SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as Expense
            FROM transactions
            WHERE 1=1
        """
        params = []
        if year and year != "All" and month and month != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}-{month:02d}%")
        elif year and year != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}%")

        query += " GROUP BY SUBSTR(date, 1, 7) ORDER BY Month DESC"

        res = db.execute(query, tuple(params))
        if res and res.rows:
            df = pd.DataFrame(res.rows, columns=["Month", "Income", "Expense"])
            return df.iloc[::-1]
        return pd.DataFrame(columns=["Month", "Income", "Expense"])

    @staticmethod
    def get_spending_trend(year=None, month=None, months=12):
        """Get monthly spending trend, optionally filtered by year/month."""
        query = """
            SELECT SUBSTR(date, 1, 7) as Month, SUM(amount) as Amount
            FROM transactions
            WHERE type='Expense'
        """
        params = []
        if year and year != "All" and month and month != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}-{month:02d}%")
        elif year and year != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}%")

        query += " GROUP BY SUBSTR(date, 1, 7) ORDER BY Month DESC"

        if year == "All" and month == "All":
            query += " LIMIT ?"
            params.append(months)

        res = db.execute(query, tuple(params))
        if res and res.rows:
            df = pd.DataFrame(res.rows, columns=["Month", "Amount"])
            return df.iloc[::-1]
        return pd.DataFrame(columns=["Month", "Amount"])

    @staticmethod
    def get_spending_by_category(year=None, month=None):
        query = """
            SELECT COALESCE(c.name, 'Other') as Category, SUM(t.amount) as Amount
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.type = 'Expense'
        """
        params = []
        if year and year != "All" and month and month != "All":
            query += " AND t.date LIKE ?"
            params.append(f"{year}-{month:02d}%")
        elif year and year != "All":
            query += " AND t.date LIKE ?"
            params.append(f"{year}%")

        query += " GROUP BY c.name ORDER BY Amount DESC"
        res = db.execute(query, tuple(params))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["Category", "Amount"])
        return pd.DataFrame(columns=["Category", "Amount"])

    @staticmethod
    def get_available_years():
        res = db.execute("SELECT DISTINCT SUBSTR(date, 1, 4) as yr FROM transactions ORDER BY yr DESC")
        if res and res.rows:
            return [int(r[0]) for r in res.rows if r[0]]
        return [datetime.now().year]

    @staticmethod
    def get_available_months(year=None):
        """Get available months for a given year. Returns list of (year, month) tuples."""
        if year and year != "All":
            query = """
                SELECT DISTINCT SUBSTR(date, 1, 7) as ym
                FROM transactions
                WHERE SUBSTR(date, 1, 4) = ?
                ORDER BY ym DESC
            """
            res = db.execute(query, (str(year),))
        else:
            query = """
                SELECT DISTINCT SUBSTR(date, 1, 7) as ym
                FROM transactions
                ORDER BY ym DESC
            """
            res = db.execute(query)

        if res and res.rows:
            months = []
            for r in res.rows:
                if r[0]:
                    y, m = r[0].split('-')
                    months.append((int(y), int(m)))
            return months
        return [(datetime.now().year, datetime.now().month)]

    @staticmethod
    def get_period_data(year, month):
        """
        Get income and expense for a specific period.
        Returns: (income, expense)
        """
        params = []
        where = "WHERE 1=1"

        if year != "All" and month != "All":
            where += " AND date LIKE ?"
            params.append(f"{year}-{month:02d}%")
        elif year != "All" and month == "All":
            where += " AND date LIKE ?"
            params.append(f"{year}%")

        query_inc = "SELECT COALESCE(SUM(amount), 0) FROM transactions " + where + " AND type='Income'"
        query_exp = "SELECT COALESCE(SUM(amount), 0) FROM transactions " + where + " AND type='Expense'"

        res_inc = db.execute(query_inc, tuple(params))
        res_exp = db.execute(query_exp, tuple(params))

        income = float(res_inc.rows[0][0]) if res_inc and res_inc.rows and res_inc.rows[0][0] else 0.0
        expense = float(res_exp.rows[0][0]) if res_exp and res_exp.rows and res_exp.rows[0][0] else 0.0
        return income, expense

    @staticmethod
    def get_previous_period_data(year, month):
        """
        Get the previous period's data for comparison.
        Returns: (prev_income, prev_expense, prev_label)
        """
        # Handle None values
        if year is None:
            year = "All"
        if month is None:
            month = "All"

        if year == "All" and month == "All":
            query = """
                SELECT SUBSTR(date, 1, 7) as ym,
                       SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as income,
                       SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as expense
                FROM transactions
                GROUP BY ym
                ORDER BY ym DESC
                LIMIT 2
            """
            res = db.execute(query)
            if res and res.rows and len(res.rows) >= 2:
                prev = res.rows[1]
                return float(prev[1]), float(prev[2]), prev[0]
            return 0.0, 0.0, "N/A"

        elif year != "All" and month == "All":
            prev_year = year - 1
            data = FinanceService.get_period_data(prev_year, "All")
            return (data[0], data[1], f"{prev_year}")

        elif year != "All" and month != "All":
            prev_month = month - 1
            prev_year = year
            if prev_month == 0:
                prev_month = 12
                prev_year = year - 1
            data = FinanceService.get_period_data(prev_year, prev_month)
            return (data[0], data[1], f"{prev_year}-{prev_month:02d}")

        return 0.0, 0.0, "N/A"

    @staticmethod
    def get_comparison_delta(current_val, prev_val):
        """
        Calculate delta percentage and formatted string.
        Returns: (delta_str, is_increase)
        """
        if prev_val == 0:
            if current_val > 0:
                return "+100% (new)", True
            return None, False

        pct = ((current_val - prev_val) / prev_val) * 100
        diff = current_val - prev_val

        if abs(pct) < 0.01:
            return None, False

        sign = "+" if pct > 0 else ""
        return f"{sign}{pct:.1f}% ({sign}{diff:,.0f})", pct > 0

    @staticmethod
    def get_savings_rate():
        """Calculate savings rate for current month: (Income - Expense) / Income * 100."""
        inc, exp = FinanceService.get_monthly_income_vs_expense()
        if inc > 0:
            return ((inc - exp) / inc) * 100
        return 0.0

    @staticmethod
    def get_top_spending_category(year=None, month=None):
        """Get the top spending category for a given period."""
        df = FinanceService.get_spending_by_category(year, month)
        if not df.empty:
            top = df.iloc[0]
            return top['Category'], top['Amount']
        return None, 0.0

    @staticmethod
    def get_top_category_comparison(year, month):
        """
        Get top category comparison with previous period.
        Returns: (cat, amt, prev_amt, delta_str, is_increase)
        """
        # Handle None values
        if year is None:
            year = "All"
        if month is None:
            month = "All"

        cat, amt = FinanceService.get_top_spending_category(year, month)

        if year == "All" and month == "All":
            query = """
                SELECT SUBSTR(date, 1, 7) as ym,
                       COALESCE(c.name, 'Other') as name,
                       SUM(t.amount) as total
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.type = 'Expense'
                GROUP BY ym, c.name
                ORDER BY ym DESC
            """
            res = db.execute(query)
            if res and res.rows:
                df = pd.DataFrame(res.rows, columns=["ym", "name", "total"])
                months = df['ym'].unique()
                if len(months) >= 2:
                    prev_month = months[1]
                    prev_df = df[df['ym'] == prev_month]
                    if not prev_df.empty:
                        prev_top = prev_df.iloc[prev_df['total'].argmax()]
                        prev_amt = prev_top['total']
                        delta_str, is_increase = FinanceService.get_comparison_delta(amt, prev_amt)
                        return cat, amt, prev_amt, delta_str, is_increase
            return cat, amt, 0.0, None, False

        elif year != "All" and month == "All":
            prev_year = year - 1
            prev_cat, prev_amt = FinanceService.get_top_spending_category(prev_year, "All")
            delta_str, is_increase = FinanceService.get_comparison_delta(amt, prev_amt)
            return cat, amt, prev_amt, delta_str, is_increase

        elif year != "All" and month != "All":
            prev_month = month - 1
            prev_year = year
            if prev_month == 0:
                prev_month = 12
                prev_year = year - 1
            prev_cat, prev_amt = FinanceService.get_top_spending_category(prev_year, prev_month)
            delta_str, is_increase = FinanceService.get_comparison_delta(amt, prev_amt)
            return cat, amt, prev_amt, delta_str, is_increase

        return cat, amt, 0.0, None, False

    @staticmethod
    def get_monthly_income_vs_expense(year=None, month=None):
        """Returns total income and total expense for the given year/month."""
        if year and month and year != "All" and month != "All":
            pattern = f"{year}-{month:02d}%"
        elif year and year != "All":
            pattern = f"{year}%"
        else:
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
