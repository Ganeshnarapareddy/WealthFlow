import pandas as pd
import uuid
import calendar
from datetime import datetime, timedelta
from database import db


class CreditCardService:
    """Manage credit cards and their transactions."""

    @staticmethod
    def get_cards():
        """Get all credit cards."""
        res = db.execute(
            "SELECT id, name, bank, card_limit, billing_date, closing_date, current_balance "
            "FROM credit_cards ORDER BY name"
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
            "SELECT id, name, bank, card_limit, billing_date, closing_date, current_balance "
            "FROM credit_cards WHERE id = ?",
            (card_id,)
        )
        if res and res.rows:
            return res.rows[0]
        return None

    @staticmethod
    def add_card(name, bank, card_limit, billing_date, closing_date):
        """Add a new credit card."""
        cid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO credit_cards (id, name, bank, card_limit, billing_date, closing_date, current_balance) "
            "VALUES (?, ?, ?, ?, ?, ?, 0)",
            (cid, name, bank, card_limit, billing_date, closing_date)
        )

    @staticmethod
    def update_card(card_id, name, bank, card_limit, billing_date, closing_date):
        """Update card details."""
        db.execute(
            "UPDATE credit_cards SET name = ?, bank = ?, card_limit = ?, "
            "billing_date = ?, closing_date = ? WHERE id = ?",
            (name, bank, card_limit, billing_date, closing_date, card_id)
        )

    @staticmethod
    def delete_card(card_id):
        """Delete a card and its transactions."""
        db.execute("DELETE FROM credit_card_transactions WHERE card_id = ?", (card_id,))
        db.execute("DELETE FROM credit_cards WHERE id = ?", (card_id,))

    @staticmethod
    def add_transaction(card_id, amount, description, txn_type, txn_date=None, sync_bank=False):
        """Add a credit card transaction and update balance."""
        tid = str(uuid.uuid4())
        if not txn_date:
            txn_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        linked_id = None
        if txn_type == "payment" and sync_bank:
            # Find or create 'CC Bill Payment' category
            res = db.execute("SELECT id FROM categories WHERE name = 'CC Bill Payment' LIMIT 1")
            if res and res.rows:
                cat_id = res.rows[0][0]
            else:
                cat_id = str(uuid.uuid4())
                db.execute("INSERT INTO categories (id, name, type, icon) VALUES (?, ?, ?, ?)",
                           (cat_id, 'CC Bill Payment', 'Expense', '🏦'))
            
            # Record main transaction
            from services.finance_service import FinanceService
            # Handle both YYYY-MM-DD and YYYY-MM-DD HH:MM
            try:
                dt_obj = datetime.strptime(txn_date, "%Y-%m-%d %H:%M")
            except ValueError:
                dt_obj = datetime.strptime(txn_date, "%Y-%m-%d")
            linked_id = FinanceService.add_transaction(amount, cat_id, f"Payment: {description}", dt_obj, "Expense")
        
        # Update card balance (Expenses reduce balance, Payments increase it)
        adj = -amount if txn_type == "expense" else amount
        db.execute(
            "UPDATE credit_cards SET current_balance = current_balance + ? WHERE id = ?",
            (adj, card_id)
        )
        
        db.execute(
            "INSERT INTO credit_card_transactions (id, card_id, amount, description, date, txn_type, linked_txn_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tid, card_id, amount, description, txn_date, txn_type, linked_id)
        )

    @staticmethod
    def delete_transaction(tid, description=None, amount=None):
        """Delete a credit card transaction and reverse balance."""
        # Safety: check if linked_txn_id column exists
        try:
            res = db.execute("SELECT amount, txn_type, card_id, linked_txn_id FROM credit_card_transactions WHERE id = ?", (tid,))
        except Exception:
            res = db.execute("SELECT amount, txn_type, card_id FROM credit_card_transactions WHERE id = ?", (tid,))
            
        if res and res.rows:
            row = res.rows[0]
            amt_val = row[0]
            t_type = row[1]
            c_id = row[2]
            linked_id = row[3] if len(row) > 3 else None
            
            # Reverse balance impact
            adj = amt_val if t_type == "expense" else -amt_val
            db.execute("UPDATE credit_cards SET current_balance = current_balance + ? WHERE id = ?", (adj, c_id))
            
            # Delete linked ledger transaction
            if linked_id:
                try:
                    from services.finance_service import FinanceService
                    FinanceService.delete_transaction(linked_id)
                except Exception:
                    pass

        # Final Purge
        db.execute("DELETE FROM credit_card_transactions WHERE id = ?", (tid,))
        if description and amount:
            # Fallback purge by description if ID delete was missed
            db.execute("DELETE FROM credit_card_transactions WHERE description = ? AND amount = ?", (description, amount))

    @staticmethod
    def get_card_transactions(card_id, year=None, month=None):
        """Get transactions for a card, optionally filtered by year/month."""
        query = """
            SELECT id, date, description, amount, txn_type 
            FROM credit_card_transactions 
            WHERE card_id = ?
        """
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
    def get_card_balance(card_id):
        """Calculate current balance: sum(expenses) - sum(payments)."""
        res = db.execute(
            "SELECT COALESCE(SUM(CASE WHEN txn_type='payment' THEN amount ELSE 0 END), 0) - "
            "COALESCE(SUM(CASE WHEN txn_type='expense' THEN amount ELSE 0 END), 0) "
            "FROM credit_card_transactions WHERE card_id = ?",
            (card_id,)
        )
        if res and res.rows:
            return float(res.rows[0][0] or 0)
        return 0.0

    @staticmethod
    def sync_card_balance(card_id):
        """Recalculate and update the stored balance from transactions."""
        balance = CreditCardService.get_card_balance(card_id)
        db.execute("UPDATE credit_cards SET current_balance = ? WHERE id = ?", (balance, card_id))
        return balance

    @staticmethod
    def get_total_outstanding():
        """Get total outstanding across all cards."""
        res = db.execute("SELECT COALESCE(SUM(current_balance), 0) FROM credit_cards")
        return float(res.rows[0][0]) if res and res.rows else 0.0

    @staticmethod
    def get_upcoming_bills(days=15):
        """Get cards with closing dates (due dates) approaching."""
        today = datetime.now().date()
        cards = CreditCardService.get_cards()
        upcoming = []
        for _, row in cards.iterrows():
            bd = int(row['closing_date'] or 1)
            # Calculate next closing date
            now = datetime.now()
            try:
                next_bill = datetime(now.year, now.month, bd).date()
                if next_bill < today:
                    # Next month
                    if now.month == 12:
                        next_bill = datetime(now.year + 1, 1, bd).date()
                    else:
                        next_bill = datetime(now.year, now.month + 1, bd).date()
                days_left = (next_bill - today).days
                if 0 <= days_left <= days:
                    upcoming.append({
                        "id": row['id'], "name": row['name'], "bank": row['bank'],
                        "closing_date": bd, "days_left": days_left,
                        "balance": row['current_balance'], "limit": row['card_limit']
                    })
            except Exception:
                continue
        return sorted(upcoming, key=lambda x: x['days_left'])
    @staticmethod
    def add_emi(card_id, description, total_amount, monthly_amount, tenure, start_date):
        """Add an EMI and its payment schedule."""
        eid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO credit_card_emis (id, card_id, description, total_amount, monthly_amount, tenure, start_date, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (eid, card_id, description, total_amount, monthly_amount, tenure, start_date, 'active')
        )
        
        # Generate payments
        st_date = datetime.strptime(start_date, "%Y-%m-%d")
        for i in range(tenure):
            # Add months
            y = st_date.year + (st_date.month + i - 1) // 12
            m = (st_date.month + i - 1) % 12 + 1
            max_d = calendar.monthrange(y, m)[1]
            d = min(st_date.day, max_d)
            due_date = f"{y}-{m:02d}-{d:02d}"
            
            db.execute(
                "INSERT INTO credit_card_emi_payments (id, emi_id, due_date, amount, status) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), eid, due_date, monthly_amount, 'pending')
            )

    @staticmethod
    def get_card_emis(card_id):
        """Get active EMIs for a card."""
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
    def get_all_active_emis():
        """Get all active EMIs across all cards."""
        res = db.execute("SELECT id, monthly_amount FROM credit_card_emis WHERE status = 'active'")
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "Monthly"])
        return pd.DataFrame(columns=["id", "Monthly"])

    @staticmethod
    def get_emi_payments(emi_id):
        """Get payment schedule for an EMI."""
        res = db.execute("SELECT id, due_date, amount, status, paid_date FROM credit_card_emi_payments WHERE emi_id = ? ORDER BY due_date", (emi_id,))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "Date", "Amount", "Status", "Paid Date"])
        return pd.DataFrame(columns=["id", "Date", "Amount", "Status", "Paid Date"])

    @staticmethod
    def get_upcoming_emi_payments(days_ahead=30):
        """Get upcoming EMI payments across all cards."""
        res = db.execute("""
            SELECT p.id, e.description, p.amount, p.due_date, c.name as card_name
            FROM credit_card_emi_payments p
            JOIN credit_card_emis e ON p.emi_id = e.id
            JOIN credit_cards c ON e.card_id = c.id
            WHERE p.status = 'pending' AND p.due_date <= date('now', '+' || ? || ' days')
            ORDER BY p.due_date ASC
        """, (days_ahead,))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "Description", "Amount", "Due Date", "Card"])
        return pd.DataFrame(columns=["id", "Description", "Amount", "Due Date", "Card"])

    @staticmethod
    def delete_emi(emi_id):
        """Delete an EMI and its payments."""
        db.execute("DELETE FROM credit_card_emi_payments WHERE emi_id = ?", (emi_id,))
        db.execute("DELETE FROM credit_card_emis WHERE id = ?", (emi_id,))

    @staticmethod
    def mark_emi_paid(payment_id, paid_date=None):
        """Mark an EMI installment as paid."""
        if not paid_date:
            paid_date = str(datetime.now().date())
        db.execute("UPDATE credit_card_emi_payments SET status = 'paid', paid_date = ? WHERE id = ?", (paid_date, payment_id))
        
        # Check if all paid
        res = db.execute("SELECT emi_id FROM credit_card_emi_payments WHERE id = ?", (payment_id,))
        if res and res.rows:
            emi_id = res.rows[0][0]
            res_pend = db.execute("SELECT COUNT(*) FROM credit_card_emi_payments WHERE emi_id = ? AND status = 'pending'", (emi_id,))
            if res_pend and res_pend.rows and res_pend.rows[0][0] == 0:
                db.execute("UPDATE credit_card_emis SET status = 'completed' WHERE id = ?", (emi_id,))

    @staticmethod
    def get_card_total_outstanding(card_id):
        """Outstanding is the total DEBT (Positive number)."""
        # Standard balance (Balance is negative for debt)
        res_bal = db.execute("SELECT current_balance FROM credit_cards WHERE id = ?", (card_id,))
        bal = float(res_bal.rows[0][0]) if res_bal and res_bal.rows else 0.0
        
        # EMI remaining (Always positive)
        res_emi = db.execute("""
            SELECT COALESCE(SUM(p.amount), 0) 
            FROM credit_card_emi_payments p
            JOIN credit_card_emis e ON p.emi_id = e.id
            WHERE e.card_id = ? AND p.status = 'pending'
        """, (card_id,))
        emi_rem = float(res_emi.rows[0][0]) if res_emi and res_emi.rows else 0.0
        
        # Outstanding is what you owe (e.g. -13k balance -> 13k outstanding)
        # If balance is positive (overpaid), outstanding from transactions is 0
        txn_out = max(0, -bal)
        return txn_out + emi_rem

    @staticmethod
    def get_card_available_limit(card_id):
        """Available = min(Limit, Limit + Balance) - Remaining EMIs."""
        res = db.execute("SELECT card_limit, current_balance FROM credit_cards WHERE id = ?", (card_id,))
        if res and res.rows:
            limit, bal = res.rows[0]
            limit = limit or 0.0
            bal = bal or 0.0
            
            # EMI remaining
            res_emi = db.execute("""
                SELECT COALESCE(SUM(p.amount), 0) 
                FROM credit_card_emi_payments p
                JOIN credit_card_emis e ON p.emi_id = e.id
                WHERE e.card_id = ? AND p.status = 'pending'
            """, (card_id,))
            emi_rem = float(res_emi.rows[0][0]) if res_emi and res_emi.rows else 0.0
            
            # If balance is positive (surplus), treat it as 0 for Available calculation
            # unless the user specifically wants to track 'Overpayment' as extra limit.
            # The user said 'should not exceed the Limit Value'.
            effective_bal = min(0.0, bal)
            
            return limit + effective_bal - emi_rem
        return 0.0
