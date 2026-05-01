import pandas as pd
import uuid
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
    def add_transaction(card_id, amount, description, txn_type, txn_date=None):
        """Add a credit card transaction. type: 'expense' or 'payment'."""
        if txn_date is None:
            txn_date = str(datetime.now().date())
        tid = str(uuid.uuid4())
        db.execute(
            "INSERT INTO credit_card_transactions (id, card_id, amount, description, date, txn_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (tid, card_id, amount, description, txn_date, txn_type)
        )
        # Update card balance (Expenses reduce balance, Payments increase it)
        adj = -amount if txn_type == "expense" else amount
        db.execute(
            "UPDATE credit_cards SET current_balance = current_balance + ? WHERE id = ?",
            (adj, card_id)
        )

    @staticmethod
    def get_card_transactions(card_id, year=None, month=None):
        """Get transactions for a card, optionally filtered by year/month."""
        query = """
            SELECT id, date, description, amount, txn_type
            FROM credit_card_transactions
            WHERE card_id = ?
        """
        params = [card_id]
        if year and month:
            query += " AND date LIKE ?"
            params.append(f"{year}-{month:02d}%")
        elif year:
            query += " AND date LIKE ?"
            params.append(f"{year}%")
        query += " ORDER BY date DESC"
        res = db.execute(query, tuple(params))
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "date", "description", "amount", "txn_type"])
        return pd.DataFrame(columns=["id", "date", "description", "amount", "txn_type"])

    @staticmethod
    def get_card_balance(card_id):
        """Calculate current balance: sum(expenses) - sum(payments)."""
        res = db.execute(
            "SELECT COALESCE(SUM(CASE WHEN txn_type='expense' THEN amount ELSE 0 END), 0) - "
            "COALESCE(SUM(CASE WHEN txn_type='payment' THEN amount ELSE 0 END), 0) "
            "FROM credit_card_transactions WHERE card_id = ?",
            (card_id,)
        )
        if res and res.rows:
            return float(res.rows[0][0] or 0)
        return 0.0

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
