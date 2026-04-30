import libsql_client
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TursoManager:
    """Robust Turso database manager with clean schema management."""
    
    def __init__(self):
        try:
            raw_url = st.secrets["TURSO_URL"]
            self.url = raw_url.replace("libsql://", "https://")
            self.token = st.secrets["TURSO_TOKEN"]
            self.client = libsql_client.create_client_sync(url=self.url, auth_token=self.token)
            logger.info("TursoManager connected successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize TursoManager: {e}")
            raise e

    def execute(self, query: str, params: tuple = ()):
        """Execute a query. Returns result or None on failure."""
        try:
            return self.client.execute(query, params)
        except Exception as e:
            logger.error(f"DB Error: {type(e).__name__} - {e} | Query: {query}")
            return None

    def initialize_schema(self):
        logger.info("Initializing Pro Schema...")
        
        ddl = [
            """CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, username TEXT, email TEXT, 
                currency TEXT DEFAULT 'USD')""",
            """CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY, user_id TEXT, account_name TEXT, 
                balance REAL, account_type TEXT)""",
            """CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY, name TEXT, type TEXT, icon TEXT)""",
            """CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY, user_id TEXT, account_id TEXT, 
                category_id TEXT, amount REAL, type TEXT, 
                date TEXT, description TEXT)""",
            """CREATE TABLE IF NOT EXISTS budgets (
                id TEXT PRIMARY KEY, category_id TEXT, 
                amount_limit REAL, month INTEGER, year INTEGER)""",
            """CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY, name TEXT, amount REAL, 
                billing_cycle TEXT, start_date TEXT, 
                next_billing_date TEXT, category TEXT, icon TEXT DEFAULT '💳')""",
            """CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY, name TEXT, target_amount REAL, 
                current_amount REAL DEFAULT 0, deadline TEXT, icon TEXT)""",
            """CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY, name TEXT, type TEXT, 
                value REAL, user_id TEXT)"""
        ]
        
        for q in ddl:
            self.execute(q)
            
        # Migration for icon in subscriptions
        self.execute("ALTER TABLE subscriptions ADD COLUMN icon TEXT DEFAULT '💳'")
            
        # Seed/Update Categories
        cats = [
            ("1", "Housing", "Expense", "🏠"), ("2", "Food", "Expense", "🍱"),
            ("3", "Transport", "Expense", "🚗"), ("4", "Entertainment", "Expense", "🎬"),
            ("5", "Healthcare", "Expense", "🏥"), ("6", "Utilities", "Expense", "⚡"),
            ("7", "Shopping", "Expense", "🛍️"), ("8", "Education", "Expense", "🎓"),
            ("9", "Tuition Fees", "Expense", "📚"), ("10", "Wellness", "Expense", "🧘"),
            ("11", "Travel", "Expense", "✈️"), ("12", "Insurance", "Expense", "🛡️"),
            ("13", "Maintenance", "Expense", "🔧"), ("14", "Subscriptions", "Expense", "💳"),
            ("15", "Charity", "Expense", "🤝"), ("16", "Personal Care", "Expense", "🧴"),
            ("17", "Bills", "Expense", "🧾"), ("18", "Others", "Expense", "📁"),
            ("19", "Salary", "Income", "💰"), ("20", "Investment", "Income", "📈"),
            ("21", "Gifts", "Income", "🎁"), ("22", "Freelance", "Income", "💻"),
            ("23", "Bonus", "Income", "🌟"), ("24", "Dividends", "Income", "🎟️"),
            ("25", "Rental", "Income", "🏠"), ("26", "Business", "Income", "💼"),
            ("27", "Rebate", "Income", "💸"), ("28", "Other Income", "Income", "💰")
        ]
        for c in cats:
            self.execute("INSERT OR REPLACE INTO categories (id, name, type, icon) VALUES (?, ?, ?, ?)", c)

        # Ensure default account
        res = self.execute("SELECT COUNT(*) FROM accounts")
        if res and res.rows[0][0] == 0:
            self.execute(
                "INSERT INTO accounts (id, user_id, account_name, balance, account_type) VALUES (?, ?, ?, ?, ?)",
                ("default_account", "default_user", "Main Account", 0.0, "Savings")
            )

@st.cache_resource
def get_db_instance(v=2):
    manager = TursoManager()
    manager.initialize_schema()
    return manager

db = get_db_instance(v=2)
