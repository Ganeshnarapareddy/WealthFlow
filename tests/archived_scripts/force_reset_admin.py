import hashlib
import libsql_client
import os

# Manual read of secrets
secrets = {}
with open(".streamlit/secrets.toml", "r") as f:
    for line in f:
        if "=" in line:
            k, v = line.split("=", 1)
            secrets[k.strip()] = v.strip().strip('"').strip("'")

url = secrets["TURSO_URL"].replace("libsql://", "https://")
token = secrets["TURSO_TOKEN"]
client = libsql_client.create_client_sync(url=url, auth_token=token)

admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
print(f"Resetting admin to hash: {admin_hash}")

client.execute("DELETE FROM users WHERE username = 'admin'")
client.execute(
    "INSERT INTO users (id, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
    ("admin", "admin", admin_hash, "admin", "2024-01-01 00:00")
)
print("Admin user RECREATED with default password 'admin123'.")
