import libsql_client
import streamlit as st
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TursoManager:
    """Robust Turso database manager with clean schema management."""
    
    def __init__(self):
        try:
            raw_url = st.secrets["TURSO_URL"]
            # Ensure URL is clean and uses https for the sync client
            self.url = raw_url.replace("libsql://", "https://").strip()
            self.token = st.secrets["TURSO_TOKEN"].strip()
            
            logger.info(f"Connecting to Turso: {self.url}")
            self.client = libsql_client.create_client_sync(url=self.url, auth_token=self.token)
            
            # Immediate test
            self.client.execute("SELECT 1")
            logger.info("TursoManager connected and verified successfully.")
        except Exception as e:
            logger.error(f"FATAL: Failed to connect to Turso: {e}")
            st.error(f"Database Connection Error: {e}")
            raise e

    def execute(self, query: str, params: tuple = ()):
        """Execute a query with defensive error handling for the protocol."""
        try:
            return self.client.execute(query, params)
        except KeyError as e:
            if str(e) == "'result'":
                logger.error(f"Protocol Error (KeyError: 'result') on query: {query}")
                # Return an empty result structure to prevent downstream crashes
                from collections import namedtuple
                MockRes = namedtuple('MockRes', ['rows'])
                return MockRes(rows=[])
            raise e
        except Exception as e:
            logger.error(f"Database Error: {e} on query: {query}")
            raise e

    def initialize_schema(self):
        logger.info("Initializing Pro Schema...")

        ddl = [
            """CREATE TABLE IF NOT EXISTS wf_users (
                id TEXT PRIMARY KEY, username TEXT UNIQUE, email TEXT,
                password_hash TEXT, role TEXT DEFAULT 'user',
                currency TEXT DEFAULT 'USD', created_at TEXT)""",
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
                id TEXT PRIMARY KEY, user_id TEXT, category_id TEXT,
                amount_limit REAL, month INTEGER, year INTEGER)""",
            """CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY, user_id TEXT, name TEXT, amount REAL,
                billing_cycle TEXT, start_date TEXT,
                next_billing_date TEXT, category TEXT, icon TEXT DEFAULT '💳')""",
            """CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY, user_id TEXT, name TEXT, target_amount REAL,
                current_amount REAL DEFAULT 0, deadline TEXT, icon TEXT)""",
            """CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY, name TEXT, type TEXT,
                value REAL, user_id TEXT)""",
            """CREATE TABLE IF NOT EXISTS settings (
                key TEXT, user_id TEXT, value TEXT,
                PRIMARY KEY (key, user_id))""",
            """CREATE TABLE IF NOT EXISTS loans (
                id TEXT PRIMARY KEY, user_id TEXT, person_name TEXT, amount REAL,
                loan_type TEXT, interest_rate REAL DEFAULT 0,
                start_date TEXT, due_date TEXT,
                emi_amount REAL DEFAULT 0, emi_active INTEGER DEFAULT 0,
                tenure INTEGER DEFAULT 0, emi_start_date TEXT,
                status TEXT DEFAULT 'pending',
                remaining_amount REAL, notes TEXT DEFAULT '')""",
            """CREATE TABLE IF NOT EXISTS loan_payments (
                id TEXT PRIMARY KEY, loan_id TEXT, due_date TEXT,
                amount REAL, status TEXT DEFAULT 'pending',
                paid_date TEXT,
                FOREIGN KEY (loan_id) REFERENCES loans(id))""",
            """CREATE TABLE IF NOT EXISTS credit_cards (
                id TEXT PRIMARY KEY, user_id TEXT, name TEXT, bank TEXT,
                card_limit REAL, billing_date INTEGER,
                closing_date INTEGER, current_balance REAL DEFAULT 0)""",
            """CREATE TABLE IF NOT EXISTS credit_card_transactions (
                id TEXT PRIMARY KEY, card_id TEXT, amount REAL,
                description TEXT, date TEXT, txn_type TEXT,
                linked_txn_id TEXT,
                FOREIGN KEY (card_id) REFERENCES credit_cards(id))""",
            """CREATE TABLE IF NOT EXISTS credit_card_emis (
                id TEXT PRIMARY KEY, card_id TEXT, description TEXT,
                total_amount REAL, monthly_amount REAL, tenure INTEGER,
                start_date TEXT, status TEXT DEFAULT 'active',
                FOREIGN KEY (card_id) REFERENCES credit_cards(id))""",
            """CREATE TABLE IF NOT EXISTS credit_card_emi_payments (
                id TEXT PRIMARY KEY, emi_id TEXT, amount REAL, status TEXT DEFAULT 'pending',
                paid_date TEXT,
                FOREIGN KEY (emi_id) REFERENCES credit_card_emis(id))""",
            """CREATE TABLE IF NOT EXISTS actioned_alerts (
                id TEXT PRIMARY KEY, user_id TEXT, alert_id TEXT,
                month_year TEXT, actioned_at TEXT,
                UNIQUE(user_id, alert_id, month_year))"""
        ]
        
        for q in ddl:
            try:
                self.execute(q)
            except Exception as e:
                logger.error(f"Failed to create table with query: {q} | Error: {e}")
                # We don't raise here to allow other tables to be created if one fails
            
        # Migration for CC linking
        try: self.execute("ALTER TABLE credit_card_transactions ADD COLUMN linked_txn_id TEXT")
        except: pass
        
        # Migration for tenure and emi_start_date in loans
        try: self.execute("ALTER TABLE loans ADD COLUMN tenure INTEGER DEFAULT 0")
        except: pass
        try: self.execute("ALTER TABLE loans ADD COLUMN emi_start_date TEXT")
        except: pass
            
        # Seed Categories only if table is empty
        res = self.execute("SELECT COUNT(*) FROM categories")
        if res and res.rows and res.rows[0][0] == 0:
            cats = [
                ("1", "Food", "Expense", "🍱"), ("2", "Transport", "Expense", "🚗"),
                ("3", "Entertainment", "Expense", "🎬"), ("4", "Healthcare", "Expense", "🏥"),
                ("5", "Utilities", "Expense", "⚡"), ("6", "Shopping", "Expense", "🛍️"),
                ("7", "Bills", "Expense", "💸"), ("8", "Subscriptions", "Expense", "💳"),
                ("9", "Other", "Expense", "📁"), ("10", "Salary", "Income", "💰"),
                ("11", "Bonus", "Income", "🌟"), ("12", "Investment", "Income", "📈"),
                ("13", "Freelance", "Income", "💻"),
                ("14", "EMI Payment", "Expense", "💳"),
                ("15", "Loan Payment", "Expense", "🏦"),
                ("16", "Subscription Payments", "Expense", "🔄")
            ]
            for c in cats:
                self.execute("INSERT OR IGNORE INTO categories (id, name, type, icon) VALUES (?, ?, ?, ?)", c)
        
        # Force rename/update categories to match user requirements exactly
        # Ensure Subscriptions is ID 8, EMI Payment is 14, Loan Payment is 15
        self.execute("UPDATE categories SET name = 'Subscriptions', icon = '📺' WHERE id = '8'")
        self.execute("INSERT OR IGNORE INTO categories (id, name, type, icon) VALUES ('14', 'EMI Payment', 'Expense', '💳')")
        self.execute("UPDATE categories SET name = 'EMI Payment', icon = '💳' WHERE id = '14'")
        self.execute("INSERT OR IGNORE INTO categories (id, name, type, icon) VALUES ('15', 'Loan Payment', 'Expense', '🏦')")
        self.execute("UPDATE categories SET name = 'Loan Payment', icon = '🏦' WHERE id = '15'")

        # Seed default settings
        self.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('fiscal_month_start_day', '1')")

        # 1. Column Migrations
        try: self.execute("ALTER TABLE wf_users ADD COLUMN password_hash TEXT")
        except: pass
        try: self.execute("ALTER TABLE wf_users ADD COLUMN role TEXT DEFAULT 'user'")
        except: pass
        try: self.execute("ALTER TABLE wf_users ADD COLUMN email TEXT")
        except: pass
        try: self.execute("ALTER TABLE wf_users ADD COLUMN currency TEXT DEFAULT 'USD'")
        except: pass
        try: self.execute("ALTER TABLE wf_users ADD COLUMN phone TEXT")
        except: pass
        try: self.execute("ALTER TABLE wf_users ADD COLUMN short_id INTEGER")
        except: pass
        try: self.execute("ALTER TABLE wf_users ADD COLUMN status TEXT DEFAULT 'active'")
        except: pass
        try: self.execute("ALTER TABLE wf_users ADD COLUMN deleted_at TEXT")
        except: pass
        try: self.execute("ALTER TABLE wf_users ADD COLUMN session_token TEXT")
        except: pass
        try: self.execute("ALTER TABLE wf_users ADD COLUMN session_expiry TEXT")
        except: pass

        # 1. Add user_id column to ALL tables if missing
        all_app_tables = [
            'transactions', 'credit_card_transactions', 'budgets', 'subscriptions', 
            'goals', 'loans', 'credit_cards', 'assets', 'credit_card_emis', 
            'credit_card_emi_payments', 'settings', 'actioned_alerts', 'categories'
        ]
        for table in all_app_tables:
            try: self.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT")
            except: pass

        # Ensure settings has the correct primary key for per-user settings
        try:
            self.execute("CREATE TABLE IF NOT EXISTS settings_new (key TEXT, user_id TEXT, value TEXT, PRIMARY KEY (key, user_id))")
            self.execute("INSERT OR IGNORE INTO settings_new SELECT key, user_id, value FROM settings")
            self.execute("DROP TABLE settings")
            self.execute("ALTER TABLE settings_new RENAME TO settings")
        except: pass

        # 2. Ensure default admin user exists (Initial setup only)
        try:
            res = self.execute("SELECT id FROM wf_users WHERE username = 'admin'")
            if not res or not res.rows:
                import hashlib
                SALT = "wealthflow_secure_2026"
                admin_pass_hash = hashlib.sha256(("admin123" + SALT).encode()).hexdigest()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                self.execute(
                    "INSERT INTO wf_users (id, username, password_hash, role, created_at, currency, status) VALUES (?, ?, ?, ?, ?, ?, 'active')",
                    ("admin", "admin", admin_pass_hash, "admin", now, "INR")
                )
        except Exception as e:
            logger.warning(f"Note: Could not ensure default admin user: {e}")

        # 3. Assign existing data to 'admin'
        try:
            all_tables = [
                'accounts', 'transactions', 'credit_card_transactions', 'assets', 
                'loans', 'budgets', 'subscriptions', 'goals', 'credit_cards', 
                'credit_card_emis', 'credit_card_emi_payments', 'settings', 'actioned_alerts'
            ]
            for table in all_tables:
                try: self.execute(f"UPDATE {table} SET user_id = 'admin' WHERE user_id IS NULL OR user_id = 'default_user'")
                except: pass
        except Exception as e:
            logger.warning(f"Note: Could not migrate legacy data: {e}")

        # Ensure default account for admin
        try:
            res = self.execute("SELECT COUNT(*) FROM accounts WHERE user_id = 'admin'")
            if res and res.rows[0][0] == 0:
                self.execute(
                    "INSERT OR IGNORE INTO accounts (id, user_id, account_name, balance, account_type) VALUES (?, ?, ?, ?, ?)",
                    ("default_account_admin", "admin", "Main Account", 0.0, "Savings")
                )
        except Exception as e:
            logger.warning(f"Note: Could not create default admin account (may already exist): {e}")

@st.cache_resource
def get_db_instance(v=3):
    manager = TursoManager()
    manager.initialize_schema()
    return manager

db = get_db_instance(v=4)
