
from database import db

def audit():
    print("--- GLOBAL AUDIT ---")
    tables = ['transactions', 'credit_card_transactions']
    for t in tables:
        print(f"\nTable: {t}")
        res = db.execute(f"SELECT id, amount, user_id, date, description FROM {t} WHERE amount > 1000000")
        if res and res.rows:
            for r in res.rows:
                print(r)
        else:
            print("No million-plus transactions found.")

if __name__ == "__main__":
    audit()
