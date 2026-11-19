import libsql_client
import streamlit as st
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from collections import namedtuple

_WRITE_PREFIXES = ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "ALTER", "DROP")
_MockRes = namedtuple('MockRes', ['rows'])


def _is_write_query(query: str) -> bool:
    if not query:
        return False
    first = query.lstrip().split(None, 1)
    return bool(first and first[0].upper() in _WRITE_PREFIXES)


class TursoManager:
    """Robust Turso database manager with bulk batch execution and cache versioning."""
    
    def __init__(self):
        self.version = 0
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

    def bump_version(self):
        """Increment monotonic data version so cached reads refresh immediately after any write."""
        self.version += 1

    def execute(self, query: str, params: tuple = ()):
        """Execute a query with defensive error handling for the protocol."""
        try:
            res = self.client.execute(query, params)
            if _is_write_query(query):
                self.version += 1
            return res
        except KeyError as e:
            if str(e) == "'result'":
                logger.error(f"Protocol Error (KeyError: 'result') on query: {query}")
                return _MockRes(rows=[])
            raise e
        except Exception as e:
            logger.error(f"Database Error: {e} on query: {query}")
            raise e

    def batch(self, statements):
        """Execute multiple SQL statements in a single Turso HTTP roundtrip.
        Each item may be a SQL string, a (sql, params) tuple, or a libsql_client.Statement.
        """
        if not statements:
            return []
        libsql_stmts = []
        has_write = False
        for item in statements:
            if isinstance(item, libsql_client.Statement):
                libsql_stmts.append(item)
                if _is_write_query(item.sql):
                    has_write = True
            elif isinstance(item, (tuple, list)):
                sql = item[0]
                params = item[1] if len(item) > 1 and item[1] is not None else ()
                libsql_stmts.append(libsql_client.Statement(sql, params))
                if _is_write_query(sql):
                    has_write = True
            else:
                libsql_stmts.append(libsql_client.Statement(str(item)))
                if _is_write_query(str(item)):
                    has_write = True
        try:
            results = self.client.batch(libsql_stmts)
            if has_write:
                self.version += 1
            return results
        except Exception as e:
            logger.warning(f"Batch execution failed ({e}); falling back to sequential execution.")
            results = []
            for st_obj in libsql_stmts:
                results.append(self.execute(st_obj.sql, st_obj.args or ()))
            return results

    def table_exists(self, table_name):
        """Check if a table exists in the database."""
        try:
            res = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return res and res.rows and len(res.rows) > 0
        except:
            return False

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
                UNIQUE(user_id, alert_id, month_year))""",
            """CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY, user_id TEXT, token TEXT UNIQUE,
                expiry TEXT, created_at TEXT)""",
            """CREATE TABLE IF NOT EXISTS trips (
                id TEXT PRIMARY KEY, user_id TEXT, name TEXT, description TEXT,
                target_budget REAL DEFAULT 0, start_date TEXT, end_date TEXT,
                status TEXT DEFAULT 'active', created_at TEXT)""",
            """CREATE TABLE IF NOT EXISTS trip_members (
                id TEXT PRIMARY KEY, trip_id TEXT, name TEXT,
                weight REAL DEFAULT 1.0, max_budget REAL DEFAULT NULL,
                created_at TEXT)""",
            """CREATE TABLE IF NOT EXISTS trip_advances (
                id TEXT PRIMARY KEY, trip_id TEXT, member_id TEXT,
                amount REAL, description TEXT, date TEXT)""",
            """CREATE TABLE IF NOT EXISTS trip_expenses (
                id TEXT PRIMARY KEY, trip_id TEXT, payer_member_id TEXT,
                paid_from_pool INTEGER DEFAULT 0, amount REAL,
                description TEXT, date TEXT, split_type TEXT DEFAULT 'equal')""",
            """CREATE TABLE IF NOT EXISTS trip_expense_splits (
                id TEXT PRIMARY KEY, expense_id TEXT, member_id TEXT,
                weight REAL DEFAULT 1.0, share_amount REAL)""",
            """CREATE TABLE IF NOT EXISTS trip_settlements (
                id TEXT PRIMARY KEY, trip_id TEXT, from_name TEXT,
                to_name TEXT, amount REAL, settled_at TEXT)"""
        ]
        
        # Batch all CREATE TABLE IF NOT EXISTS statements in one roundtrip
        try:
            self.batch(ddl)
        except Exception:
            for q in ddl:
                try:
                    self.execute(q)
                except Exception as e:
                    logger.error(f"Failed to create table with query: {q} | Error: {e}")

        # Seed categories + normalize core category IDs + default settings in bulk
        res = self.execute("SELECT COUNT(*) FROM categories")
        seed_stmts = []
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
                seed_stmts.append(("INSERT OR IGNORE INTO categories (id, name, type, icon) VALUES (?, ?, ?, ?)", c))

        seed_stmts.extend([
            ("UPDATE categories SET name = 'Subscriptions', icon = '📺' WHERE id = '8'", ()),
            ("INSERT OR IGNORE INTO categories (id, name, type, icon) VALUES ('14', 'EMI Payment', 'Expense', '💳')", ()),
            ("UPDATE categories SET name = 'EMI Payment', icon = '💳' WHERE id = '14'", ()),
            ("INSERT OR IGNORE INTO categories (id, name, type, icon) VALUES ('15', 'Loan Payment', 'Expense', '🏦')", ()),
            ("UPDATE categories SET name = 'Loan Payment', icon = '🏦' WHERE id = '15'", ()),
            ("INSERT OR IGNORE INTO settings (key, user_id, value) VALUES ('fiscal_month_start_day', 'admin', '1')", ()),
        ])
        self.batch(seed_stmts)

        # Fast schema inspection in a single batch (only runs ALTER TABLE if a column is genuinely missing)
        inspect_tables = [
            'credit_card_transactions', 'loans', 'wf_users', 'transactions',
            'budgets', 'subscriptions', 'goals', 'credit_cards', 'assets',
            'credit_card_emis', 'credit_card_emi_payments', 'settings',
            'actioned_alerts', 'categories'
        ]
        pragma_results = self.batch([f"PRAGMA table_info({t})" for t in inspect_tables])
        table_cols = {}
        for t, r in zip(inspect_tables, pragma_results):
            table_cols[t] = {row[1] for row in r.rows} if (r and r.rows) else set()

        alter_stmts = []
        if 'linked_txn_id' not in table_cols['credit_card_transactions']:
            alter_stmts.append("ALTER TABLE credit_card_transactions ADD COLUMN linked_txn_id TEXT")
        if 'tenure' not in table_cols['loans']:
            alter_stmts.append("ALTER TABLE loans ADD COLUMN tenure INTEGER DEFAULT 0")
        if 'emi_start_date' not in table_cols['loans']:
            alter_stmts.append("ALTER TABLE loans ADD COLUMN emi_start_date TEXT")

        user_cols_needed = [
            ('password_hash', 'TEXT'), ('role', "TEXT DEFAULT 'user'"), ('email', 'TEXT'),
            ('currency', "TEXT DEFAULT 'USD'"), ('phone', 'TEXT'), ('short_id', 'INTEGER'),
            ('status', "TEXT DEFAULT 'active'"), ('deleted_at', 'TEXT'),
        ]
        for col, col_def in user_cols_needed:
            if col not in table_cols['wf_users']:
                alter_stmts.append(f"ALTER TABLE wf_users ADD COLUMN {col} {col_def}")

        for table in [
            'transactions', 'credit_card_transactions', 'budgets', 'subscriptions',
            'goals', 'loans', 'credit_cards', 'assets', 'credit_card_emis',
            'credit_card_emi_payments', 'settings', 'actioned_alerts', 'categories'
        ]:
            if 'user_id' not in table_cols[table]:
                alter_stmts.append(f"ALTER TABLE {table} ADD COLUMN user_id TEXT")

        if alter_stmts:
            for stmt in alter_stmts:
                try:
                    self.execute(stmt)
                except Exception:
                    pass

        # Performance Indexes: Composite indexes for sub-millisecond query performance
        index_ddl = [
            "CREATE INDEX IF NOT EXISTS idx_txn_user_date ON transactions(user_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_txn_user_cat ON transactions(user_id, category_id)",
            "CREATE INDEX IF NOT EXISTS idx_cc_txn_card_date ON credit_card_transactions(card_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_budgets_user_period ON budgets(user_id, year, month)",
            "CREATE INDEX IF NOT EXISTS idx_loans_user ON loans(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_assets_user ON assets(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_actioned_alerts_user ON actioned_alerts(user_id, alert_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(token)",
            "CREATE INDEX IF NOT EXISTS idx_wf_users_user ON wf_users(username)",
        ]
        try:
            self.batch(index_ddl)
        except Exception:
            for idx_stmt in index_ddl:
                try:
                    self.execute(idx_stmt)
                except Exception:
                    pass

        # Ensure default admin user & default admin account exist (single batch check)
        try:
            chk_res = self.batch([
                ("SELECT id FROM wf_users WHERE role = 'admin' OR id = 'admin' OR username = 'admin' LIMIT 1", ()),
                ("SELECT COUNT(*) FROM accounts", ()),
            ])
            admin_id = chk_res[0].rows[0][0] if (chk_res[0] and chk_res[0].rows) else None
            setup_stmts = []
            if not admin_id:
                import hashlib
                SALT = "wealthflow_secure_2026"
                admin_pass_hash = hashlib.sha256(("admin123" + SALT).encode()).hexdigest()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                admin_id = "admin"
                setup_stmts.append((
                    "INSERT OR IGNORE INTO wf_users (id, username, password_hash, role, created_at, currency, status) VALUES (?, ?, ?, ?, ?, ?, 'active')",
                    ("admin", "admin", admin_pass_hash, "admin", now, "INR")
                ))
            if not (chk_res[1] and chk_res[1].rows and chk_res[1].rows[0][0] > 0):
                setup_stmts.append((
                    "INSERT OR IGNORE INTO accounts (id, user_id, account_name, balance, account_type) VALUES (?, ?, ?, ?, ?)",
                    ("default_account_admin", admin_id, "Main Account", 0.0, "Savings")
                ))
            if setup_stmts:
                self.batch(setup_stmts)
        except Exception as e:
            logger.warning(f"Note: Could not ensure default admin user/account: {e}")

@st.cache_resource
def get_db_instance(v=5):
    manager = TursoManager()
    manager.initialize_schema()
    return manager

db = get_db_instance(v=5)
