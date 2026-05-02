
import urllib.request
import json
import random

URL = "https://finance-tracker-ganeshnarapareddy.aws-ap-south-1.turso.io/v2/pipeline"
TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc1NzAzOTgsImlkIjoiMDE5ZGRmNzItOWEwMS03MTQyLWI3NTAtNjNhNGZjMjEwMDY1IiwicmlkIjoiM2Y4ZjFiYmEtYWUyNi00NGI3LTk0MjMtZTYzMmQ0ZThlMjA0In0.3xjWCO-Su3JP5yCi4ArXKXDP59dn1lzsfOh70OHo0D7K6IExHhkpPsble8XepxEQtaHu2_f3D7ff1mzLD0QkBg"

def execute(sql, params=None):
    stmt = {"sql": sql}
    if params:
        stmt["args"] = [{"type": "text", "value": str(p)} for p in params]
    req_body = {"requests": [{"type": "execute", "stmt": stmt}]}
    req = urllib.request.Request(URL, data=json.dumps(req_body).encode("utf-8"),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["results"][0]["response"]["result"]

if __name__ == "__main__":
    sid = random.randint(10000, 99999)
    execute("UPDATE wf_users SET status = 'active', short_id = ? WHERE username = 'admin'", (sid,))
    print(f"Admin migrated successfully with Short ID: {sid}")
