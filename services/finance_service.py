import pandas as pd
import uuid
import calendar
from datetime import datetime, timedelta, date
from database import db


class FinanceService:
    # v1.1 - Added daily spending analytics
    """Core financial operations — transactions, categories, analytics."""

    @staticmethod
    def get_categories(user_id=None):
        if user_id:
            res = db.execute("SELECT id, name, type, icon FROM categories WHERE user_id IS NULL OR user_id = ? ORDER BY name", (user_id,))
        else:
            res = db.execute("SELECT id, name, type, icon FROM categories WHERE user_id IS NULL ORDER BY name")
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "name", "type", "icon"])
        return pd.DataFrame(columns=["id", "name", "type", "icon"])

    @staticmethod
    def is_alert_actioned(alert_id, user_id):
        """Check if an alert is actioned for the current month."""
        month_year = datetime.now().strftime("%m-%Y")
        res = db.execute("SELECT id FROM actioned_alerts WHERE user_id = ? AND alert_id = ? AND month_year = ?", (user_id, str(alert_id), month_year))
        return True if res and res.rows else False

    @staticmethod
    def mark_alert_actioned(alert_id, user_id):
        """Mark an alert as actioned for the current month."""
        aid = str(uuid.uuid4())
        month_year = datetime.now().strftime("%m-%Y")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute("INSERT OR REPLACE INTO actioned_alerts (id, user_id, alert_id, month_year, actioned_at) VALUES (?, ?, ?, ?, ?)",
                   (aid, user_id, str(alert_id), month_year, now))

    @staticmethod
    def add_transaction(amount, category_id, description, date_obj, txn_type, user_id, account_id=None):
        tid = str(uuid.uuid4())
        date_str = date_obj.strftime("%Y-%m-%d %H:%M")
        if not account_id:
            res = db.execute("SELECT id FROM accounts WHERE user_id = ? LIMIT 1", (user_id,))
            account_id = res.rows[0][0] if res and res.rows else "default_account_admin"
        try:
            db.execute(
                "INSERT INTO transactions (id, user_id, account_id, category_id, amount, type, date, description) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (tid, user_id, account_id, category_id, amount, txn_type, date_str, description),
            )
            adj = amount if txn_type == "Income" else -amount
            db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (adj, account_id))
            return tid
        except: return None

    @staticmethod
    def auto_txn_exists(description, user_id):
        today = datetime.now().strftime("%Y-%m-%d")
        res = db.execute("SELECT id FROM transactions WHERE user_id = ? AND description = ? AND date LIKE ?", (user_id, description, f"{today}%"))
        return True if res and res.rows else False

    @staticmethod
    def delete_transaction(tid, user_id):
        res = db.execute("SELECT amount, type, account_id FROM transactions WHERE id = ? AND user_id = ?", (tid, user_id))
        if res and res.rows:
            amount, txn_type, account_id = res.rows[0]
            adj = -amount if txn_type == "Income" else amount
            db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (adj, account_id))
            db.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tid, user_id))

    @staticmethod
    def get_filtered_transactions(user_id, year=None, month=None, day=None, txn_type=None, description_search=None, category_name=None, limit=100):
        conditions = ["user_id = ?"]
        params = [user_id]
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
        if description_search:
            conditions.append("LOWER(description) LIKE ?")
            params.append(f"%{description_search.lower()}%")
        if category_name and category_name != "All":
            conditions.append("category = ?")
            params.append(category_name)
        
        where_clause = " WHERE " + " AND ".join(conditions)
        query = f"""
            SELECT id, date, description, amount, category, icon, type, source FROM (
                SELECT t.id, t.date, t.description, t.amount,
                       COALESCE(c.name, 'Other') AS category,
                       COALESCE(c.icon, '❔') AS icon,
                       COALESCE(t.type, 'Expense') AS type,
                       'main' as source, t.user_id
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                UNION ALL
                SELECT ct.id, ct.date, ct.description, ct.amount,
                       'Credit Card' as category, '💳' as icon, 'Expense' as type,
                       'credit_card' as source, ct.user_id
                FROM credit_card_transactions ct
                WHERE ct.txn_type = 'expense'
            ) {where_clause}
            ORDER BY date DESC LIMIT ?
        """
        params.append(limit)
        res = db.execute(query, tuple(params))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["ID", "Date", "Description", "Amount", "Category", "Icon", "Type", "Source"])
        return pd.DataFrame(columns=["ID", "Date", "Description", "Amount", "Category", "Icon", "Type", "Source"])

    @staticmethod
    def get_recent_transactions(user_id, limit=50):
        return FinanceService.get_filtered_transactions(user_id, limit=limit)

    @staticmethod
    def get_net_worth(user_id):
        res_acc = db.execute("SELECT SUM(balance) FROM accounts WHERE user_id = ?", (user_id,))
        acc = float(res_acc.rows[0][0]) if res_acc and res_acc.rows and res_acc.rows[0][0] else 0.0
        res_ast = db.execute("SELECT SUM(value) FROM assets WHERE user_id = ?", (user_id,))
        ast = float(res_ast.rows[0][0]) if res_ast and res_ast.rows and res_ast.rows[0][0] else 0.0
        return acc + ast

    @staticmethod
    def get_today_vs_yesterday(user_id):
        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        res_today = db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM (SELECT amount FROM transactions WHERE user_id=? AND UPPER(type)='EXPENSE' AND date LIKE ? UNION ALL SELECT amount FROM credit_card_transactions WHERE user_id=? AND UPPER(txn_type)='EXPENSE' AND date LIKE ?)",
            (user_id, f"{today_str}%", user_id, f"{today_str}%")
        )
        res_yest = db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM (SELECT amount FROM transactions WHERE user_id=? AND UPPER(type)='EXPENSE' AND date LIKE ? UNION ALL SELECT amount FROM credit_card_transactions WHERE user_id=? AND UPPER(txn_type)='EXPENSE' AND date LIKE ?)",
            (user_id, f"{yesterday_str}%", user_id, f"{yesterday_str}%")
        )
        today_val = float(res_today.rows[0][0]) if res_today and res_today.rows and res_today.rows[0][0] else 0.0
        yest_val = float(res_yest.rows[0][0]) if res_yest and res_yest.rows and res_yest.rows[0][0] else 0.0
        return today_val, yest_val

    @staticmethod
    def get_income_expense_by_month(user_id, year=None, month=None):
        query = """
            SELECT SUBSTR(date, 1, 7) as Month,
                   SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as Income,
                   SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as Expense
            FROM (
                SELECT date, amount, type, user_id FROM transactions
                UNION ALL
                SELECT date, amount, 'Expense' as type, user_id FROM credit_card_transactions WHERE txn_type='expense'
            )
            WHERE user_id = ?
        """
        params = [user_id]
        if year and year != "All" and month and month != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}-{month:02d}%")
        elif year and year != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}%")
        query += " GROUP BY Month ORDER BY Month DESC"
        res = db.execute(query, tuple(params))
        if res and res.rows:
            df = pd.DataFrame(res.rows, columns=["Month", "Income", "Expense"])
            return df.iloc[::-1]
        return pd.DataFrame(columns=["Month", "Income", "Expense"])

    @staticmethod
    def get_spending_trend(user_id, year=None, month=None, months=12):
        query = """
            SELECT SUBSTR(date, 1, 7) as Month, SUM(amount) as Amount
            FROM (
                SELECT date, amount, user_id FROM transactions WHERE type='Expense'
                UNION ALL
                SELECT date, amount, user_id FROM credit_card_transactions WHERE txn_type='expense'
            )
            WHERE user_id = ?
        """
        params = [user_id]
        if year and year != "All" and month and month != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}-{month:02d}%")
        elif year and year != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}%")
        query += " GROUP BY Month ORDER BY Month DESC LIMIT ?"
        params.append(months)
        res = db.execute(query, tuple(params))
        if res and res.rows:
            df = pd.DataFrame(res.rows, columns=['Month', 'Amount'])
            return df.sort_values('Month')
        return pd.DataFrame(columns=['Month', 'Amount'])

    @staticmethod
    def get_spending_by_category(user_id, year=None, month=None):
        query = """
            SELECT Category, SUM(Amount) as Amount FROM (
                SELECT (SELECT name FROM categories WHERE id = t.category_id) as Category, amount as Amount, date, user_id, type
                FROM transactions t
                UNION ALL
                SELECT 'Credit Card' as Category, amount as Amount, date, user_id, txn_type as type
                FROM credit_card_transactions
            )
            WHERE user_id = ? AND UPPER(type) = 'EXPENSE'
        """
        params = [user_id]
        if year and year != "All" and month and month != "All":
            query += " AND SUBSTR(date, 1, 10) >= ? AND SUBSTR(date, 1, 10) <= ?"
            start_day = int(FinanceService.get_setting('fiscal_month_start_day', '1', user_id))
            start_date = date(int(year), month, start_day).strftime("%Y-%m-%d")
            if month == 12:
                end_date = (date(int(year) + 1, 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                end_date = (date(int(year), month + 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
            params.extend([start_date, end_date])
        elif year and year != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}%")
            
        query += " GROUP BY Category ORDER BY Amount DESC"
        res = db.execute(query, tuple(params))
        
        # Clean up category names
        rows = []
        if res and res.rows:
            for r in res.rows:
                cat_name = r[0] if r[0] else "Other"
                rows.append([cat_name, r[1]])
                
        if rows:
            return pd.DataFrame(rows, columns=["Category", "Amount"])
        return pd.DataFrame(columns=["Category", "Amount"])

    @staticmethod
    def get_daily_spending_by_category(user_id, year=None, month=None):
        query = """
            SELECT Date, Category, SUM(Amount) as Amount FROM (
                SELECT SUBSTR(date, 1, 10) as Date, 
                       (SELECT name FROM categories WHERE id = t.category_id) as Category, 
                       amount as Amount, user_id, type
                FROM transactions t
                UNION ALL
                SELECT SUBSTR(date, 1, 10) as Date, 
                       'Credit Card' as Category, 
                       amount as Amount, user_id, txn_type as type
                FROM credit_card_transactions
            )
            WHERE user_id = ? AND UPPER(type) = 'EXPENSE'
        """
        params = [user_id]
        if year and year != "All" and month and month != "All":
            query += " AND SUBSTR(Date, 1, 10) >= ? AND SUBSTR(Date, 1, 10) <= ?"
            start_day = int(FinanceService.get_setting('fiscal_month_start_day', '1', user_id))
            start_date = date(int(year), month, start_day).strftime("%Y-%m-%d")
            if month == 12:
                end_date = (date(int(year) + 1, 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                end_date = (date(int(year), month + 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
            params.extend([start_date, end_date])
        elif year and year != "All":
            query += " AND Date LIKE ?"
            params.append(f"{year}%")
            
        query += " GROUP BY Date, Category ORDER BY Date ASC"
        res = db.execute(query, tuple(params))
        
        rows = []
        if res and res.rows:
            for r in res.rows:
                cat_name = r[1] if r[1] else "Other"
                rows.append([r[0], cat_name, r[2]])
                
        if rows:
            return pd.DataFrame(rows, columns=["Date", "Category", "Amount"])
        return pd.DataFrame(columns=["Date", "Category", "Amount"])

    @staticmethod
    def get_available_years(user_id):
        res = db.execute("SELECT DISTINCT SUBSTR(date, 1, 4) as yr FROM (SELECT date, user_id FROM transactions UNION ALL SELECT date, user_id FROM credit_card_transactions) WHERE user_id = ? ORDER BY yr DESC", (user_id,))
        if res and res.rows: return [int(r[0]) for r in res.rows if r[0]]
        return [datetime.now().year]

    @staticmethod
    def get_available_months(user_id, year=None):
        query = "SELECT DISTINCT SUBSTR(date, 1, 7) as ym FROM (SELECT date, user_id FROM transactions UNION ALL SELECT date, user_id FROM credit_card_transactions) WHERE user_id = ?"
        params = [user_id]
        if year and year != "All":
            query += " AND SUBSTR(date, 1, 4) = ?"
            params.append(str(year))
        query += " ORDER BY ym DESC"
        res = db.execute(query, tuple(params))
        if res and res.rows:
            months = []
            for r in res.rows:
                if r[0]:
                    parts = r[0].split('-')
                    if len(parts) == 2: months.append((int(parts[0]), int(parts[1])))
            return months
        return [(datetime.now().year, datetime.now().month)]

    @staticmethod
    def get_period_data(user_id, year, month):
        params = [user_id]
        where = "WHERE user_id = ?"
        if year != "All" and month != "All":
            where += " AND date LIKE ?"
            params.append(f"{year}-{month:02d}%")
        elif year != "All":
            where += " AND date LIKE ?"
            params.append(f"{year}%")
        
        query_inc = "SELECT COALESCE(SUM(amount), 0) FROM transactions " + where + " AND UPPER(type)='INCOME'"
        query_exp = "SELECT COALESCE(SUM(amount), 0) FROM (SELECT amount, user_id, date, type FROM transactions UNION ALL SELECT amount, user_id, date, 'Expense' as type FROM credit_card_transactions WHERE UPPER(txn_type)='EXPENSE') " + where + " AND UPPER(type)='EXPENSE'"
        res_inc = db.execute(query_inc, tuple(params))
        res_exp = db.execute(query_exp, tuple(params))
        
        inc = float(res_inc.rows[0][0]) if res_inc and res_inc.rows and res_inc.rows[0][0] else 0.0
        exp = float(res_exp.rows[0][0]) if res_exp and res_exp.rows and res_exp.rows[0][0] else 0.0
        return inc, exp

    @staticmethod
    def get_previous_period_data(user_id, year, month):
        if year == "All" or month == "All":
            query = "SELECT SUBSTR(date, 1, 7) as ym, SUM(CASE WHEN type='Income' THEN amount ELSE 0 END), SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) FROM (SELECT date, amount, type, user_id FROM transactions UNION ALL SELECT date, amount, 'Expense' as type, user_id FROM credit_card_transactions WHERE txn_type='expense') WHERE user_id = ? GROUP BY ym ORDER BY ym DESC LIMIT 2"
            res = db.execute(query, (user_id,))
            if res and res.rows and len(res.rows) >= 2:
                prev = res.rows[1]
                return float(prev[1]), float(prev[2]), prev[0]
            return 0.0, 0.0, "Previous"
        
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year = year - 1
        inc, exp = FinanceService.get_period_data(user_id, prev_year, prev_month)
        return inc, exp, f"{prev_year}-{prev_month:02d}"

    @staticmethod
    def get_comparison_delta(current_val, prev_val):
        if prev_val == 0: return ("+100% (new)", True) if current_val > 0 else (None, False)
        pct = ((current_val - prev_val) / prev_val) * 100
        diff = current_val - prev_val
        if abs(pct) < 0.01: return None, False
        sign = "+" if pct > 0 else ""
        return f"{sign}{pct:.1f}% ({sign}{diff:,.0f})", pct > 0

    @staticmethod
    def get_savings_rate(user_id, year, month):
        inc, exp = FinanceService.get_period_data(user_id, year, month)
        return ((inc - exp) / inc) * 100 if inc > 0 else 0.0

    @staticmethod
    def get_fiscal_month_label(year, month, start_day):
        """Generate label for fiscal month based on start day."""
        if start_day == 1:
            return calendar.month_name[month][:3]
        
        # Calculate start and end dates
        start_date = date(int(year), month, start_day)
        if month == 12:
            end_date = date(int(year) + 1, 1, start_day) - timedelta(days=1)
        else:
            end_date = date(int(year), month + 1, start_day) - timedelta(days=1)
            
        return f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"

    @staticmethod
    def get_fiscal_data(user_id, year, month, start_day):
        """Fetch transaction data for a specific fiscal month or 'All' months."""
        if month == "All":
            # Year-wide range
            start_date_str = f"{year}-01-01"
            end_date_str = f"{year}-12-31"
        else:
            # Specific month range
            m_int = int(month)
            start_date_str = date(int(year), m_int, start_day).strftime("%Y-%m-%d")
            if m_int == 12:
                end_date_str = (date(int(year) + 1, 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                end_date_str = (date(int(year), m_int + 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
            
        # Pull ALL transactions for this user and filter in Python to avoid SQLite date issues
        query = """
            SELECT amount, date, type FROM (
                SELECT amount, date, type, user_id FROM transactions
                UNION ALL
                SELECT amount, date, txn_type as type, user_id FROM credit_card_transactions
            )
            WHERE user_id = ?
        """
        res = db.execute(query, (user_id,))
        inc, exp = 0.0, 0.0
        
        if res and res.rows:
            for r in res.rows:
                # Safety check for NULL values
                val = r[0] if r[0] is not None else 0.0
                amt, dt, t_type = float(val), str(r[1])[:10], str(r[2] or 'Expense').upper()
                if start_date_str <= dt <= end_date_str:
                    if t_type == 'INCOME':
                        inc += amt
                    else:
                        exp += amt
                        
        return inc, exp

    @staticmethod
    def repair_legacy_data(user_id="admin"):
        """One-time repair to assign orphaned transactions to admin."""
        tables = ['transactions', 'credit_card_transactions', 'accounts', 'budgets', 'subscriptions', 'goals', 'assets', 'loans', 'credit_cards']
        for t in tables:
            try:
                if user_id == "admin":
                    # Admin can claim everything that is orphan or legacy 'admin' tag
                    db.execute(f"UPDATE {t} SET user_id = ? WHERE user_id IS NULL OR user_id = 'default_user' OR user_id = '' OR user_id = 'admin'", (user_id,))
                else:
                    # Normal users can ONLY claim truly orphan data, NEVER 'admin' data
                    db.execute(f"UPDATE {t} SET user_id = ? WHERE user_id IS NULL OR user_id = 'default_user' OR user_id = ''", (user_id,))
            except: pass
            
        # Fix category mapping mix-ups
        db.execute("UPDATE transactions SET category_id = '8' WHERE category_id = '16' AND user_id = ?", (user_id,))
        db.execute("UPDATE transactions SET category_id = '14' WHERE description LIKE 'EMI Payment%' AND user_id = ?", (user_id,))
        db.execute("UPDATE transactions SET category_id = '15' WHERE description LIKE 'Loan EMI%' AND user_id = ?", (user_id,))

    @staticmethod
    def get_setting(key, default=None, user_id="admin"):
        res = db.execute("SELECT value FROM settings WHERE key = ? AND user_id = ?", (key, user_id))
        if res and res.rows:
            return res.rows[0][0]
        return default

    @staticmethod
    def set_setting(key, value, user_id="admin"):
        db.execute("INSERT OR REPLACE INTO settings (key, user_id, value) VALUES (?, ?, ?)", (key, user_id, str(value)))
