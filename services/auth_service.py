import hashlib
import uuid
from datetime import datetime
from database import db

class AuthService:
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def login(username, password):
        """Verify credentials and return user dict if successful."""
        pwd_hash = AuthService.hash_password(password)
        res = db.execute(
            "SELECT id, username, role, email, currency FROM wf_users WHERE username = ? AND password_hash = ?",
            (username, pwd_hash)
        )
        if res and res.rows:
            row = res.rows[0]
            return {
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "email": row[3],
                "currency": row[4]
            }
        return None

    @staticmethod
    def signup(username, password, email=None):
        """Create a new user. Returns user_id or None if username exists."""
        # Check if exists
        res = db.execute("SELECT id FROM wf_users WHERE username = ?", (username,))
        if res and res.rows:
            return None
        
        uid = str(uuid.uuid4())
        pwd_hash = AuthService.hash_password(password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        db.execute(
            "INSERT INTO wf_users (id, username, password_hash, email, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, username, pwd_hash, email, 'user', now)
        )
        
        # Create default account for new user
        db.execute(
            "INSERT INTO accounts (id, user_id, account_name, balance, account_type) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), uid, "Main Account", 0.0, "Savings")
        )
        
        return uid

    @staticmethod
    def reset_password(username, new_password):
        """Update password for a user."""
        pwd_hash = AuthService.hash_password(new_password)
        db.execute("UPDATE wf_users SET password_hash = ? WHERE username = ?", (pwd_hash, username))

    @staticmethod
    def get_all_users():
        """Admin only: list all users."""
        res = db.execute("SELECT id, username, role, email, created_at FROM wf_users ORDER BY created_at DESC")
        if res and res.rows:
            return res.rows
        return []

    @staticmethod
    def update_user(user_id, username, role, password=None):
        """Admin only: update user details."""
        if password:
            pwd_hash = AuthService.hash_password(password)
            db.execute(
                "UPDATE wf_users SET username = ?, role = ?, password_hash = ? WHERE id = ?",
                (username, role, pwd_hash, user_id)
            )
        else:
            db.execute(
                "UPDATE wf_users SET username = ?, role = ? WHERE id = ?",
                (username, role, user_id)
            )

    @staticmethod
    def delete_user(user_id):
        """Admin only: delete user and their data."""
        if user_id == "admin": return False # Prevent self-deletion
        
        # Delete related data (cascading manually since no foreign keys with ON DELETE CASCADE)
        tables = ['transactions', 'accounts', 'assets', 'loans', 'budgets', 'subscriptions', 'credit_cards', 'goals']
        for table in tables:
            db.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
        
        # Finally delete user
        db.execute("DELETE FROM wf_users WHERE id = ?", (user_id,))
        return True
