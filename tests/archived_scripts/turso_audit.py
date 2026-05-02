
import urllib.request
import json

URL = "https://finance-tracker-ganeshnarapareddy.aws-ap-south-1.turso.io/v2/pipeline"
TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc1NzAzOTgsImlkIjoiMDE5ZGRmNzItOWEwMS03MTQyLWI3NTAtNjNhNGZjMjEwMDY1IiwicmlkIjoiM2Y4ZjFiYmEtYWUyNi00NGI3LTk0MjMtZTYzMmQ0ZThlMjA0In0.3xjWCO-Su3JP5yCi4ArXKXDP59dn1lzsfOh70OHo0D7K6IExHhkpPsble8XepxEQtaHu2_f3D7ff1mzLD0QkBg"

def execute(sql):
    req_body = {
        "requests": [
            {"type": "execute", "stmt": {"sql": sql}}
        ]
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(req_body).encode("utf-8"),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["results"][0]["response"]["result"]

def audit():
    print("--- USERS ---")
    users = execute("SELECT id, username FROM wf_users")
    user_ids = []
    for r in users["rows"]:
        uid = r[0]["value"]
        uname = r[1]["value"]
        user_ids.append(uid)
        print(f"User: {uname} (ID: {uid})")
    
    print("\n--- DATA CHECK ---")
    tables = ['transactions', 'credit_card_transactions']
    for t in tables:
        # Check for user_ids not in wf_users
        q = f"SELECT user_id, COUNT(*) FROM {t} GROUP BY user_id"
        res = execute(q)
        print(f"Table: {t}")
        for r in res["rows"]:
            uid = r[0]["value"]
            count = r[1]["value"]
            status = "VALID" if uid in user_ids or uid == 'admin' else "ORPHAN/STOLEN"
            print(f"  UID: {uid} | Count: {count} | Status: {status}")

if __name__ == "__main__":
    audit()
