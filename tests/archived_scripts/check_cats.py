import sys
import os
sys.path.append(os.getcwd())
from database import db

res = db.execute("SELECT DISTINCT type FROM categories")
print("Distinct types in DB:", res.rows if res else "None")

res = db.execute("SELECT id, name, type FROM categories")
if res:
    for row in res.rows:
        print(row)
else:
    print("No categories found.")
