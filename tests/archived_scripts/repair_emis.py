import libsql_client
import toml

# Load database credentials
with open('.streamlit/secrets.toml', 'r') as f:
    secrets = toml.load(f)
    url = secrets['TURSO_URL'].replace('libsql://', 'https://')
    token = secrets['TURSO_TOKEN']
    client = libsql_client.create_client_sync(url=url, auth_token=token)

# 1. Fix EMI status
res = client.execute('UPDATE credit_card_emis SET status = "active" WHERE status IS NULL OR status = ""')
print(f'Updated {res.rows_affected} EMI records status')

# 2. Recalculate current_balance for each credit card
cards = client.execute('SELECT id, name FROM credit_cards').rows
for card in cards:
    card_id, card_name = card
    
    # Calculate balance: Sum of Payments - Sum of Expenses
    res_txn = client.execute("""
        SELECT COALESCE(SUM(CASE WHEN txn_type='payment' THEN amount ELSE 0 END), 0) - 
               COALESCE(SUM(CASE WHEN txn_type='expense' THEN amount ELSE 0 END), 0)
        FROM credit_card_transactions WHERE card_id = ?
    """, (card_id,)).rows[0][0]
    
    client.execute('UPDATE credit_cards SET current_balance = ? WHERE id = ?', (res_txn, card_id))
    print(f"Fixed balance for {card_name}: New Balance = {res_txn}")

print("Database repair complete!")
