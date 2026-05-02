from database import db
import hashlib

def audit_users():
    print("--- Database Audit ---")
    res = db.execute("SELECT id, username, password_hash FROM wf_users")
    if not res or not res.rows:
        print("No users found.")
        return

    SALT = "wealthflow_secure_2026"
    
    for row in res.rows:
        uid, uname, u_hash = row
        print(f"User: '{uname}'")
        
        # Check if username needs stripping
        if uname != uname.strip():
            print(f"  [FIX] Stripping username: '{uname}' -> '{uname.strip()}'")
            db.execute("UPDATE wf_users SET username = ? WHERE id = ?", (uname.strip(), uid))
            uname = uname.strip()

        # Check hash format (Try to guess if it's unsalted 'admin123' or '123456')
        admin_unsalted = hashlib.sha256("admin123".encode()).hexdigest()
        admin_salted = hashlib.sha256(("admin123" + SALT).encode()).hexdigest()
        
        test2_unsalted = hashlib.sha256("123456".encode()).hexdigest()
        test2_salted = hashlib.sha256(("123456" + SALT).encode()).hexdigest()

        if u_hash == admin_unsalted:
            print("  [INFO] User has OLD unsalted hash (admin123).")
        elif u_hash == admin_salted:
            print("  [INFO] User has NEW salted hash (admin123).")
        elif u_hash == test2_unsalted:
            print("  [INFO] User has OLD unsalted hash (123456).")
        elif u_hash == test2_salted:
            print("  [INFO] User has NEW salted hash (123456).")
        else:
            print(f"  [INFO] Hash is custom/unknown: {u_hash[:10]}...")

    print("--- Audit Complete ---")

if __name__ == "__main__":
    audit_users()
