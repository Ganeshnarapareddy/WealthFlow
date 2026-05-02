import libsql_client

def test_db():
    url = "https://finance-tracker-ganeshnarapareddy.aws-ap-south-1.turso.io"
    token = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc1NzAzOTgsImlkIjoiMDE5ZGRmNzItOWEwMS03MTQyLWI3NTAtNjNhNGZjMjEwMDY1IiwicmlkIjoiM2Y4ZjFiYmEtYWUyNi00NGI3LTk0MjMtZTYzMmQ0ZThlMjA0In0.3xjWCO-Su3JP5yCi4ArXKXDP59dn1lzsfOh70OHo0D7K6IExHhkpPsble8XepxEQtaHu2_f3D7ff1mzLD0QkBg"
    
    try:
        client = libsql_client.create_client_sync(url=url, auth_token=token)
        
        print("--- Testing Connection ---")
        res = client.execute("SELECT 1")
        print(f"SELECT 1 success: {res.rows}")
        
        print("--- Testing Table Creation ---")
        client.execute("CREATE TABLE IF NOT EXISTS _test_table (id TEXT PRIMARY KEY, val TEXT)")
        print("CREATE TABLE success")
        
        print("--- Testing Insert ---")
        client.execute("INSERT INTO _test_table (id, val) VALUES (?, ?)", ("1", "test"))
        print("INSERT success")
        
        print("--- Testing Select ---")
        res = client.execute("SELECT * FROM _test_table")
        print(f"SELECT result: {res.rows}")
        
        print("--- Testing Drop ---")
        client.execute("DROP TABLE _test_table")
        print("DROP TABLE success")
        
    except Exception as e:
        print(f"FAILED with {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_db()
