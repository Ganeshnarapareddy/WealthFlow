import hashlib
import uuid
from datetime import datetime, timedelta
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
        # Try with current salted format
        pwd_hash_salted = AuthService.hash_password(password)
        res = db.execute(
            "SELECT id, username, role, email, currency, phone, short_id, status FROM wf_users WHERE username = ? AND password_hash = ? AND status = 'active'",
            (username, pwd_hash_salted)
        )
        if res and res.rows:
            row = res.rows[0]
            return {
                "id": row[0], "username": row[1], "role": row[2], 
                "email": row[3], "currency": row[4], "phone": row[5],
                "short_id": row[6], "status": row[7]
            }
            
        # Migration path: Try with old unsalted format
        pwd_hash_unsalted = hashlib.sha256(password.encode()).hexdigest()
        res_old = db.execute(
            "SELECT id, username, role, email, currency, phone, short_id, status FROM wf_users WHERE username = ? AND password_hash = ? AND status = 'active'",
            (username, pwd_hash_unsalted)
        )
        if res_old and res_old.rows:
            row = res_old.rows[0]
            # Upgrade user to salted format permanently
            db.execute("UPDATE wf_users SET password_hash = ? WHERE id = ?", (pwd_hash_salted, row[0]))
            return {
                "id": row[0], "username": row[1], "role": row[2], 
                "email": row[3], "currency": row[4], "phone": row[5],
                "short_id": row[6], "status": row[7]
            }
            
        return None

    @staticmethod
    def signup(username, password, email=None, phone=None, role="user"):
        """Create a new user or reclaim an archived one."""
        username = (username or "").strip()
        email = (email or "").strip() or None
        phone = (phone or "").strip() or None
        role = (role or "user").strip().lower()
        if role not in ("admin", "user"):
            role = "user"

        if not username:
            return "Username is required."
        if not password or len(password) < 6:
            return "Password must be at least 6 characters."
        if not email and not phone:
            return "Email or Phone is mandatory."

        # Check if username already exists case-insensitively across all users
        res_u = db.execute(
            "SELECT id FROM wf_users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))",
            (username,)
        )
        if res_u and res_u.rows:
            return "Username already present."

        # Check if email already exists among active users
        if email:
            res_e = db.execute(
                "SELECT id FROM wf_users WHERE LOWER(TRIM(email)) = LOWER(TRIM(?)) AND status = 'active'",
                (email,)
            )
            if res_e and res_e.rows:
                return "Email already present."

        # Check if phone already exists among active users
        if phone:
            res_p = db.execute(
                "SELECT id FROM wf_users WHERE TRIM(phone) = TRIM(?) AND status = 'active'",
                (phone,)
            )
            if res_p and res_p.rows:
                return "Phone number already present."

        # Check for archived account to reclaim
        res_arch = None
        if email or phone:
            res_arch = db.execute(
                "SELECT id FROM wf_users WHERE ((email = ? AND email != '') OR (phone = ? AND phone != '')) AND status = 'archived'",
                (email or "", phone or "")
            )
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
            (uid, username, pwd_hash, email, phone, role, now, sid)
        )

        # Create default account for new user
        db.execute(
            "INSERT INTO accounts (id, user_id, account_name, balance, account_type) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), uid, "Main Account", 0.0, "Savings")
        )
        return uid

    @staticmethod
    def update_username(user_id, new_username):
        """Allow users/admin to change username with case-insensitive uniqueness check."""
        new_username = (new_username or "").strip()
        if not new_username:
            return "Username cannot be empty."
        res = db.execute(
            "SELECT id FROM wf_users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?)) AND id != ?",
            (new_username, user_id)
        )
        if res and res.rows:
            return "Username already present."
        db.execute("UPDATE wf_users SET username = ? WHERE id = ?", (new_username, user_id))
        return True

    @staticmethod
    def update_profile(user_id, username, email, phone):
        """Update username, email, and phone with case-insensitive uniqueness checks."""
        username = (username or "").strip()
        email = (email or "").strip()
        phone = (phone or "").strip()

        if not username:
            return "Username cannot be empty."

        # Check if new username is taken by another user (case-insensitive)
        res_u = db.execute(
            "SELECT id FROM wf_users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?)) AND id != ?",
            (username, user_id)
        )
        if res_u and res_u.rows:
            return "Username already present."

        # Check if new email is taken by another active user
        if email:
            res_e = db.execute(
                "SELECT id FROM wf_users WHERE LOWER(TRIM(email)) = LOWER(TRIM(?)) AND id != ? AND status = 'active'",
                (email, user_id)
            )
            if res_e and res_e.rows:
                return "Email already present."

        # Check if new phone is taken by another active user
        if phone:
            res_p = db.execute(
                "SELECT id FROM wf_users WHERE TRIM(phone) = TRIM(?) AND id != ? AND status = 'active'",
                (phone, user_id)
            )
            if res_p and res_p.rows:
                return "Phone number already present."

        db.execute("UPDATE wf_users SET username = ?, email = ?, phone = ? WHERE id = ?", (username, email or None, phone or None, user_id))
        return True

    @staticmethod
    def update_password(user_id, new_password):
        """Securely update a user's password."""
        pwd_hash = AuthService.hash_password(new_password)
        db.execute("UPDATE wf_users SET password_hash = ? WHERE id = ?", (pwd_hash, user_id))
        return True

    @staticmethod
    def update_role(user_id, role):
        """Update a user's role ('admin' or 'user')."""
        role = (role or "user").strip().lower()
        if role not in ("admin", "user"):
            return "Invalid role."
        db.execute("UPDATE wf_users SET role = ? WHERE id = ?", (role, user_id))
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
    def purge_expired_archived_users(retention_days=10):
        """Permanently delete archived users whose deletion date is older than retention_days (default 10 days), along with all their data."""
        try:
            cutoff = (datetime.now() - timedelta(days=retention_days)).strftime("%Y-%m-%d %H:%M")
            res = db.execute(
                "SELECT id FROM wf_users WHERE status = 'archived' AND deleted_at IS NOT NULL AND deleted_at != '' AND deleted_at <= ? AND id != 'admin'",
                (cutoff,)
            )
            if not res or not res.rows:
                return 0

            purged_count = 0
            for row in res.rows:
                target_uid = row[0]
                # Cascade cleanup across all user-scoped tables
                tables = [
                    ("actioned_alerts", "user_id"),
                    ("assets", "user_id"),
                    ("budgets", "user_id"),
                    ("goals", "user_id"),
                    ("loans", "user_id"),
                    ("settings", "user_id"),
                    ("subscriptions", "user_id"),
                    ("transactions", "user_id"),
                    ("trips", "user_id"),
                    ("user_sessions", "user_id"),
                    ("accounts", "user_id"),
                    ("credit_cards", "user_id"),
                ]
                for tbl, col in tables:
                    try:
                        db.execute(f"DELETE FROM {tbl} WHERE {col} = ?", (target_uid,))
                    except Exception:
                        pass
                
                # Delete user record from wf_users
                db.execute("DELETE FROM wf_users WHERE id = ? AND id != 'admin'", (target_uid,))
                purged_count += 1

            return purged_count
        except Exception:
            return 0

    @staticmethod
    def get_all_users():
        """List all users (including archived), automatically purging archived accounts past retention period."""
        AuthService.purge_expired_archived_users(retention_days=10)
        res = db.execute("SELECT id, username, role, email, phone, short_id, status, created_at FROM wf_users ORDER BY (CASE WHEN role = 'admin' THEN 0 ELSE 1 END), created_at DESC")
        if res and res.rows:
            return res.rows
        return []

    @staticmethod
    def create_session(user_id):
        """Generate a persistent session token for a user (Supports Multi-device)."""
        token = str(uuid.uuid4())
        expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute(
            "INSERT INTO user_sessions (id, user_id, token, expiry, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, token, expiry, now)
        )
        return token

    @staticmethod
    def validate_session(token):
        """Check if a session token is valid and not expired."""
        if not token: return None
        res = db.execute(
            "SELECT u.id, u.username, u.role, u.email, u.currency, u.phone, u.short_id, u.status, s.expiry "
            "FROM wf_users u JOIN user_sessions s ON u.id = s.user_id "
            "WHERE s.token = ? AND u.status = 'active'",
            (token,)
        )
        if res and res.rows:
            row = res.rows[0]
            try:
                expiry = datetime.strptime(row[8], "%Y-%m-%d %H:%M")
                if expiry > datetime.now():
                    return {
                        "id": row[0], "username": row[1], "role": row[2], 
                        "email": row[3], "currency": row[4], "phone": row[5],
                        "short_id": row[6], "status": row[7]
                    }
                else:
                    # Cleanup expired session
                    db.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
            except: pass
        return None

    @staticmethod
    def clear_session(token):
        """Clear a specific session token (on logout)."""
        if not token: return
        db.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
