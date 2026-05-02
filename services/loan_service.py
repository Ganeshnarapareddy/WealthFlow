import pandas as pd
import uuid
import calendar
from datetime import datetime, timedelta, date
from database import db


class LoanService:
    """Track loans given/taken, EMI, due dates."""

    @staticmethod
    def get_loans(loan_type=None):
        """Get all loans, optionally filtered by type ('given' or 'taken')."""
        query = """
            SELECT id, person_name, amount, loan_type, interest_rate,
                   start_date, due_date, emi_amount, emi_active,
                   tenure, emi_start_date,
                   status, remaining_amount, notes,
                   (SELECT COUNT(*) FROM loan_payments WHERE loan_id = loans.id AND status = 'pending') as remaining_tenure
            FROM loans
        """
        params = ()
        if loan_type:
            query += " WHERE loan_type = ?"
            params = (loan_type,)
        query += " ORDER BY due_date ASC"
        res = db.execute(query, params)
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=[
                "id", "person_name", "amount", "loan_type", "interest_rate",
                "start_date", "due_date", "emi_amount", "emi_active",
                "tenure", "emi_start_date",
                "status", "remaining_amount", "notes", "remaining_tenure"
            ])
        return pd.DataFrame(columns=[
            "id", "person_name", "amount", "loan_type", "interest_rate",
            "start_date", "due_date", "emi_amount", "emi_active",
            "tenure", "emi_start_date",
            "status", "remaining_amount", "notes", "remaining_tenure"
        ])
    
    @staticmethod
    def get_active_emi_stats():
        """Get stats for all active loan EMIs."""
        res = db.execute("SELECT id, emi_amount FROM loans WHERE emi_active = 1 AND status != 'paid'")
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "Monthly"])
        return pd.DataFrame(columns=["id", "Monthly"])
    @staticmethod
    def get_loan_by_id(loan_id):
        """Get a single loan by ID."""
        res = db.execute(
            "SELECT id, person_name, amount, loan_type, interest_rate, "
            "start_date, due_date, emi_amount, emi_active, tenure, emi_start_date, "
            "status, remaining_amount, notes "
            "FROM loans WHERE id = ?",
            (loan_id,)
        )
        if res and res.rows:
            return res.rows[0]
        return None

    @staticmethod
    def add_loan(person_name, amount, loan_type, interest_rate=0,
                 start_date=None, due_date=None, emi_amount=0, emi_active=False, 
                 tenure=0, emi_start_date=None, notes=""):
        """Add a new loan and generate its payment schedule."""
        lid = str(uuid.uuid4())
        sd = str(start_date) if start_date else str(datetime.now().date())
        dd = str(due_date) if due_date else ""
        esd = str(emi_start_date) if emi_start_date else sd
        
        db.execute(
            "INSERT INTO loans "
            "(id, person_name, amount, loan_type, interest_rate, "
            "start_date, due_date, emi_amount, emi_active, tenure, emi_start_date, "
            "status, remaining_amount, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)",
            (lid, person_name, amount, loan_type, interest_rate,
             sd, dd, emi_amount, 1 if emi_active else 0, tenure, esd, amount, notes)
        )
        
        # Generate Schedule
        LoanService._generate_schedule(lid, amount, emi_amount, emi_active, tenure, esd, dd)

    @staticmethod
    def _generate_schedule(loan_id, total_amount, emi_amount, emi_active, tenure, emi_start_date, due_date):
        """Internal helper to create installment entries."""
        if emi_active and tenure > 0:
            start_dt = datetime.strptime(emi_start_date, "%Y-%m-%d")
            for i in range(tenure):
                # Add i months
                month = (start_dt.month + i - 1) % 12 + 1
                year = start_dt.year + (start_dt.month + i - 1) // 12
                # Clamp day to max available in month
                last_day = calendar.monthrange(year, month)[1]
                day = min(start_dt.day, last_day)
                inst_date = date(year, month, day).strftime("%Y-%m-%d")
                
                db.execute(
                    "INSERT INTO loan_payments (id, loan_id, due_date, amount, status) VALUES (?, ?, ?, ?, 'pending')",
                    (str(uuid.uuid4()), loan_id, inst_date, emi_amount)
                )
        else:
            # Single payment
            db.execute(
                "INSERT INTO loan_payments (id, loan_id, due_date, amount, status) VALUES (?, ?, ?, ?, 'pending')",
                (str(uuid.uuid4()), loan_id, due_date, total_amount)
            )

    @staticmethod
    def get_loan_payments(loan_id):
        """Get all payments/installments for a loan."""
        res = db.execute(
            "SELECT id, due_date, amount, status, paid_date FROM loan_payments WHERE loan_id = ? ORDER BY due_date ASC",
            (loan_id,)
        )
        if res and res.rows:
            return pd.DataFrame(res.rows, columns=["id", "due_date", "amount", "status", "paid_date"])
        return pd.DataFrame(columns=["id", "due_date", "amount", "status", "paid_date"])

    @staticmethod
    def toggle_payment_status(payment_id, current_status):
        """Mark a payment as paid/pending and update loan remaining_amount."""
        new_status = "paid" if current_status == "pending" else "pending"
        paid_date = datetime.now().strftime("%Y-%m-%d") if new_status == "paid" else None
        
        # Update payment
        db.execute("UPDATE loan_payments SET status = ?, paid_date = ? WHERE id = ?", (new_status, paid_date, payment_id))
        
        # Get loan_id for this payment
        res = db.execute("SELECT loan_id FROM loan_payments WHERE id = ?", (payment_id,))
        if res and res.rows:
            loan_id = res.rows[0][0]
            LoanService.recalculate_remaining_amount(loan_id)

    @staticmethod
    def recalculate_remaining_amount(loan_id):
        """Update the remaining_amount and status based on payments."""
        res_loan = db.execute("SELECT amount FROM loans WHERE id = ?", (loan_id,))
        if not res_loan or not res_loan.rows: return
        total = res_loan.rows[0][0]
        
        # Get total paid
        res_paid = db.execute("SELECT SUM(amount) FROM loan_payments WHERE loan_id = ? AND status = 'paid'", (loan_id,))
        paid = float(res_paid.rows[0][0] or 0)
        
        # Check if ALL installments are paid (important if emi_amt is 0)
        res_pending = db.execute("SELECT COUNT(*) FROM loan_payments WHERE loan_id = ? AND status = 'pending'", (loan_id,))
        pending_count = int(res_pending.rows[0][0] or 0)
        
        remaining = max(0, total - paid)
        status = "paid" if pending_count == 0 else "pending"
        db.execute("UPDATE loans SET remaining_amount = ?, status = ? WHERE id = ?", (remaining, status, loan_id))

    @staticmethod
    def record_payment(loan_id, payment_amount, payment_date=None):
        """Record a manual payment against a loan."""
        if payment_date is None:
            payment_date = str(datetime.now().date())
        loan = LoanService.get_loan_by_id(loan_id)
        if loan:
            # Index 12 is remaining_amount
            new_remaining = max(0, float(loan[12]) - payment_amount)
            status = "paid" if new_remaining == 0 else "pending"
            db.execute(
                "UPDATE loans SET remaining_amount = ?, status = ? WHERE id = ?",
                (new_remaining, status, loan_id)
            )

    @staticmethod
    def update_loan_status(loan_id, status):
        """Update loan status ('pending', 'paid', 'overdue')."""
        db.execute("UPDATE loans SET status = ? WHERE id = ?", (status, loan_id))

    @staticmethod
    def delete_loan(loan_id):
        """Delete a loan and its payment schedule."""
        db.execute("DELETE FROM loan_payments WHERE loan_id = ?", (loan_id,))
        db.execute("DELETE FROM loans WHERE id = ?", (loan_id,))

    @staticmethod
    def update_loan(loan_id, person_name, amount, interest_rate, start_date, due_date, 
                    emi_amount, emi_active, tenure, emi_start_date):
        """Update loan details and refresh schedule."""
        db.execute(
            "UPDATE loans SET person_name = ?, amount = ?, interest_rate = ?, "
            "start_date = ?, due_date = ?, emi_amount = ?, emi_active = ?, "
            "tenure = ?, emi_start_date = ? "
            "WHERE id = ?",
            (person_name, amount, interest_rate, str(start_date), str(due_date),
             emi_amount, 1 if emi_active else 0, tenure, str(emi_start_date), loan_id)
        )
        # Note: In a production app, we'd handle existing payments carefully.
        # Here we'll clear pending ones and re-generate if the schedule changed significantly.
        # But for simplicity, we'll just recalculate remaining.
        LoanService.recalculate_remaining_amount(loan_id)

    @staticmethod
    def get_upcoming_dues(days=30):
        """Get loans with due dates within X days."""
        today = datetime.now().date()
        cutoff = today + timedelta(days=days)
        res = db.execute(
            "SELECT id, person_name, amount, loan_type, due_date, remaining_amount "
            "FROM loans WHERE due_date != '' AND status = 'pending' "
            "ORDER BY due_date ASC"
        )
        if not res or not res.rows:
            return []
        upcoming = []
        for row in res.rows:
            try:
                due = datetime.strptime(row[4], "%Y-%m-%d").date()
                days_left = (due - today).days
                if 0 <= days_left <= days:
                    upcoming.append({
                        "id": row[0], "person_name": row[1], "amount": row[2],
                        "loan_type": row[3], "due_date": row[4],
                        "remaining": row[5], "days_left": days_left
                    })
            except Exception:
                continue
        return upcoming

    @staticmethod
    def update_overdue_status():
        """Update status to 'overdue' for past-due loans."""
        today = str(datetime.now().date())
        db.execute(
            "UPDATE loans SET status = 'overdue' "
            "WHERE due_date != '' AND due_date < ? AND status = 'pending'",
            (today,)
        )
