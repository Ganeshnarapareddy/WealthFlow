import pandas as pd
import uuid
import calendar
from datetime import datetime, timedelta
from database import db


class CreditCardService:
    """Manage credit cards and their transactions."""

    @staticmethod
    def get_cards(user_id):
        """Get all credit cards for a user."""
        res = db.execute(
            "SELECT id, name, bank, card_limit, billing_date, closing_date, current_balance "
            "FROM credit_cards WHERE user_id = ? ORDER BY name", (user_id,)
        )
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=[
                "id", "name", "bank", "card_limit", "billing_date",
                "closing_date", "current_balance"
            ])
        return pd.DataFrame(columns=[
            "id", "name", "bank", "card_limit", "billing_date",
            "closing_date", "current_balance"
        ])

    @staticmethod
    def get_card_by_id(card_id):
        """Get a single card by ID."""
        res = db.execute(
            "SELECT id, name, bank, card_limit, billing_date, closing_date, current_balance, user_id "
            "FROM credit_cards WHERE id = ?",
            (card_id,)
        )
        if res and res.rows:
            return res.rows[0]
        return None

    @staticmethod
    def add_card(user_id, name, bank, card_limit, billing_date, closing_date):
        """Add a new credit card."""
        cid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO credit_cards (id, user_id, name, bank, card_limit, billing_date, closing_date, current_balance) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
            (cid, user_id, name, bank, card_limit, billing_date, closing_date)
        )

    @staticmethod
    def update_card(card_id, name, bank, card_limit, billing_date, closing_date):
        db.execute(
            "UPDATE credit_cards SET name = ?, bank = ?, card_limit = ?, "
            "billing_date = ?, closing_date = ? WHERE id = ?",
            (name, bank, card_limit, billing_date, closing_date, card_id)
        )

    @staticmethod
    def delete_card(card_id, user_id):
        # Verify ownership
        res = db.execute("SELECT id FROM credit_cards WHERE id = ? AND user_id = ?", (card_id, user_id))
        if res and res.rows:
            db.execute("DELETE FROM credit_card_transactions WHERE card_id = ? AND user_id = ?", (card_id, user_id))
            db.execute("DELETE FROM credit_cards WHERE id = ? AND user_id = ?", (card_id, user_id))

    @staticmethod
    def add_transaction(user_id, card_id, amount, description, txn_type, txn_date=None, sync_bank=False):
        tid = str(uuid.uuid4())
        if not txn_date: txn_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        linked_id = None
        if txn_type == "payment" and sync_bank:
            res = db.execute("SELECT id FROM categories WHERE name = 'CC Bill Payment' LIMIT 1")
            cat_id = res.rows[0][0] if res and res.rows else None
            if not cat_id:
                cat_id = str(uuid.uuid4())
                db.execute("INSERT INTO categories (id, name, type, icon) VALUES (?, ?, ?, ?)",
                           (cat_id, 'CC Bill Payment', 'Expense', '🏦'))
            
            from services.finance_service import FinanceService
            try: dt_obj = datetime.strptime(txn_date, "%Y-%m-%d %H:%M")
            except: dt_obj = datetime.strptime(txn_date, "%Y-%m-%d")
            linked_id = FinanceService.add_transaction(amount, cat_id, f"Payment: {description}", dt_obj, "Expense", user_id)
        
        adj = -amount if txn_type == "expense" else amount
        db.execute("UPDATE credit_cards SET current_balance = current_balance + ? WHERE id = ?", (adj, card_id))
        db.execute(
            "INSERT INTO credit_card_transactions (id, user_id, card_id, amount, description, date, txn_type, linked_txn_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tid, user_id, card_id, amount, description, txn_date, txn_type, linked_id)
        )

    @staticmethod
    def delete_transaction(tid, user_id):
        res = db.execute("SELECT amount, txn_type, card_id, linked_txn_id FROM credit_card_transactions WHERE id = ? AND user_id = ?", (tid, user_id))
        if res and res.rows:
            row = res.rows[0]
            adj = row[0] if row[1] == "expense" else -row[0]
            db.execute("UPDATE credit_cards SET current_balance = current_balance + ? WHERE id = ? AND user_id = ?", (adj, row[2], user_id))
            if row[3]:
                from services.finance_service import FinanceService
                FinanceService.delete_transaction(row[3], user_id)
            db.execute("DELETE FROM credit_card_transactions WHERE id = ? AND user_id = ?", (tid, user_id))

    @staticmethod
    def get_card_transactions(card_id, year=None, month=None):
        query = "SELECT id, date, description, amount, txn_type FROM credit_card_transactions WHERE card_id = ?"
        params = [card_id]
        if year and year != "All" and month and month != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}-{month:02d}%")
        elif year and year != "All":
            query += " AND date LIKE ?"
            params.append(f"{year}%")
        query += " ORDER BY date DESC LIMIT 50"
        res = db.execute(query, tuple(params))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "date", "description", "amount", "txn_type"])
        return pd.DataFrame(columns=["id", "date", "description", "amount", "txn_type"])

    @staticmethod
    def get_total_outstanding(user_id):
        res = db.execute("SELECT COALESCE(SUM(current_balance), 0) FROM credit_cards WHERE user_id = ?", (user_id,))
        return float(res.rows[0][0]) if res and res.rows else 0.0

    @staticmethod
    def get_upcoming_bills(user_id, days=15):
        today = datetime.now().date()
        cards = CreditCardService.get_cards(user_id)
        upcoming = []
        for _, row in cards.iterrows():
            bd = int(row['closing_date'] or 1)
            now = datetime.now()
            try:
                next_bill = datetime(now.year, now.month, bd).date()
                if next_bill < today:
                    if now.month == 12: next_bill = datetime(now.year + 1, 1, bd).date()
                    else: next_bill = datetime(now.year, now.month + 1, bd).date()
                days_left = (next_bill - today).days
                if 0 <= days_left <= days:
                    upcoming.append({
                        "id": row['id'], "name": row['name'], "bank": row['bank'],
                        "closing_date": bd, "days_left": days_left,
                        "balance": row['current_balance'], "limit": row['card_limit']
                    })
            except: continue
        return sorted(upcoming, key=lambda x: x['days_left'])

    @staticmethod
    def add_emi(user_id, card_id, description, total_amount, monthly_amount, tenure, start_date):
        eid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO credit_card_emis (id, user_id, card_id, description, total_amount, monthly_amount, tenure, start_date, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (eid, user_id, card_id, description, total_amount, monthly_amount, tenure, start_date, 'active')
        )
        st_date = datetime.strptime(start_date, "%Y-%m-%d")
        for i in range(tenure):
            y = st_date.year + (st_date.month + i - 1) // 12
            m = (st_date.month + i - 1) % 12 + 1
            d = min(st_date.day, calendar.monthrange(y, m)[1])
            db.execute(
                "INSERT INTO credit_card_emi_payments (id, emi_id, due_date, amount, status) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), eid, f"{y}-{m:02d}-{d:02d}", monthly_amount, 'pending')
            )

    @staticmethod
    def get_card_emis(card_id):
        res = db.execute("""
            SELECT e.id, e.description, e.total_amount, e.monthly_amount, e.tenure, e.start_date,
                   (SELECT COUNT(*) FROM credit_card_emi_payments WHERE emi_id = e.id AND status = 'pending') as remaining_tenure
            FROM credit_card_emis e 
            WHERE e.card_id = ? AND e.status = 'active'
        """, (card_id,))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "Description", "Total", "Monthly", "Tenure", "Start", "Remaining"])
        return pd.DataFrame(columns=["id", "Description", "Total", "Monthly", "Tenure", "Start", "Remaining"])

    @staticmethod
    def get_all_active_emis(user_id):
        res = db.execute("SELECT id, monthly_amount FROM credit_card_emis WHERE user_id = ? AND status = 'active'", (user_id,))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "Monthly"])
        return pd.DataFrame(columns=["id", "Monthly"])

    @staticmethod
    def get_upcoming_emi_payments(user_id, days_ahead=30):
        res = db.execute("""
            SELECT p.id, e.description, p.amount, p.due_date, c.name as card_name
            FROM credit_card_emi_payments p
            JOIN credit_card_emis e ON p.emi_id = e.id
            JOIN credit_cards c ON e.card_id = c.id
            WHERE e.user_id = ? AND p.status = 'pending' AND p.due_date <= date('now', '+' || ? || ' days')
            ORDER BY p.due_date ASC
        """, (user_id, days_ahead))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "Description", "Amount", "Due Date", "Card"])
        return pd.DataFrame(columns=["id", "Description", "Amount", "Due Date", "Card"])

    @staticmethod
    def delete_emi(emi_id):
        db.execute("DELETE FROM credit_card_emi_payments WHERE emi_id = ?", (emi_id,))
        db.execute("DELETE FROM credit_card_emis WHERE id = ?", (emi_id,))

    @staticmethod
    def mark_emi_paid(payment_id, paid_date=None):
        if not paid_date: paid_date = str(datetime.now().date())
        
        # Get payment details first
        res_p = db.execute("""
            SELECT p.amount, e.description, e.user_id, e.card_id 
            FROM credit_card_emi_payments p
            JOIN credit_card_emis e ON p.emi_id = e.id
            WHERE p.id = ?
        """, (payment_id,))
        
        if res_p and res_p.rows:
            amount, desc, uid, card_id = res_p.rows[0]
            
            # 1. Update EMI payment status
            db.execute("UPDATE credit_card_emi_payments SET status = 'paid', paid_date = ? WHERE id = ?", (paid_date, payment_id))
            
            # 2. Record in main transactions
            from services.finance_service import FinanceService
            # Capture full current time for the transaction
            now_dt = datetime.now()
            
            FinanceService.add_transaction(
                amount=amount,
                category_id="14", 
                description=f"EMI Payment: {desc}",
                date_obj=now_dt,
                txn_type="Expense",
                user_id=uid
            )
            
            # 3. Check if EMI is fully completed
            res = db.execute("SELECT emi_id FROM credit_card_emi_payments WHERE id = ?", (payment_id,))
            if res and res.rows:
                emi_id = res.rows[0][0]
                res_pend = db.execute("SELECT COUNT(*) FROM credit_card_emi_payments WHERE emi_id = ? AND status = 'pending'", (emi_id,))
                if res_pend and res_pend.rows and res_pend.rows[0][0] == 0:
                    db.execute("UPDATE credit_card_emis SET status = 'completed' WHERE id = ?", (emi_id,))

    @staticmethod
    def get_card_total_outstanding(card_id):
        res_bal = db.execute("SELECT current_balance FROM credit_cards WHERE id = ?", (card_id,))
        bal = float(res_bal.rows[0][0]) if res_bal and res_bal.rows else 0.0
        res_emi = db.execute("""
            SELECT COALESCE(SUM(p.amount), 0) FROM credit_card_emi_payments p
            JOIN credit_card_emis e ON p.emi_id = e.id
            WHERE e.card_id = ? AND p.status = 'pending'
        """, (card_id,))
        emi_rem = float(res_emi.rows[0][0]) if res_emi and res_emi.rows else 0.0
        return max(0, -bal) + emi_rem

    @staticmethod
    def get_card_available_limit(card_id):
        res = db.execute("SELECT card_limit, current_balance FROM credit_cards WHERE id = ?", (card_id,))
        if res and res.rows:
            limit, bal = res.rows[0]
            res_emi = db.execute("""
                SELECT COALESCE(SUM(p.amount), 0) FROM credit_card_emi_payments p
                JOIN credit_card_emis e ON p.emi_id = e.id
                WHERE e.card_id = ? AND p.status = 'pending'
            """, (card_id,))
            emi_rem = float(res_emi.rows[0][0]) if res_emi and res_emi.rows else 0.0
            return (limit or 0.0) + min(0.0, bal or 0.0) - emi_rem
        return 0.0

    @staticmethod
    def sync_card_balance(card_id):
        """Recalculate balance from transactions to ensure consistency."""
        res = db.execute("SELECT SUM(CASE WHEN txn_type='expense' THEN -amount ELSE amount END) FROM credit_card_transactions WHERE card_id = ?", (card_id,))
        bal = float(res.rows[0][0]) if res and res.rows and res.rows[0][0] is not None else 0.0
        db.execute("UPDATE credit_cards SET current_balance = ? WHERE id = ?", (bal, card_id))

    @staticmethod
    def get_emi_payments(emi_id):
        """Get all payments for a specific EMI."""
        res = db.execute(
            "SELECT id, due_date, amount, status, paid_date FROM credit_card_emi_payments "
            "WHERE emi_id = ? ORDER BY due_date ASC", (emi_id,)
        )
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "Date", "Amount", "Status", "Paid Date"])
        return pd.DataFrame(columns=["id", "Date", "Amount", "Status", "Paid Date"])
