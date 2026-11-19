import pandas as pd
import uuid
import calendar
from datetime import datetime, timedelta, date
import streamlit as st
from database import db


@st.cache_data(ttl=60, show_spinner=False)
def _cached_categories(user_id, v: int):
    if user_id:
        res = db.execute("SELECT id, name, type, icon, user_id FROM categories WHERE user_id IS NULL OR user_id = ? ORDER BY name", (user_id,))
    else:
        res = db.execute("SELECT id, name, type, icon, user_id FROM categories WHERE user_id IS NULL ORDER BY name")
    if res and res.rows:
        return pd.DataFrame(res.rows, columns=["id", "name", "type", "icon", "user_id"])
    return pd.DataFrame(columns=["id", "name", "type", "icon", "user_id"])


@st.cache_data(ttl=60, show_spinner=False)
def _cached_all_settings(user_id: str, v: int):
    res = db.execute("SELECT key, value FROM settings WHERE user_id = ?", (user_id,))
    out = {}
    if res and res.rows:
        for k, val in res.rows:
            out[k] = val
    return out


@st.cache_data(ttl=60, show_spinner=False)
def _cached_default_account(user_id: str, v: int):
    res = db.execute("SELECT id FROM accounts WHERE user_id = ? LIMIT 1", (user_id,))
    return res.rows[0][0] if res and res.rows else "default_account_admin"


@st.cache_data(ttl=60, show_spinner=False)
def _cached_available_years(user_id: str, v: int):
    res = db.execute(
        "SELECT DISTINCT SUBSTR(date, 1, 4) as yr FROM ("
        "SELECT date, user_id FROM transactions UNION ALL SELECT date, user_id FROM credit_card_transactions"
        ") WHERE user_id = ? ORDER BY yr DESC",
        (user_id,),
    )
    if res and res.rows:
        yrs = [int(r[0]) for r in res.rows if r[0] and str(r[0]).isdigit()]
        if yrs:
            return yrs
    return [datetime.now().year]


@st.cache_data(ttl=60, show_spinner=False)
def _cached_filtered_transactions(user_id, year, month, day, txn_type, description_search, category_name, limit, v: int):
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
    cols = ["ID", "Date", "Description", "Amount", "Category", "Icon", "Type", "Source"]
    if res and res.rows:
        return pd.DataFrame(res.rows, columns=cols)
    return pd.DataFrame(columns=cols)


@st.cache_data(ttl=60, show_spinner=False)
def _cached_spending_by_category(user_id, year, month, start_day, v: int):
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
        start_date = date(int(year), int(month), start_day).strftime("%Y-%m-%d")
        if int(month) == 12:
            end_date = (date(int(year) + 1, 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            end_date = (date(int(year), int(month) + 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
        params.extend([start_date, end_date])
    elif year and year != "All":
        query += " AND date LIKE ?"
        params.append(f"{year}%")

    query += " GROUP BY Category ORDER BY Amount DESC"
    res = db.execute(query, tuple(params))
    rows = [[r[0] if r[0] else "Other", r[1]] for r in res.rows] if (res and res.rows) else []
    return pd.DataFrame(rows, columns=["Category", "Amount"]) if rows else pd.DataFrame(columns=["Category", "Amount"])


@st.cache_data(ttl=60, show_spinner=False)
def _cached_daily_spending(user_id, year, month, start_day, v: int):
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
        start_date = date(int(year), int(month), start_day).strftime("%Y-%m-%d")
        if int(month) == 12:
            end_date = (date(int(year) + 1, 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            end_date = (date(int(year), int(month) + 1, start_day) - timedelta(days=1)).strftime("%Y-%m-%d")
        params.extend([start_date, end_date])
    elif year and year != "All":
        query += " AND Date LIKE ?"
        params.append(f"{year}%")

    query += " GROUP BY Date, Category ORDER BY Date ASC"
    res = db.execute(query, tuple(params))
    rows = [[r[0], r[1] if r[1] else "Other", r[2]] for r in res.rows] if (res and res.rows) else []
    return pd.DataFrame(rows, columns=["Date", "Category", "Amount"]) if rows else pd.DataFrame(columns=["Date", "Category", "Amount"])


@st.cache_data(ttl=60, show_spinner=False)
def _cached_income_expense_by_month(user_id, year, month, v: int):
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
        params.append(f"{year}-{int(month):02d}%")
    elif year and year != "All":
        query += " AND date LIKE ?"
        params.append(f"{year}%")
    query += " GROUP BY Month ORDER BY Month DESC"
    res = db.execute(query, tuple(params))
    if res and res.rows:
        df = pd.DataFrame(res.rows, columns=["Month", "Income", "Expense"])
        return df.iloc[::-1]
    return pd.DataFrame(columns=["Month", "Income", "Expense"])


@st.cache_data(ttl=60, show_spinner=False)
def _cached_spending_trend(user_id, year, month, months, v: int):
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
        params.append(f"{year}-{int(month):02d}%")
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


@st.cache_data(ttl=60, show_spinner=False)
def _cached_dashboard_bundle(user_id: str, sel_year, sel_month, month_mode: str, fiscal_day: int, v: int):
    """Fetch ALL Dashboard KPIs, Credit Cards, Alerts, and Wealth Allocation in ONE Turso HTTP roundtrip!"""
    now = datetime.now()
    today = now.date()
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    month_year = now.strftime("%m-%Y")

    # Period WHERE clause for current period
    p_where = "WHERE user_id = ?"
    p_params = [user_id]
    if sel_year != "All" and sel_month != "All":
        p_where += " AND date LIKE ?"
        p_params.append(f"{sel_year}-{int(sel_month):02d}%")
    elif sel_year != "All":
        p_where += " AND date LIKE ?"
        p_params.append(f"{sel_year}%")

    # Previous period SQL
    if sel_year == "All" or sel_month == "All":
        prev_sql = (
            "SELECT SUBSTR(date, 1, 7) as ym, "
            "SUM(CASE WHEN type='Income' THEN amount ELSE 0 END), "
            "SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) "
            "FROM (SELECT date, amount, type, user_id FROM transactions UNION ALL "
            "SELECT date, amount, 'Expense' as type, user_id FROM credit_card_transactions WHERE txn_type='expense') "
            "WHERE user_id = ? GROUP BY ym ORDER BY ym DESC LIMIT 2"
        )
        prev_params = (user_id,)
        prev_is_specific = False
        prev_label_default = "Previous"
    else:
        pm = int(sel_month) - 1
        py = int(sel_year)
        if pm == 0:
            pm = 12
            py -= 1
        prev_pat = f"{py}-{pm:02d}%"
        prev_sql = (
            "SELECT SUM(CASE WHEN UPPER(type)='INCOME' THEN amount ELSE 0 END), "
            "SUM(CASE WHEN UPPER(type)='EXPENSE' THEN amount ELSE 0 END) "
            "FROM (SELECT amount, user_id, date, type FROM transactions UNION ALL "
            "SELECT amount, user_id, date, 'Expense' as type FROM credit_card_transactions WHERE UPPER(txn_type)='EXPENSE') "
            "WHERE user_id = ? AND date LIKE ?"
        )
        prev_params = (user_id, prev_pat)
        prev_is_specific = True
        prev_label_default = f"{py}-{pm:02d}"

    stmts = [
        # 0: Accounts sum
        ("SELECT COALESCE(SUM(balance), 0) FROM accounts WHERE user_id = ?", (user_id,)),
        # 1: Assets by type (also gives total assets for net worth!)
        ("SELECT type, COALESCE(SUM(value), 0) FROM assets WHERE user_id = ? GROUP BY type", (user_id,)),
        # 2: Current period income + expense combined
        (
            "SELECT COALESCE(SUM(CASE WHEN UPPER(type)='INCOME' THEN amount ELSE 0 END), 0), "
            "COALESCE(SUM(CASE WHEN UPPER(type)='EXPENSE' THEN amount ELSE 0 END), 0) "
            "FROM (SELECT amount, user_id, date, type FROM transactions UNION ALL "
            "SELECT amount, user_id, date, 'Expense' as type FROM credit_card_transactions WHERE UPPER(txn_type)='EXPENSE') "
            + p_where,
            tuple(p_params),
        ),
        # 3: Today vs Yesterday combined
        (
            "SELECT "
            "COALESCE(SUM(CASE WHEN date LIKE ? THEN amount ELSE 0 END), 0), "
            "COALESCE(SUM(CASE WHEN date LIKE ? THEN amount ELSE 0 END), 0) "
            "FROM (SELECT amount, date FROM transactions WHERE user_id=? AND UPPER(type)='EXPENSE' AND (date LIKE ? OR date LIKE ?) "
            "UNION ALL "
            "SELECT amount, date FROM credit_card_transactions WHERE user_id=? AND UPPER(txn_type)='EXPENSE' AND (date LIKE ? OR date LIKE ?))",
            (f"{today_str}%", f"{yesterday_str}%", user_id, f"{today_str}%", f"{yesterday_str}%", user_id, f"{today_str}%", f"{yesterday_str}%"),
        ),
        # 4: Previous period
        (prev_sql, prev_params),
        # 5: All subscriptions (gives burn, count, prev_burn, AND upcoming renewals)
        ("SELECT id, name, amount, billing_cycle, start_date, next_billing_date, category, icon FROM subscriptions WHERE user_id = ? ORDER BY name", (user_id,)),
        # 6: Active CC EMIs
        ("SELECT id, monthly_amount FROM credit_card_emis WHERE user_id = ? AND status = 'active'", (user_id,)),
        # 7: Active Loan EMIs
        ("SELECT id, emi_amount FROM loans WHERE user_id = ? AND emi_active = 1 AND status != 'paid'", (user_id,)),
        # 8: Credit cards (gives utilization AND upcoming bills)
        ("SELECT id, name, bank, card_limit, billing_date, closing_date, current_balance FROM credit_cards WHERE user_id = ? ORDER BY name", (user_id,)),
        # 9: Upcoming non-EMI loans
        ("SELECT id, person_name, amount, loan_type, due_date, remaining_amount FROM loans WHERE user_id = ? AND due_date != '' AND status = 'pending' AND emi_active = 0 ORDER BY due_date ASC", (user_id,)),
        # 10: Upcoming loan EMI payments (30 days)
        (
            "SELECT p.id, l.person_name, p.amount, l.loan_type, p.due_date, l.remaining_amount, l.id as loan_id "
            "FROM loan_payments p JOIN loans l ON p.loan_id = l.id "
            "WHERE l.user_id = ? AND l.emi_active = 1 AND p.status = 'pending' AND p.due_date <= date('now', '+30 days') "
            "ORDER BY p.due_date ASC",
            (user_id,),
        ),
        # 11: Upcoming CC EMI payments (30 days)
        (
            "SELECT p.id, e.description, p.amount, p.due_date, c.name as card_name "
            "FROM credit_card_emi_payments p JOIN credit_card_emis e ON p.emi_id = e.id JOIN credit_cards c ON e.card_id = c.id "
            "WHERE e.user_id = ? AND p.status = 'pending' AND p.due_date <= date('now', '+30 days') "
            "ORDER BY p.due_date ASC",
            (user_id,),
        ),
        # 12: Actioned alerts for current month (eliminates N+1 checks)
        ("SELECT alert_id FROM actioned_alerts WHERE user_id = ? AND month_year = ?", (user_id, month_year)),
        # 13: Today's transactions descriptions (eliminates N+1 auto_txn_exists checks)
        ("SELECT description FROM transactions WHERE user_id = ? AND date LIKE ?", (user_id, f"{today_str}%")),
    ]

    if month_mode == "Fiscal":
        stmts.append((
            "SELECT amount, date, type FROM ("
            "SELECT amount, date, type, user_id FROM transactions UNION ALL "
            "SELECT amount, date, txn_type as type, user_id FROM credit_card_transactions"
            ") WHERE user_id = ?",
            (user_id,),
        ))

    res = db.batch(stmts)

    # Unpack Net Worth & Assets
    acc_sum = float(res[0].rows[0][0]) if res[0] and res[0].rows and res[0].rows[0][0] else 0.0
    asset_data = []
    asset_sum = 0.0
    if res[1] and res[1].rows:
        for row in res[1].rows:
            val = float(row[1] or 0.0)
            asset_data.append({"Category": row[0], "Amount": val})
            asset_sum += val
    net_worth = acc_sum + asset_sum

    # Unpack Income & Expense
    inc = float(res[2].rows[0][0]) if res[2] and res[2].rows and res[2].rows[0][0] else 0.0
    exp = float(res[2].rows[0][1]) if res[2] and res[2].rows and res[2].rows[0][1] else 0.0
    if month_mode == "Fiscal" and len(res) > 14:
        inc, exp = FinanceService._compute_fiscal_from_rows(res[14].rows if res[14] else [], sel_year, sel_month, fiscal_day)

    # Unpack Today vs Yesterday
    today_spent = float(res[3].rows[0][0]) if res[3] and res[3].rows and res[3].rows[0][0] else 0.0
    yesterday_spent = float(res[3].rows[0][1]) if res[3] and res[3].rows and res[3].rows[0][1] else 0.0

    # Unpack Previous Period
    prev_inc, prev_exp, prev_label = 0.0, 0.0, prev_label_default
    if prev_is_specific:
        if res[4] and res[4].rows:
            prev_inc = float(res[4].rows[0][0] or 0.0)
            prev_exp = float(res[4].rows[0][1] or 0.0)
    else:
        if res[4] and res[4].rows and len(res[4].rows) >= 2:
            prev_row = res[4].rows[1]
            prev_label = prev_row[0]
            prev_inc = float(prev_row[1] or 0.0)
            prev_exp = float(prev_row[2] or 0.0)

    # Unpack Subscriptions (burn, count, prev_burn, upcoming renewals)
    from services.recurring_service import RecurringService
    subs_rows = res[5].rows if (res[5] and res[5].rows) else []
    active_subs_count = len(subs_rows)
    burn = 0.0
    prev_burn = 0.0
    prev_sub_cutoff = None
    if sel_year != "All" and sel_month != "All":
        pm = int(sel_month) - 1
        py = int(sel_year)
        if pm == 0:
            pm = 12
            py -= 1
        prev_sub_cutoff = f"{py + 1}-01-01" if pm == 12 else f"{py}-{pm + 1:02d}-01"

    upcoming_subs = []
    for row in subs_rows:
        sid, sname, samt, scycle, sstart, snext, _, _ = row
        samt = float(samt or 0.0)
        m_cost = 0.0
        if scycle == "Monthly": m_cost = samt
        elif scycle == "Quarterly": m_cost = samt / 3
        elif scycle == "6 Months": m_cost = samt / 6
        elif scycle == "Yearly": m_cost = samt / 12
        elif scycle and str(scycle).startswith("Custom:"):
            try: m_cost = samt / int(str(scycle).split(":")[1])
            except: pass
        burn += m_cost
        if prev_sub_cutoff and sstart and str(sstart) < prev_sub_cutoff:
            prev_burn += m_cost
        try:
            nd = datetime.strptime(snext, "%Y-%m-%d").date()
            nd = RecurringService._project_next_date(nd, scycle, today)
            dl = (nd - today).days
            if 0 <= dl <= 30:
                upcoming_subs.append({
                    "id": sid, "name": sname, "amount": samt,
                    "cycle": scycle, "days_left": dl, "next_date": nd,
                })
        except Exception:
            pass
    upcoming_subs.sort(key=lambda x: x["days_left"])

    # Unpack EMIs
    cc_emi_rows = res[6].rows if (res[6] and res[6].rows) else []
    loan_emi_rows = res[7].rows if (res[7] and res[7].rows) else []
    total_emi_amt = sum(float(r[1] or 0.0) for r in cc_emi_rows) + sum(float(r[1] or 0.0) for r in loan_emi_rows)
    active_emi_count = len(cc_emi_rows) + len(loan_emi_rows)

    # Unpack Credit Cards & Upcoming Bills
    card_cols = ["id", "name", "bank", "card_limit", "billing_date", "closing_date", "current_balance"]
    cards_df = pd.DataFrame(res[8].rows, columns=card_cols) if (res[8] and res[8].rows) else pd.DataFrame(columns=card_cols)
    upcoming_bills = []
    for _, crow in cards_df.iterrows():
        bal = -crow["current_balance"] if crow["current_balance"] else 0
        if bal <= 0:
            continue
        bd = int(crow["closing_date"] or 1)
        try:
            next_bill = datetime(now.year, now.month, bd).date()
            if next_bill < today:
                next_bill = datetime(now.year + 1, 1, bd).date() if now.month == 12 else datetime(now.year, now.month + 1, bd).date()
            dl = (next_bill - today).days
            if 0 <= dl <= 30:
                upcoming_bills.append({
                    "id": crow["id"], "name": crow["name"], "bank": crow["bank"],
                    "closing_date": bd, "due_date": next_bill, "days_left": dl,
                    "balance": bal, "limit": crow["card_limit"],
                })
        except Exception:
            continue
    upcoming_bills.sort(key=lambda x: x["days_left"])

    # Unpack Actioned Alerts & Today's Auto Transactions (O(1) sets!)
    actioned_set = {str(r[0]) for r in res[12].rows} if (res[12] and res[12].rows) else set()
    today_txn_descs = {str(r[0]) for r in res[13].rows} if (res[13] and res[13].rows) else set()

    # Build Consolidated Alerts (ZERO extra DB queries!)
    all_alerts = []
    for s in upcoming_subs:
        aid = f"sub_{s['id']}"
        if aid not in actioned_set and f"Auto: {s['name']}" not in today_txn_descs:
            all_alerts.append({
                "category": "Subscription", "days": s["days_left"],
                "date": s["next_date"].strftime("%d %b"), "name": s["name"],
                "amount": s["amount"], "id": aid, "icon": "💳",
            })

    if res[9] and res[9].rows:
        for row in res[9].rows:
            try:
                due = datetime.strptime(row[4], "%Y-%m-%d").date()
                dl = (due - today).days
                if 0 <= dl <= 30 and f"Auto: {row[1]}" not in today_txn_descs:
                    all_alerts.append({
                        "category": "Loan", "days": dl,
                        "date": due.strftime("%d %b"),
                        "name": f"{row[1]} ({'Given' if row[3] == 'given' else 'Taken'})",
                        "amount": row[5], "id": row[0], "icon": "💰", "is_emi": False,
                    })
            except Exception:
                continue

    if res[10] and res[10].rows:
        for row in res[10].rows:
            try:
                due = datetime.strptime(row[4], "%Y-%m-%d").date()
                dl = (due - today).days
                if 0 <= dl <= 30 and f"Auto: {row[1]}" not in today_txn_descs:
                    all_alerts.append({
                        "category": "Loan", "days": dl,
                        "date": due.strftime("%d %b"),
                        "name": f"{row[1]} ({'Given' if row[3] == 'given' else 'Taken'})",
                        "amount": row[2], "id": row[0], "icon": "💰", "is_emi": True,
                    })
            except Exception:
                continue

    if res[11] and res[11].rows:
        for row in res[11].rows:
            try:
                due = datetime.strptime(row[3], "%Y-%m-%d").date()
                dl = (due - today).days
                if f"Auto: {row[1]}" not in today_txn_descs:
                    all_alerts.append({
                        "category": "EMI", "days": dl,
                        "date": due.strftime("%d %b"),
                        "name": f"{row[1]} ({row[4]})", "amount": row[2], "id": row[0], "icon": "🗓️",
                    })
            except Exception:
                continue

    for b in upcoming_bills:
        all_alerts.append({
            "category": "Bill", "days": b["days_left"],
            "date": b["due_date"].strftime("%d %b"),
            "name": f"{b['name']} Bill", "amount": b["balance"], "id": b["id"], "icon": "💳",
        })

    all_alerts.sort(key=lambda x: x["days"])

    return {
        "net_worth": net_worth,
        "asset_data": asset_data,
        "inc": inc,
        "exp": exp,
        "today_spent": today_spent,
        "yesterday_spent": yesterday_spent,
        "prev_inc": prev_inc,
        "prev_exp": prev_exp,
        "prev_label": prev_label,
        "burn": burn,
        "prev_burn": prev_burn,
        "active_subs_count": active_subs_count,
        "total_emi_amt": total_emi_amt,
        "active_emi_count": active_emi_count,
        "cards_df": cards_df,
        "all_alerts": all_alerts,
    }


class FinanceService:
    # v1.2 - Bulk batched dashboard bundle + versioned read caching
    """Core financial operations — transactions, categories, analytics."""

    @staticmethod
    def get_dashboard_bundle(user_id, sel_year, sel_month, month_mode="Calendar", fiscal_day=1):
        return _cached_dashboard_bundle(user_id, sel_year, sel_month, month_mode, int(fiscal_day), db.version)

    @staticmethod
    def get_categories(user_id=None):
        return _cached_categories(user_id, db.version)

    @staticmethod
    def add_category(name: str, cat_type: str, icon: str, user_id: str):
        name_clean = name.strip()
        if not name_clean:
            return False, "Category name cannot be empty."
        existing = db.execute(
            "SELECT id FROM categories WHERE LOWER(name) = LOWER(?) AND (user_id IS NULL OR user_id = ?)",
            (name_clean, user_id)
        )
        if existing and existing.rows:
            return False, f"Category '{name_clean}' already exists."
        cid = str(uuid.uuid4())
        icon_clean = (icon.strip() if icon and icon.strip() else "🏷️")[:8]
        type_clean = "Expense" if cat_type.lower() == "expense" else "Income"
        db.execute(
            "INSERT INTO categories (id, user_id, name, type, icon) VALUES (?, ?, ?, ?, ?)",
            (cid, user_id, name_clean, type_clean, icon_clean)
        )
        db.bump_version()
        return True, "Category added successfully."

    @staticmethod
    def update_category(cat_id: str, name: str, icon: str, user_id: str):
        name_clean = name.strip()
        if not name_clean:
            return False, "Category name cannot be empty."
        own = db.execute("SELECT id FROM categories WHERE id = ? AND user_id = ?", (str(cat_id), user_id))
        if not own or not own.rows:
            return False, "Cannot edit system categories or categories belonging to other users."
        icon_clean = (icon.strip() if icon and icon.strip() else "🏷️")[:8]
        db.execute(
            "UPDATE categories SET name = ?, icon = ? WHERE id = ? AND user_id = ?",
            (name_clean, icon_clean, str(cat_id), user_id)
        )
        db.bump_version()
        return True, "Category updated successfully."

    @staticmethod
    def delete_category(cat_id: str, user_id: str):
        own = db.execute("SELECT id FROM categories WHERE id = ? AND user_id = ?", (str(cat_id), user_id))
        if not own or not own.rows:
            return False, "Cannot delete system categories."
        db.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (str(cat_id), user_id))
        db.bump_version()
        return True, "Category deleted successfully."

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
            account_id = _cached_default_account(user_id, db.version)
        try:
            adj = amount if txn_type == "Income" else -amount
            db.batch([
                (
                    "INSERT INTO transactions (id, user_id, account_id, category_id, amount, type, date, description) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (tid, user_id, account_id, category_id, amount, txn_type, date_str, description),
                ),
                (
                    "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                    (adj, account_id),
                ),
            ])
            return tid
        except Exception:
            return None

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
            db.batch([
                ("UPDATE accounts SET balance = balance + ? WHERE id = ?", (adj, account_id)),
                ("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tid, user_id)),
            ])

    @staticmethod
    def get_filtered_transactions(user_id, year=None, month=None, day=None, txn_type=None, description_search=None, category_name=None, limit=100):
        return _cached_filtered_transactions(user_id, year, month, day, txn_type, description_search, category_name, limit, db.version)

    @staticmethod
    def get_recent_transactions(user_id, limit=50):
        return FinanceService.get_filtered_transactions(user_id, limit=limit)

    @staticmethod
    def get_net_worth(user_id):
        res_acc, res_ast = db.batch([
            ("SELECT SUM(balance) FROM accounts WHERE user_id = ?", (user_id,)),
            ("SELECT SUM(value) FROM assets WHERE user_id = ?", (user_id,)),
        ])
        acc = float(res_acc.rows[0][0]) if res_acc and res_acc.rows and res_acc.rows[0][0] else 0.0
        ast = float(res_ast.rows[0][0]) if res_ast and res_ast.rows and res_ast.rows[0][0] else 0.0
        return acc + ast

    @staticmethod
    def get_today_vs_yesterday(user_id):
        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        res = db.execute(
            "SELECT "
            "COALESCE(SUM(CASE WHEN date LIKE ? THEN amount ELSE 0 END), 0), "
            "COALESCE(SUM(CASE WHEN date LIKE ? THEN amount ELSE 0 END), 0) "
            "FROM (SELECT amount, date FROM transactions WHERE user_id=? AND UPPER(type)='EXPENSE' AND (date LIKE ? OR date LIKE ?) "
            "UNION ALL SELECT amount, date FROM credit_card_transactions WHERE user_id=? AND UPPER(txn_type)='EXPENSE' AND (date LIKE ? OR date LIKE ?))",
            (f"{today_str}%", f"{yesterday_str}%", user_id, f"{today_str}%", f"{yesterday_str}%", user_id, f"{today_str}%", f"{yesterday_str}%"),
        )
        today_val = float(res.rows[0][0]) if res and res.rows and res.rows[0][0] else 0.0
        yest_val = float(res.rows[0][1]) if res and res.rows and res.rows[0][1] else 0.0
        return today_val, yest_val

    @staticmethod
    def get_income_expense_by_month(user_id, year=None, month=None):
        return _cached_income_expense_by_month(user_id, year, month, db.version)

    @staticmethod
    def get_spending_trend(user_id, year=None, month=None, months=12):
        return _cached_spending_trend(user_id, year, month, months, db.version)

    @staticmethod
    def get_spending_by_category(user_id, year=None, month=None, start_day=1):
        return _cached_spending_by_category(user_id, year, month, start_day, db.version)

    @staticmethod
    def get_daily_spending_by_category(user_id, year=None, month=None, start_day=1):
        return _cached_daily_spending(user_id, year, month, start_day, db.version)

    @staticmethod
    def get_available_years(user_id):
        return _cached_available_years(user_id, db.version)

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
                    if len(parts) == 2:
                        months.append((int(parts[0]), int(parts[1])))
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

        res = db.execute(
            "SELECT COALESCE(SUM(CASE WHEN UPPER(type)='INCOME' THEN amount ELSE 0 END), 0), "
            "COALESCE(SUM(CASE WHEN UPPER(type)='EXPENSE' THEN amount ELSE 0 END), 0) "
            "FROM (SELECT amount, user_id, date, type FROM transactions UNION ALL "
            "SELECT amount, user_id, date, 'Expense' as type FROM credit_card_transactions WHERE UPPER(txn_type)='EXPENSE') "
            + where,
            tuple(params),
        )
        inc = float(res.rows[0][0]) if res and res.rows and res.rows[0][0] else 0.0
        exp = float(res.rows[0][1]) if res and res.rows and res.rows[0][1] else 0.0
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

        start_date = date(int(year), month, start_day)
        if month == 12:
            end_date = date(int(year) + 1, 1, start_day) - timedelta(days=1)
        else:
            end_date = date(int(year), month + 1, start_day) - timedelta(days=1)

        return f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"

    @staticmethod
    def _compute_fiscal_from_rows(rows, year, month, start_day):
        inc, exp = 0.0, 0.0
        for r in rows:
            val = r[0] if r[0] is not None else 0.0
            amt, dt, t_type = float(val), str(r[1])[:10], str(r[2] or 'Expense').upper()
            try:
                txn_date = datetime.strptime(dt, "%Y-%m-%d").date()
            except ValueError:
                continue

            in_range = False
            if year == "All":
                if month == "All":
                    in_range = True
                else:
                    m_int = int(month)
                    txn_year = txn_date.year
                    start_date = date(txn_year, m_int, start_day)
                    end_date = (date(txn_year + 1, 1, start_day) if m_int == 12 else date(txn_year, m_int + 1, start_day)) - timedelta(days=1)
                    in_range = (start_date <= txn_date <= end_date)
            else:
                y_int = int(year)
                if month == "All":
                    in_range = (txn_date.year == y_int)
                else:
                    m_int = int(month)
                    start_date = date(y_int, m_int, start_day)
                    end_date = (date(y_int + 1, 1, start_day) if m_int == 12 else date(y_int, m_int + 1, start_day)) - timedelta(days=1)
                    in_range = (start_date <= txn_date <= end_date)

            if in_range:
                if t_type == 'INCOME':
                    inc += amt
                else:
                    exp += amt
        return inc, exp

    @staticmethod
    def get_fiscal_data(user_id, year, month, start_day):
        query = """
            SELECT amount, date, type FROM (
                SELECT amount, date, type, user_id FROM transactions
                UNION ALL
                SELECT amount, date, txn_type as type, user_id FROM credit_card_transactions
            )
            WHERE user_id = ?
        """
        res = db.execute(query, (user_id,))
        return FinanceService._compute_fiscal_from_rows(res.rows if (res and res.rows) else [], year, month, start_day)

    @staticmethod
    def repair_legacy_data(user_id="admin"):
        """One-time repair to assign orphaned transactions to admin (batched)."""
        tables = ['transactions', 'credit_card_transactions', 'accounts', 'budgets', 'subscriptions', 'goals', 'assets', 'loans', 'credit_cards']
        stmts = []
        for t in tables:
            if user_id == "admin":
                stmts.append((f"UPDATE {t} SET user_id = ? WHERE user_id IS NULL OR user_id = 'default_user' OR user_id = '' OR user_id = 'admin'", (user_id,)))
            else:
                stmts.append((f"UPDATE {t} SET user_id = ? WHERE user_id IS NULL OR user_id = 'default_user' OR user_id = ''", (user_id,)))
        stmts.extend([
            ("UPDATE transactions SET category_id = '8' WHERE category_id = '16' AND user_id = ?", (user_id,)),
            ("UPDATE transactions SET category_id = '14' WHERE description LIKE 'EMI Payment%' AND user_id = ?", (user_id,)),
            ("UPDATE transactions SET category_id = '15' WHERE description LIKE 'Loan EMI%' AND user_id = ?", (user_id,)),
        ])
        db.batch(stmts)

    @staticmethod
    def get_setting(key, default=None, user_id="admin"):
        settings_map = _cached_all_settings(user_id, db.version)
        return settings_map.get(key, default)

    @staticmethod
    def set_setting(key, value, user_id="admin"):
        db.execute("INSERT OR REPLACE INTO settings (key, user_id, value) VALUES (?, ?, ?)", (key, user_id, str(value)))

    @staticmethod
    def update_setting(key, value, user_id="admin"):
        FinanceService.set_setting(key, value, user_id)
