import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

# Cleanup duplicate test transactions
db.execute("DELETE FROM transactions WHERE description LIKE 'Auto: %'")
db.execute("DELETE FROM actioned_alerts")
print("Cleanup complete.")
