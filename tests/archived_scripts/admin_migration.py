
from database import db
import random

def migrate():
    # Give admin a short ID and active status
    sid = random.randint(10000, 99999)
    db.execute("UPDATE wf_users SET status = 'active', short_id = ? WHERE username = 'admin'", (sid,))
    print(f"Admin migrated with ID: {sid}")

if __name__ == "__main__":
    migrate()
