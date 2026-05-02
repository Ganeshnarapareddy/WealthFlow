import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from datetime import datetime

print("Actioned Alerts Table Content:")
res = db.execute("SELECT * FROM actioned_alerts")
if res and res.rows:
    for row in res.rows:
        print(row)
else:
    print("Empty table")

my = datetime.now().strftime("%m-%Y")
print(f"\nCurrent Month-Year: {my}")

res = db.execute("SELECT COUNT(*) FROM actioned_alerts WHERE month_year = ?", (my,))
print(f"Alerts for this month: {res.rows[0][0] if res and res.rows else 0}")
