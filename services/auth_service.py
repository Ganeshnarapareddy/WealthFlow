import hashlib
import uuid
from datetime import datetime
from database import db

class AuthService:
    @staticmethod
    def hash_password(password):
        # Using a fixed salt for now
        SALT = "wealthflow_secure_2026" 
        return hashlib.sha256((password + SALT).encode()).hexdigest()

    @staticmethod
    def generate_short_id():
        """Generate a random 5-digit numeric ID."""
        import random
        return random.randint(10000, 99999)

    @staticmethod
    def login(username, password):
        """Verify credentials and return user dict if successful (only for active users)."""
        pwd_hash = AuthService.hash_password(password)
        res = db.execute(
            "SELECT id, username, role, email, currency, phone, short_id, status FROM wf_users WHERE username = ? AND password_hash = ? AND status = 'active'",
            (username, pwd_hash)
        )
        if res and res.rows:
            row = res.rows[0]
            return {
                "id": row[0], "username": row[1], "role": row[2], 
                "email": row[3], "currency": row[4], "phone": row[5],
                "short_id": row[6], "status": row[7]
            }
        return None

    @staticmethod
    def signup(username, password, email=None, phone=None):
        """Create a new user or reclaim an archived one."""
        if not email and not phone:
            return "Email or Phone is mandatory."
            
        # Check if an active user exists
        res = db.execute("SELECT id FROM wf_users WHERE (username = ? OR (email = ? AND email != '') OR (phone = ? AND phone != '')) AND status = 'active'", (username, email, phone))
        if res and res.rows:
            return "User with this name/contact already exists."
        
        # Check for archived account to reclaim
        res_arch = db.execute("SELECT id FROM wf_users WHERE ((email = ? AND email != '') OR (phone = ? AND phone != '')) AND status = 'archived'", (email, phone))
        if res_arch and res_arch.rows:
            uid = res_arch.rows[0][0]
            pwd_hash = AuthService.hash_password(password)
            db.execute("UPDATE wf_users SET status = 'active', deleted_at = NULL, username = ?, password_hash = ? WHERE id = ?", (username, pwd_hash, uid))
            return uid

        uid = str(uuid.uuid4())
        pwd_hash = AuthService.hash_password(password)
        sid = AuthService.generate_short_id()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        db.execute(
            "INSERT INTO wf_users (id, username, password_hash, email, phone, role, created_at, short_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')",
            (uid, username, pwd_hash, email, phone, 'user', now, sid)
        )
        
        # Create default account for new user
        db.execute(
            "INSERT INTO accounts (id, user_id, account_name, balance, account_type) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), uid, "Main Account", 0.0, "Savings")
        )
        return uid

    @staticmethod
    def update_username(user_id, new_username):
        """Allow users/admin to change username."""
        # Check if exists
        res = db.execute("SELECT id FROM wf_users WHERE username = ? AND id != ?", (new_username, user_id))
        if res and res.rows: return False
        db.execute("UPDATE wf_users SET username = ? WHERE id = ?", (new_username, user_id))
        return True

    @staticmethod
    def update_profile(user_id, username, email, phone):
        """Update username, email, and phone in one go."""
        # Check if new username is taken by another user
        res = db.execute("SELECT id FROM wf_users WHERE username = ? AND id != ?", (username, user_id))
        if res and res.rows: return "Username already taken"
        
        db.execute("UPDATE wf_users SET username = ?, email = ?, phone = ? WHERE id = ?", (username, email, phone, user_id))
        return True

    @staticmethod
    def update_password(user_id, new_password):
        """Securely update a user's password."""
        pwd_hash = AuthService.hash_password(new_password)
        db.execute("UPDATE wf_users SET password_hash = ? WHERE id = ?", (pwd_hash, user_id))
        return True

    @staticmethod
    def unarchive_user(user_id):
        """Restore an archived user to active status."""
        db.execute("UPDATE wf_users SET status = 'active', deleted_at = NULL WHERE id = ?", (user_id,))
        return True

    @staticmethod
    def update_contact_info(user_id, email, phone):
        """Update a user's email and phone number."""
        db.execute("UPDATE wf_users SET email = ?, phone = ? WHERE id = ?", (email, phone, user_id))
        return True

    @staticmethod
    def delete_user(user_id):
        """Soft-delete (Archive) user and their data."""
        if user_id == "admin": return False 
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        # Just mark as archived and set deletion date
        db.execute("UPDATE wf_users SET status = 'archived', deleted_at = ? WHERE id = ?", (now, user_id))
        return True

    @staticmethod
    def get_all_users():
        """List all users (including archived)."""
        res = db.execute("SELECT id, username, role, email, phone, short_id, status, created_at FROM wf_users ORDER BY created_at DESC")
        if res and res.rows:
            return res.rows
        return []
