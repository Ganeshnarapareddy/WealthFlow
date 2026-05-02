
import urllib.request
import json

URL = "https://finance-tracker-ganeshnarapareddy.aws-ap-south-1.turso.io/v2/pipeline"
TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc1NzAzOTgsImlkIjoiMDE5ZGRmNzItOWEwMS03MTQyLWI3NTAtNjNhNGZjMjEwMDY1IiwicmlkIjoiM2Y4ZjFiYmEtYWUyNi00NGI3LTk0MjMtZTYzMmQ0ZThlMjA0In0.3xjWCO-Su3JP5yCi4ArXKXDP59dn1lzsfOh70OHo0D7K6IExHhkpPsble8XepxEQtaHu2_f3D7ff1mzLD0QkBg"

def execute(sql):
    req_body = {"requests": [{"type": "execute", "stmt": {"sql": sql}}]}
    req = urllib.request.Request(URL, data=json.dumps(req_body).encode("utf-8"),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["results"][0]["response"]["result"]

def exhaustive_search():
    print("--- SEARCHING ALL TRANSACTIONS ---")
    res = execute("SELECT user_id, COUNT(*) FROM transactions GROUP BY user_id")
    if res["rows"]:
        for r in res["rows"]:
            print(f"Found {r[1]['value']} transactions for UID: {r[0]['value']}")
    else:
        print("No transactions found at all.")

if __name__ == "__main__":
    exhaustive_search()
