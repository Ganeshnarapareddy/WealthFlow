from database import db
import hashlib

res = db.execute("SELECT username, password_hash FROM users WHERE username = 'admin'")
if res and res.rows:
    user, pwd = res.rows[0]
    expected = hashlib.sha256("admin123".encode()).hexdigest()
    print(f"User: {user}")
    print(f"Hash in DB: {pwd}")
    print(f"Expected:  {expected}")
    print(f"Match: {pwd == expected}")
else:
    print("Admin user not found in database.")
