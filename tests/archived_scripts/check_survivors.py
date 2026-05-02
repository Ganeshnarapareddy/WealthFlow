
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

def check_survivors():
    print("--- LOANS ---")
    res = execute("SELECT id, person_name, user_id FROM loans")
    for r in res["rows"]:
        print(f"Loan: {r[1]['value']} | UID: {r[2]['value']}")
        
    print("\n--- CREDIT CARDS ---")
    res = execute("SELECT id, card_name, user_id FROM credit_cards")
    for r in res["rows"]:
        print(f"Card: {r[1]['value']} | UID: {r[2]['value']}")

if __name__ == "__main__":
    check_survivors()
