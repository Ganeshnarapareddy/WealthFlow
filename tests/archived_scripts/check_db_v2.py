from database import db
import pandas as pd

res = db.execute("SELECT id, person_name, loan_type, status, due_date FROM loans")
if res and res.rows:
    df = pd.DataFrame(res.rows, columns=["id", "person_name", "loan_type", "status", "due_date"])
    print("Loans Summary:")
    print(df)
else:
    print("No loans found.")
