from database import db
db.execute("UPDATE wf_users SET short_id = '00001' WHERE username = 'admin'")
print("Admin ID set to 00001")
