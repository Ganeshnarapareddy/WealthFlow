import libsql_client
import streamlit as st

url = st.secrets["TURSO_URL"].replace("libsql://", "https://")
token = st.secrets["TURSO_TOKEN"]
client = libsql_client.create_client_sync(url=url, auth_token=token)

print("Connected")
res = client.execute("SELECT 1")
print("Result 1:", res.rows)

try:
    client.execute("DROP TABLE IF EXISTS test_table")
    print("Dropped")
    client.execute("CREATE TABLE test_table (id TEXT PRIMARY KEY, val TEXT)")
    print("Created")
    client.execute("INSERT INTO test_table (id, val) VALUES ('1', 'hello')")
    print("Inserted")
    res = client.execute("SELECT * FROM test_table")
    print("Result 2:", res.rows)
except Exception as e:
    print("Error:", e)
