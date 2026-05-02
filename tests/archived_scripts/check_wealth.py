from database import db
import pandas as pd

def check_wealth():
    res_acc = db.execute("SELECT * FROM accounts")
    print("Accounts:")
    if res_acc and res_acc.rows:
        print(pd.DataFrame(res_acc.rows, columns=res_acc.columns))
    else:
        print("Empty")

    res_ast = db.execute("SELECT * FROM assets")
    print("\nAssets:")
    if res_ast and res_ast.rows:
        print(pd.DataFrame(res_ast.rows, columns=res_ast.columns))
    else:
        print("Empty")

    res_txn = db.execute("SELECT COUNT(*) FROM transactions")
    print(f"\nTransactions count: {res_txn.rows[0][0]}")

if __name__ == "__main__":
    check_wealth()
