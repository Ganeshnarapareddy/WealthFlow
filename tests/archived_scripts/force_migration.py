
import urllib.request
import json

URL = "https://finance-tracker-ganeshnarapareddy.aws-ap-south-1.turso.io/v2/pipeline"
TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc1NzAzOTgsImlkIjoiMDE5ZGRmNzItOWEwMS03MTQyLWI3NTAtNjNhNGZjMjEwMDY1IiwicmlkIjoiM2Y4ZjFiYmEtYWUyNi00NGI3LTk0MjMtZTYzMmQ0ZThlMjA0In0.3xjWCO-Su3JP5yCi4ArXKXDP59dn1lzsfOh70OHo0D7K6IExHhkpPsble8XepxEQtaHu2_f3D7ff1mzLD0QkBg"

def execute(sql):
    req_body = {"requests": [{"type": "execute", "stmt": {"sql": sql}}]}
    req = urllib.request.Request(URL, data=json.dumps(req_body).encode("utf-8"),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error executing {sql}: {e}")
        return None

if __name__ == "__main__":
    commands = [
        "ALTER TABLE wf_users ADD COLUMN phone TEXT",
        "ALTER TABLE wf_users ADD COLUMN short_id INTEGER",
        "ALTER TABLE wf_users ADD COLUMN status TEXT DEFAULT 'active'",
        "ALTER TABLE wf_users ADD COLUMN deleted_at TEXT"
    ]
    for cmd in commands:
        print(f"Running: {cmd}")
        execute(cmd)
    print("Migration forced successfully.")
