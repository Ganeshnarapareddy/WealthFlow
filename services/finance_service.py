import pandas as pd
import uuid
import calendar
from datetime import datetime, timedelta, date
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
    def is_alert_actioned(alert_id):
        """Check if an alert is actioned for the current month."""
        month_year = datetime.now().strftime("%m-%Y")
        res = db.execute("SELECT id FROM actioned_alerts WHERE alert_id = ? AND month_year = ?", (str(alert_id), month_year))
        return True if res and res.rows else False

    @staticmethod
    def mark_alert_actioned(alert_id):
        """Mark an alert as actioned for the current month."""
        aid = str(uuid.uuid4())
        month_year = datetime.now().strftime("%m-%Y")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute("INSERT OR REPLACE INTO actioned_alerts (id, alert_id, month_year, actioned_at) VALUES (?, ?, ?, ?)",
                   (aid, str(alert_id), month_year, now))

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
            return tid
        except Exception:
            return None

    @staticmethod
    def auto_txn_exists(description):
        """Check if an auto-transaction with this description exists for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        res = db.execute("SELECT id FROM transactions WHERE description = ? AND date LIKE ?", (description, f"{today}%"))
        return True if res and res.rows else False

    @staticmethod
    def delete_transaction(tid):
        """Delete a transaction and reverse its balance impact."""
        res = db.execute("SELECT amount, type, account_id FROM transactions WHERE id = ?", (tid,))
        if res and res.rows:
            amount, txn_type, account_id = res.rows[0]
            # Reverse balance
            adj = -amount if txn_type == "Income" else amount
            db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (adj, account_id))
            db.execute("DELETE FROM transactions WHERE id = ?", (tid,))

    @staticmethod
    def get_filtered_transactions(year=None, month=None, day=None, txn_type=None, limit=100):
        """Retrieve transactions with filters for year, month, day, and type."""
        conditions = []
        params = []
        
        if txn_type and txn_type != "All":
            conditions.append("type = ?")
            params.append(txn_type)
        
        if year and year != "All":
            conditions.append("strftime('%Y', date) = ?")
            params.append(str(year))
            
        if month and month != "All":
            conditions.append("strftime('%m', date) = ?")
            params.append(f"{int(month):02d}")
            
        if day and day != "All":
            conditions.append("strftime('%d', date) = ?")
            params.append(f"{int(day):02d}")
            
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT id, date, description, amount, category, icon, type, source FROM (
                SELECT t.id, t.date, t.description, t.amount,
                       COALESCE(c.name, 'Other') AS category,
                       COALESCE(c.icon, '❔')    AS icon,
                       COALESCE(t.type, 'Expense') AS type,
                       'main' as source
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                UNION ALL
                SELECT ct.id, ct.date, ct.description, ct.amount,
                       'Credit Card' as category, '💳' as icon, 'Expense' as type,
                       'credit_card' as source
                FROM credit_card_transactions ct
                WHERE ct.txn_type = 'expense'
            ) {where_clause}
            ORDER BY date DESC
            LIMIT ?
        """
        params.append(limit)
        res = db.execute(query, tuple(params))
        if res and res.rows:
            return pd.DataFrame(
                res.rows,
                columns=["ID", "Date", "Description", "Amount", "Category", "Icon", "Type", "Source"],
            )
        return pd.DataFrame(
            columns=["ID", "Date", "Description", "Amount", "Category", "Icon", "Type", "Source"]
        )

    @staticmethod
    def get_recent_transactions(limit=50):
        return FinanceService.get_filtered_transactions(limit=limit)

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
        
        # Combined query for Today
        res_today = db.execute(
            """SELECT COALESCE(SUM(amount), 0) FROM (
                SELECT amount FROM transactions WHERE type='Expense' AND date LIKE ?
                UNION ALL
                SELECT amount FROM credit_card_transactions WHERE txn_type='expense' AND date LIKE ?
            )""",
            (f"{today_str}%", f"{today_str}%")
        )
        # Combined query for Yesterday
        res_yest = db.execute(
            """SELECT COALESCE(SUM(amount), 0) FROM (
                SELECT amount FROM transactions WHERE type='Expense' AND date LIKE ?
                UNION ALL
                SELECT amount FROM credit_card_transactions WHERE txn_type='expense' AND date LIKE ?
            )""",
            (f"{yesterday_str}%", f"{yesterday_str}%")
        )
        today = float(res_today.rows[0][0]) if res_today and res_today.rows else 0.0
        yesterday = float(res_yest.rows[0][0]) if res_yest and res_yest.rows else 0.0
        return today, yesterday

    @staticmethod
    def get_income_expense_by_month(year=None, month=None, fiscal_start_day=None):
        """Get income and expense by month, optionally filtered by year/month."""
        if fiscal_start_day is not None:
            start_date, end_date = FinanceService.get_fiscal_period(year, month, int(fiscal_start_day))
            query = """
                SELECT SUBSTR(date, 1, 7) as Month,
                       SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as Income,
                       SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as Expense
                FROM (
                    SELECT date, amount, type FROM transactions
                    UNION ALL
                    SELECT date, amount, 'Expense' as type FROM credit_card_transactions WHERE txn_type='expense'
                )
                WHERE date >= ? AND date < ?
                GROUP BY SUBSTR(date, 1, 7) ORDER BY Month DESC
            """
            res = db.execute(query, (start_date, end_date))
        else:
            query = """
                SELECT SUBSTR(date, 1, 7) as Month,
                       SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as Income,
                       SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as Expense
                FROM (
                    SELECT date, amount, type FROM transactions
                    UNION ALL
                    SELECT date, amount, 'Expense' as type FROM credit_card_transactions WHERE txn_type='expense'
                )
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
    def get_spending_trend(year=None, month=None, months=12, fiscal_start_day=None):
        """Get monthly spending trend, optionally filtered by year/month."""
        if fiscal_start_day is not None:
            start_date, end_date = FinanceService.get_fiscal_period(year, month, int(fiscal_start_day))
            query = """
                SELECT SUBSTR(date, 1, 7) as Month, SUM(amount) as Amount
                FROM (
                    SELECT date, amount FROM transactions WHERE type='Expense'
                    UNION ALL
                    SELECT date, amount FROM credit_card_transactions WHERE txn_type='expense'
                )
                WHERE date >= ? AND date < ?
                GROUP BY SUBSTR(date, 1, 7) ORDER BY Month DESC
                LIMIT ?
            """
            res = db.execute(query, (start_date, end_date, months))
        else:
            query = """
                SELECT SUBSTR(date, 1, 7) as Month, SUM(amount) as Amount
                FROM (
                    SELECT date, amount FROM transactions WHERE type='Expense'
                    UNION ALL
                    SELECT date, amount FROM credit_card_transactions WHERE txn_type='expense'
                )
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
            if year == "All" and month == "All":
                query += " LIMIT ?"
                params.append(months)
            res = db.execute(query, tuple(params))
        if res and res.rows:
            df = pd.DataFrame(res.rows, columns=["Month", "Amount"])
            return df.iloc[::-1]
        return pd.DataFrame(columns=["Month", "Amount"])

    @staticmethod
    def get_spending_by_category(year=None, month=None, fiscal_start_day=None):
        if fiscal_start_day is not None:
            start_date, end_date = FinanceService.get_fiscal_period(year, month, int(fiscal_start_day))
            query = """
                SELECT Category, SUM(Amount) as Amount FROM (
                    SELECT COALESCE(c.name, 'Other') as Category, t.amount as Amount, t.date
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE t.type = 'Expense'
                    UNION ALL
                    SELECT 'Credit Card' as Category, amount as Amount, date
                    FROM credit_card_transactions
                    WHERE txn_type = 'expense'
                )
                WHERE date >= ? AND date < ?
                GROUP BY Category ORDER BY Amount DESC
            """
            res = db.execute(query, (start_date, end_date))
        else:
            query = """
                SELECT Category, SUM(Amount) as Amount FROM (
                    SELECT COALESCE(c.name, 'Other') as Category, t.amount as Amount, t.date
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE t.type = 'Expense'
                    UNION ALL
                    SELECT 'Credit Card' as Category, amount as Amount, date
                    FROM credit_card_transactions
                    WHERE txn_type = 'expense'
                )
                WHERE 1=1
            """
            params = []
            if year and year != "All" and month and month != "All":
                query += " AND date LIKE ?"
                params.append(f"{year}-{month:02d}%")
            elif year and year != "All":
                query += " AND date LIKE ?"
                params.append(f"{year}%")
            query += " GROUP BY Category ORDER BY Amount DESC"
            res = db.execute(query, tuple(params))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["Category", "Amount"])
        return pd.DataFrame(columns=["Category", "Amount"])

    @staticmethod
    def get_available_years():
        query = """
            SELECT DISTINCT SUBSTR(date, 1, 4) as yr FROM (
                SELECT date FROM transactions
                UNION ALL
                SELECT date FROM credit_card_transactions
            ) ORDER BY yr DESC
        """
        res = db.execute(query)
        if res and res.rows:
            return [int(r[0]) for r in res.rows if r[0]]
        return [datetime.now().year]

    @staticmethod
    def get_available_months(year=None):
        """Get available months for a given year. Returns list of (year, month) tuples."""
        if year and year != "All":
            query = """
                SELECT DISTINCT SUBSTR(date, 1, 7) as ym
                FROM (
                    SELECT date FROM transactions
                    UNION ALL
                    SELECT date FROM credit_card_transactions
                )
                WHERE SUBSTR(date, 1, 4) = ?
                ORDER BY ym DESC
            """
            res = db.execute(query, (str(year),))
        else:
            query = """
                SELECT DISTINCT SUBSTR(date, 1, 7) as ym
                FROM (
                    SELECT date FROM transactions
                    UNION ALL
                    SELECT date FROM credit_card_transactions
                )
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
    def get_period_data(year, month, fiscal_start_day=None):
        """
        Get income and expense for a specific period.
        Returns: (income, expense)
        If fiscal_start_day is set, uses date-range queries for fiscal period.
        """
        if fiscal_start_day is not None:
            start_date, end_date = FinanceService.get_fiscal_period(year, month, int(fiscal_start_day))
            query_inc = "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Income' AND date >= ? AND date < ?"
            query_exp = "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Expense' AND date >= ? AND date < ?"
            res_inc = db.execute(query_inc, (start_date, end_date))
            res_exp = db.execute(query_exp, (start_date, end_date))
        else:
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
    def get_previous_period_data(year, month, fiscal_start_day=None):
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
            if fiscal_start_day is not None:
                # Previous fiscal year: same month 12 of previous year
                prev_year = year - 1
                prev_month = 12
                data = FinanceService.get_period_data(prev_year, prev_month, fiscal_start_day)
                return (data[0], data[1], f"{prev_year}-{prev_month:02d}")
            else:
                prev_year = year - 1
                data = FinanceService.get_period_data(prev_year, "All")
                return (data[0], data[1], f"{prev_year}")

        elif year != "All" and month != "All":
            if fiscal_start_day is not None:
                # Previous fiscal period: subtract 1 month
                prev_month = month - 1
                prev_year = year
                if prev_month == 0:
                    prev_month = 12
                    prev_year = year - 1
                data = FinanceService.get_period_data(prev_year, prev_month, fiscal_start_day)
                label = FinanceService.get_fiscal_month_label(prev_year, prev_month, int(fiscal_start_day))
                return (data[0], data[1], label)
            else:
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
    def get_savings_rate(fiscal_start_day=None):
        """Calculate savings rate for current period: (Income - Expense) / Income * 100."""
        inc, exp = FinanceService.get_monthly_income_vs_expense(fiscal_start_day=fiscal_start_day)
        if inc > 0:
            return ((inc - exp) / inc) * 100
        return 0.0

    @staticmethod
    def get_top_spending_category(year=None, month=None, fiscal_start_day=None):
        """Get the top spending category for a given period."""
        df = FinanceService.get_spending_by_category(year, month, fiscal_start_day)
        if not df.empty:
            top = df.iloc[0]
            return top['Category'], top['Amount']
        return None, 0.0

    @staticmethod
    def get_top_category_comparison(year, month, fiscal_start_day=None):
        """
        Get top category comparison with previous period.
        Returns: (cat, amt, prev_amt, delta_str, is_increase)
        """
        # Handle None values
        if year is None:
            year = "All"
        if month is None:
            month = "All"

        cat, amt = FinanceService.get_top_spending_category(year, month, fiscal_start_day)

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
            prev_cat, prev_amt = FinanceService.get_top_spending_category(prev_year, "All", fiscal_start_day)
            delta_str, is_increase = FinanceService.get_comparison_delta(amt, prev_amt)
            return cat, amt, prev_amt, delta_str, is_increase

        elif year != "All" and month != "All":
            prev_month = month - 1
            prev_year = year
            if prev_month == 0:
                prev_month = 12
                prev_year = year - 1
            prev_cat, prev_amt = FinanceService.get_top_spending_category(prev_year, prev_month, fiscal_start_day)
            delta_str, is_increase = FinanceService.get_comparison_delta(amt, prev_amt)
            return cat, amt, prev_amt, delta_str, is_increase

        return cat, amt, 0.0, None, False

    @staticmethod
    def get_setting(key, default=None):
        """Read a key from settings table, return default if not found."""
        res = db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        if res and res.rows and res.rows[0][0]:
            return res.rows[0][0]
        return default

    @staticmethod
    def set_setting(key, value):
        """Upsert a key-value pair in settings table."""
        db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))

    @staticmethod
    def _add_months_to_date(year, month, day, months):
        """Add months to a (year, month, day) tuple, return (new_year, new_month, clamped_day)."""
        m = (month + months - 1) % 12 + 1
        y = year + (month + months - 1) // 12
        max_day = calendar.monthrange(y, m)[1]
        adjusted_day = min(day, max_day)
        return y, m, adjusted_day

    @staticmethod
    def get_fiscal_period(year, month, start_day):
        """
        Get fiscal period start/end dates.
        Returns: (start_date_str, end_date_str) e.g., ('2026-04-28', '2026-05-28')
        """
        start_date = f"{year}-{month:02d}-{start_day:02d}"
        y, m, d = FinanceService._add_months_to_date(year, month, start_day, 1)
        end_date = f"{y}-{m:02d}-{d:02d}"
        return start_date, end_date

    @staticmethod
    def get_fiscal_month_label(year, month, start_day):
        """Return display label like 'Apr 28 - May 27' for fiscal period."""
        start_day_actual = min(start_day, calendar.monthrange(year, month)[1])
        y1, m1, d1 = year, month, start_day_actual
        y2, m2, d2 = FinanceService._add_months_to_date(year, month, start_day_actual, 1)
        end_minus_one = date(y2, m2, d2) - timedelta(days=1)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return f"{months[m1-1]} {d1} - {months[m2-1]} {end_minus_one.day}"

    @staticmethod
    def get_monthly_income_vs_expense(year=None, month=None, fiscal_start_day=None):
        """
        Returns total income and total expense for the given year/month.
        If fiscal_start_day is set, uses fiscal period date range.
        """
        if fiscal_start_day is not None:
            fiscal_start_day = int(fiscal_start_day)
            start_date, end_date = FinanceService.get_fiscal_period(year, month, fiscal_start_day)
            res_inc = db.execute(
                "SELECT SUM(amount) FROM transactions WHERE type='Income' AND date >= ? AND date < ?",
                (start_date, end_date),
            )
            res_exp = db.execute(
                "SELECT SUM(amount) FROM transactions WHERE type='Expense' AND date >= ? AND date < ?",
                (start_date, end_date),
            )
        elif year and month and year != "All" and month != "All":
            pattern = f"{year}-{month:02d}%"
            res_inc = db.execute(
                "SELECT SUM(amount) FROM transactions WHERE type='Income' AND date LIKE ?",
                (pattern,),
            )
            res_exp = db.execute(
                "SELECT SUM(amount) FROM transactions WHERE type='Expense' AND date LIKE ?",
                (pattern,),
            )
        elif year and year != "All":
            pattern = f"{year}%"
            res_inc = db.execute(
                "SELECT SUM(amount) FROM transactions WHERE type='Income' AND date LIKE ?",
                (pattern,),
            )
            res_exp = db.execute(
                "SELECT SUM(amount) FROM transactions WHERE type='Expense' AND date LIKE ?",
                (pattern,),
            )
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
