import base64
import os
import sys

# Ensure Mobile Finance Manager modules take priority and parent repo provides shared database/services
MOBILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(MOBILE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if MOBILE_DIR not in sys.path:
    sys.path.insert(0, MOBILE_DIR)

import streamlit as st
if not hasattr(st, "cache"):
    st.cache = st.cache_data

import streamlit_cookies_manager as scm
from streamlit_javascript import st_javascript

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="WealthFlow Mobile",
    page_icon=os.path.join(ROOT_DIR, "assets", "logo.png") if os.path.exists(os.path.join(ROOT_DIR, "assets", "logo.png")) else "💳",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Auto-evict stale local modules after Streamlit Cloud git pull hot-reloads
_M_WATCHED_MODULES = (
    "database",
    "services.auth_service",
    "services.recurring_service",
    "services.budget_service",
    "services.goal_service",
    "services.asset_service",
    "services.loan_service",
    "services.credit_card_service",
    "services.finance_service",
    "services.trip_service",
    "components.mobile_pwa",
    "components.mobile_styles",
    "components.mobile_nav",
    "components.mobile_ui",
    "components.auth_cookie",
    "components.upi_bridge",
    "views.auth_view",
    "views.dashboard_view",
    "views.quick_add_view",
    "views.ledger_view",
    "views.tripflow_view",
    "views.more_views",
)


def _sync_modules():
    db_stale = False
    any_stale = False
    for name in _M_WATCHED_MODULES:
        mod = sys.modules.get(name)
        if mod is None:
            continue
        mod_file = getattr(mod, "__file__", None)
        if not mod_file or not os.path.exists(mod_file):
            continue
        try:
            cur_mtime = os.path.getmtime(mod_file)
        except OSError:
            continue
        if db_stale or getattr(mod, "__wf_m_mtime__", None) != cur_mtime:
            sys.modules.pop(name, None)
            any_stale = True
            if name == "database":
                db_stale = True
    if any_stale:
        try:
            st.cache_data.clear()
        except Exception:
            pass


def _stamp_modules():
    for name in _M_WATCHED_MODULES:
        mod = sys.modules.get(name)
        mod_file = getattr(mod, "__file__", None) if mod is not None else None
        if mod is not None and mod_file and os.path.exists(mod_file) and getattr(mod, "__wf_m_mtime__", None) is None:
            try:
                mod.__wf_m_mtime__ = os.path.getmtime(mod_file)
            except OSError:
                pass


_sync_modules()

# Shared Turso DB & batched backend services (100% reused from parent repo, untouched)
from database import db
from services.finance_service import FinanceService
from services.budget_service import BudgetService
from services.recurring_service import RecurringService
from services.goal_service import GoalService
from services.asset_service import AssetService
from services.loan_service import LoanService
from services.credit_card_service import CreditCardService
from services.auth_service import AuthService
from services.trip_service import TripService

# Mobile-only UI components & views
from components.mobile_pwa import mount_ios_pwa_bridge
from components.mobile_styles import apply_mobile_styles
from components.mobile_nav import render_mobile_topbar, render_mobile_dock
from views.auth_view import render_auth_view
from views.dashboard_view import render_dashboard_view
from views.quick_add_view import render_quick_add_view
from views.ledger_view import render_ledger_view
from views.tripflow_view import render_tripflow_view
from views.more_views import (
    render_more_hub,
    render_budgets_mobile,
    render_subscriptions_mobile,
    render_loans_mobile,
    render_credit_cards_mobile,
    render_goals_mobile,
    render_assets_mobile,
    render_settings_mobile,
    render_admin_mobile,
)

_stamp_modules()


@st.cache_data
def _load_logo_b64() -> str | None:
    logo_path = os.path.join(ROOT_DIR, "assets", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return None


LOGO_B64 = _load_logo_b64()

# Apply Mobile Obsidian Fintech CSS (PWA JS bridge mounts at page end so zero iframe sits above top bar)
apply_mobile_styles()

from components.auth_cookie import get_persisted_token, inject_save_token_script

if "user" not in st.session_state:
    st.session_state.user = None

# Frame-1 synchronous check via native HTTP request cookies
if not st.session_state.user:
    req_token = get_persisted_token()
    if req_token:
        user_data = AuthService.validate_session(req_token)
        if user_data:
            st.session_state.user = user_data

# Persistent Cookie + iOS PWA localStorage session manager
cookies = scm.EncryptedCookieManager(
    password=st.secrets.get("COOKIE_PASSWORD", "wealthflow_pro_2026_secure"),
    path="/",
)

if not st.session_state.user:
    if not cookies.ready():
        st.stop()
    token = get_persisted_token(cookies)
    if not token:
        ls_token = st_javascript("localStorage.getItem('wealthflow_remember_token');")
        if ls_token and ls_token != "null" and isinstance(ls_token, str):
            token = ls_token
            try:
                cookies["wealthflow_remember_token"] = token
                cookies.save()
            except Exception:
                pass
    if token:
        user_data = AuthService.validate_session(token)
        if user_data:
            st.session_state.user = user_data
            st.rerun()

if not st.session_state.get('_purged_archived'):
    try:
        AuthService.purge_expired_archived_users(retention_days=10)
        st.session_state['_purged_archived'] = True
    except Exception:
        pass

# Auth Gate
if not st.session_state.user:
    render_auth_view(LOGO_B64, AuthService, cookies, db)
    mount_ios_pwa_bridge(LOGO_B64)
    st.stop()

# Signed-in User State
user_data = st.session_state.user
uid = user_data["id"]

# Ensure remember token is persistently mirrored to browser document.cookie & localStorage
save_tok = st.session_state.pop("_auth_save_token", None)
if save_tok:
    inject_save_token_script(save_tok)

if "sym" not in st.session_state:
    saved_sym = FinanceService.get_setting("currency_symbol", "₹", uid)
    st.session_state["sym"] = saved_sym if saved_sym in ("₹", "$", "€", "£") else "₹"

if "m_page" not in st.session_state:
    st.session_state["m_page"] = "Home"

# Fire any queued mobile toast
m_toast = st.session_state.pop("m_toast", None)
if m_toast:
    st.toast(m_toast, icon=":material/check_circle:")

# Sticky Mobile Header
render_mobile_topbar(user_data, LOGO_B64, FinanceService, AuthService, cookies)

# Active View Router
page = st.session_state["m_page"]

if page == "Home":
    render_dashboard_view(uid, FinanceService, CreditCardService, LoanService, BudgetService)
elif page == "Ledger":
    render_ledger_view(uid, FinanceService, CreditCardService)
elif page == "QuickAdd":
    render_quick_add_view(uid, FinanceService, TripService)
elif page == "Trips":
    render_tripflow_view(uid, user_data, TripService, db)
elif page == "More":
    render_more_hub(user_data)
elif page == "Budgets":
    render_budgets_mobile(uid, FinanceService, BudgetService)
elif page == "Subscriptions":
    render_subscriptions_mobile(uid, RecurringService)
elif page == "Loans":
    render_loans_mobile(uid, LoanService)
elif page == "Credit Cards":
    render_credit_cards_mobile(uid, CreditCardService, FinanceService)
elif page == "Goals":
    render_goals_mobile(uid, GoalService)
elif page == "Assets":
    render_assets_mobile(uid, AssetService)
elif page == "Settings":
    render_settings_mobile(uid, user_data, FinanceService, AuthService)
elif page == "Admin" and user_data.get("role") == "admin":
    render_admin_mobile(AuthService)
else:
    st.session_state["m_page"] = "Home"
    render_dashboard_view(uid, FinanceService, CreditCardService, LoanService, BudgetService)

# Fixed 5-Slot iOS Bottom Tab Dock & iOS Safari PWA Meta Bridge (at end so top bar is flush top-left)
render_mobile_dock()
mount_ios_pwa_bridge(LOGO_B64)
