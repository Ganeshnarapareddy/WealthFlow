import libsql_client
import streamlit as st
import hashlib

# Use st.secrets to connect
url = st.secrets["TURSO_URL"].replace("libsql://", "https://")
token = st.secrets["TURSO_TOKEN"]
client = libsql_client.create_client_sync(url=url, auth_token=token)

print("Checking users table...")
res = client.execute("SELECT id, username, password_hash, role FROM users")
for row in res.rows:
    print(f"ID: {row[0]} | User: {row[1]} | Role: {row[3]}")
    if row[1] == 'admin':
        expected = hashlib.sha256("admin123".encode()).hexdigest()
        print(f"  Password Hash: {row[2]}")
        print(f"  Expected Hash: {expected}")
        print(f"  Match: {row[2] == expected}")

print("\nEnsuring admin user with admin123 exists...")
admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
client.execute("DELETE FROM users WHERE username = 'admin'")
client.execute(
    "INSERT INTO users (id, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
    ("admin", "admin", admin_hash, "admin", "2024-01-01 00:00")
)
print("Admin user recreated successfully.")
