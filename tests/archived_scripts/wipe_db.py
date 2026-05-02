import libsql_client
import streamlit as st

def wipe_data():
    url = st.secrets["TURSO_URL"].replace("libsql://", "https://")
    token = st.secrets["TURSO_TOKEN"]
    client = libsql_client.create_client_sync(url=url, auth_token=token)
    
    print("--- Wiping All Financial Data ---")
    
    # List of tables to clear completely
    tables_to_clear = [
        "transactions",
        "subscriptions",
        "goals",
        "assets",
        "budgets"
    ]
    
    for table in tables_to_clear:
        try:
            client.execute(f"DELETE FROM {table}")
            print(f"Cleared table: {table}")
        except Exception as e:
            print(f"Error clearing {table}: {e}")
            
    # Reset account balance
    try:
        client.execute("UPDATE accounts SET balance = 0.0")
        print("Reset account balance to 0")
    except Exception as e:
        print(f"Error resetting accounts: {e}")
        
    print("\n✅ Database is now clean and ready for fresh entries!")

if __name__ == "__main__":
    # Mock streamlit secrets for local script execution
    import toml
    with open(".streamlit/secrets.toml", "r") as f:
        secrets = toml.load(f)
        st.secrets = secrets
        
    wipe_data()
