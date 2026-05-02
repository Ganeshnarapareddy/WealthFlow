
import urllib.request
import json

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

def rescue():
    ghost_id = "77d00438-a01d-4485-b0fc-b1ee9359892e"
    admin_id = "admin"
    tables = ['transactions', 'credit_card_transactions', 'accounts', 'assets', 'loans', 'budgets', 'subscriptions', 'goals', 'credit_cards', 'loan_payments', 'credit_card_emi_payments']
    
    print(f"Rescuing data from {ghost_id} to {admin_id}...")
    for t in tables:
        try:
            # Check if column exists (loan_payments might not have user_id, but loan_id links it)
            # Actually most tables have user_id
            if t in ['loan_payments', 'credit_card_emi_payments']:
                 continue # These are linked by foreign keys, but we'll check others
                 
            res = execute(f"UPDATE {t} SET user_id = ? WHERE user_id = ?", (admin_id, ghost_id))
            print(f"Table: {t} | Status: Success")
        except Exception as e:
            print(f"Table: {t} | Status: Failed ({e})")

if __name__ == "__main__":
    rescue()
