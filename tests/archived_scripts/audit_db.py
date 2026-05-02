
from database import db

def audit():
    print("--- CATEGORIES ---")
    res_cats = db.execute("SELECT * FROM categories")
    if res_cats and res_cats.rows:
        for r in res_cats.rows:
            print(r)
    
    print("\n--- RECENT TRANSACTIONS ---")
    res_txns = db.execute("SELECT id, date, description, amount, category_id, type, user_id FROM transactions ORDER BY date DESC LIMIT 10")
    if res_txns and res_txns.rows:
        for r in res_txns.rows:
            print(r)

    print("\n--- RECENT CREDIT CARD TRANSACTIONS ---")
    res_cc = db.execute("SELECT id, date, description, amount, txn_type, user_id FROM credit_card_transactions ORDER BY date DESC LIMIT 10")
    if res_cc and res_cc.rows:
        for r in res_cc.rows:
            print(r)

if __name__ == "__main__":
    audit()
