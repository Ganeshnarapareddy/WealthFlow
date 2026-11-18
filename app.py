import streamlit as st
if not hasattr(st, "cache"):
    st.cache = st.cache_data
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit_cookies_manager as scm
from streamlit_javascript import st_javascript
from datetime import datetime, timedelta
import base64
import html as _html
import os
import sys
import json
import streamlit.components.v1 as components

# Auto-reload stale local modules after git pull on Streamlit Cloud hot-reloads
_WF_LOCAL_MODULES = (
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
    "components.styles",
    "components.ui_elements",
    "components.sidebar",
)

def _sync_local_modules():
    """Evict stale local modules when files change on disk (fixes Streamlit Cloud hot-reload after git pull)."""
    db_stale = False
    any_stale = False
    for name in _WF_LOCAL_MODULES:
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
        if db_stale or getattr(mod, "__wf_mtime__", None) != cur_mtime:
            sys.modules.pop(name, None)
            any_stale = True
            if name == "database":
                db_stale = True
    if any_stale:
        try:
            st.cache_data.clear()
        except Exception:
            pass

def _stamp_local_modules():
    for name in _WF_LOCAL_MODULES:
        mod = sys.modules.get(name)
        mod_file = getattr(mod, "__file__", None) if mod is not None else None
        if mod is not None and mod_file and os.path.exists(mod_file) and getattr(mod, "__wf_mtime__", None) is None:
            try:
                mod.__wf_mtime__ = os.path.getmtime(mod_file)
            except OSError:
                pass

_sync_local_modules()

# Import Services
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

# --- LOGO HELPER ---
@st.cache_data
def get_base64_logo():
    logo_path = os.path.join("assets", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    return None

LOGO_B64 = get_base64_logo()

# --- COOKIE MANAGEMENT ---
# Using the more persistent EncryptedCookieManager
cookies = scm.EncryptedCookieManager(
    password=st.secrets.get("COOKIE_PASSWORD", "wealthflow_pro_2026_secure"),
    path="/"
)
if not cookies.ready():
    st.stop()

# Session State Initialization
if "user" not in st.session_state:
    st.session_state.user = None

# --- PERSISTENT LOGIN CHECK ---
if not st.session_state.user:
    token = cookies.get('wealthflow_remember_token')
    
    # iPhone PWA Fallback: Check localStorage if cookie is missing or empty
    if not token:
        # st_javascript returns the value directly
        ls_token = st_javascript("localStorage.getItem('wealthflow_remember_token');")
        if ls_token and ls_token != "null" and isinstance(ls_token, str):
            token = ls_token
            # Sync back to cookie for next time
            cookies['wealthflow_remember_token'] = token
            cookies.save()

    if token:
        user_data = AuthService.validate_session(token)
        if user_data:
            st.session_state.user = user_data
            st.rerun()

# AUTO-REPAIR: Database integrity fixes (once per session, single batched call)
if not st.session_state.get('_db_repaired'):
    try:
        db.batch([
            ("UPDATE wf_users SET username = TRIM(username)", ()),
            ("UPDATE wf_users SET short_id = '00001' WHERE role = 'admin' AND (short_id IS NULL OR short_id = 'None')", ()),
        ])
        if st.session_state.get('user') and st.session_state.user['role'] == 'admin':
            if st.session_state.user.get('short_id') in [None, 'None']:
                st.session_state.user['short_id'] = '00001'
    except Exception:
        pass
    st.session_state['_db_repaired'] = True

# Import UI Components
from components.styles import apply_styles
from components.ui_elements import card_metric, section_header, empty_state, stat_strip, style_plotly
from components.sidebar import render_sidebar
_stamp_local_modules()

# Constants
ASSET_TYPES = ["Mutual Fund", "Stock", "Crypto", "Gold", "Real Estate", "FD", "Other"]

# --- CONFIG ---
st.set_page_config(
    page_title="WealthFlow Pro",
    page_icon=LOGO_B64 if LOGO_B64 else "💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- APPLE HOME SCREEN ICON ---
if LOGO_B64:
    st.markdown(f'<link rel="apple-touch-icon" href="{LOGO_B64}">', unsafe_allow_html=True)

# --- GLOBAL STYLES — handled by components/styles.py token system ---
apply_styles()

# --- AUTHENTICATION ---
def login_page():
    col1, col2, col3 = st.columns([1.2, 1.6, 1.2])
    with col2:
        with st.container(border=True):
            logo_html = f'<img src="{LOGO_B64}" alt="WealthFlow">' if LOGO_B64 else '<span class="wf-rail-logo-fallback">W</span>'
            st.markdown(f'<div class="auth-logo">{logo_html}<div>WealthFlow</div></div>', unsafe_allow_html=True)

            tab_login, tab_signup, tab_forgot = st.tabs(["Sign in", "Create account", "Reset password"])

            with tab_login:
                user_in = st.text_input("Username", key="l_user")
                pass_in = st.text_input("Password", type="password", key="l_pass")
                l_remember = st.checkbox("Remember me for 30 days", value=True, key="l_remember")
                if st.button("Sign in", use_container_width=True, type="primary"):
                    user = AuthService.login(user_in.strip(), pass_in)
                    if user:
                        st.session_state.user = user
                        if l_remember:
                            token = AuthService.create_session(user['id'])
                            cookies['wealthflow_remember_token'] = token
                            cookies.save()
                            # Backup to localStorage for mobile PWA persistence
                            st_javascript(f"localStorage.setItem('wealthflow_remember_token', '{token}');")
                        # Load saved currency preference
                        saved_sym = FinanceService.get_setting('currency_symbol', '₹', user['id'])
                        st.session_state['sym'] = saved_sym
                        # ULTIMATE SAFETY: Only allow the admin account to trigger the data repair/claim logic.
                        if user['username'] == 'admin':
                            FinanceService.repair_legacy_data(user['id'])
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

            with tab_signup:
                s_user = st.text_input("Choose Username", key="s_user")
                s_pass = st.text_input("Choose Password", type="password", key="s_pass")
                s_email = st.text_input("Email", key="s_email")
                s_phone = st.text_input("Phone Number", key="s_phone")
                s_remember = st.checkbox("Remember me for 30 days", value=True, key="s_remember")
                st.info("Providing an email or phone number ensures your data can be recovered if needed.")
                if st.button("Create Account", use_container_width=True, type="primary"):
                    if not s_email and not s_phone:
                        st.error("Email or Phone is mandatory for account recovery.")
                    elif len(s_user) < 3 or len(s_pass) < 6:
                        st.warning("Username must be >= 3 and Password >= 6 characters")
                    else:
                        uid_res = AuthService.signup(s_user.strip(), s_pass, s_email, s_phone)
                        if isinstance(uid_res, str) and len(uid_res) > 30:
                            user = AuthService.login(s_user.strip(), s_pass)
                            if user:
                                st.session_state.user = user
                                if s_remember:
                                    token = AuthService.create_session(user['id'])
                                    cookies['wealthflow_remember_token'] = token
                                    cookies.save()
                                    # Backup to localStorage for mobile PWA persistence
                                    st_javascript(f"localStorage.setItem('wealthflow_remember_token', '{token}');")
                                st.rerun()
                        else:
                            st.error(str(uid_res))

            with tab_forgot:
                st.markdown("#### Account recovery")
                st.caption("Enter your registered email or phone to reset your password.")
                f_contact = st.text_input("Registered Email or Phone", key="f_contact")
                f_pass = st.text_input("New Password", type="password", key="f_pass")
                if st.button("Verify & Reset Password", use_container_width=True, type="primary"):
                    if not f_contact:
                        st.error("Please enter your contact info.")
                    else:
                        from database import db
                        # Find user by email or phone
                        res = db.execute("SELECT id FROM wf_users WHERE (email = ? OR phone = ?) AND status = 'active'", (f_contact, f_contact))
                        if res and res.rows:
                            AuthService.update_password(res.rows[0][0], f_pass)
                            st.success("Password updated. You can now sign in.")
                        else:
                            st.error("Contact information not found.")

# Auth Check
if not st.session_state.user:
    login_page()
    st.stop()

uid = st.session_state.user['id']

# Initialize Session State
if 'sym' not in st.session_state:
    if st.session_state.user:
        st.session_state['sym'] = FinanceService.get_setting('currency_symbol', '₹', st.session_state.user['id'])
    else:
        st.session_state['sym'] = '₹'
if 'edit_asset_id' not in st.session_state: st.session_state['edit_asset_id'] = None
if 'page' not in st.session_state: st.session_state['page'] = 'Dashboard'
if 'show_menu' not in st.session_state: st.session_state['show_menu'] = False
if 'should_collapse_sidebar' not in st.session_state: st.session_state['should_collapse_sidebar'] = False
if 'delete_confirm' not in st.session_state: st.session_state['delete_confirm'] = {}
if 'sub_added' not in st.session_state: st.session_state['sub_added'] = False
if 'budget_added' not in st.session_state: st.session_state['budget_added'] = False
if 'goal_added' not in st.session_state: st.session_state['goal_added'] = False
if 'asset_added' not in st.session_state: st.session_state['asset_added'] = False
if 'loan_added' not in st.session_state: st.session_state['loan_added'] = False
if 'loan_deleted' not in st.session_state: st.session_state['loan_deleted'] = False
if 'card_added' not in st.session_state: st.session_state['card_added'] = False
if 'card_deleted' not in st.session_state: st.session_state['card_deleted'] = False
if 'loan_payment_added' not in st.session_state: st.session_state['loan_payment_added'] = False
if 'card_txn_added' not in st.session_state: st.session_state['card_txn_added'] = False
if 'edit_loan_id' not in st.session_state: st.session_state['edit_loan_id'] = None
if 'edit_card_id' not in st.session_state: st.session_state['edit_card_id'] = None
if 'cat_added' not in st.session_state: st.session_state['cat_added'] = False
if 'txn_deleted' not in st.session_state: st.session_state['txn_deleted'] = False
if 'card_txn_deleted' not in st.session_state: st.session_state['card_txn_deleted'] = False
if 'loan_given_version' not in st.session_state: st.session_state['loan_given_version'] = 0
if 'loan_taken_version' not in st.session_state: st.session_state['loan_taken_version'] = 0
if 'card_add_version' not in st.session_state: st.session_state['card_add_version'] = 0
if 'active_trip_id' not in st.session_state: st.session_state['active_trip_id'] = None
if 'trip_added' not in st.session_state: st.session_state['trip_added'] = False
if 'trip_deleted' not in st.session_state: st.session_state['trip_deleted'] = False
if 'trip_expense_added' not in st.session_state: st.session_state['trip_expense_added'] = False
if 'trip_advance_added' not in st.session_state: st.session_state['trip_advance_added'] = False
if 'trip_member_added' not in st.session_state: st.session_state['trip_member_added'] = False
if 'edit_member_id' not in st.session_state: st.session_state['edit_member_id'] = None

# --- SIDEBAR NAVIGATION ---
render_sidebar(st.session_state.user, LOGO_B64, FinanceService, AuthService, cookies)

# --- PAGE CONTENT ---

def fmt(val):
    if val is None:
        return f"{st.session_state['sym']}0.00"
    return f"{st.session_state['sym']}{val:,.2f}"

# Delete confirmation helper — floating popover keeps Yes / No cleanly side-by-side without narrow-column wrapping
def render_delete_button(item_id, button_key, delete_func, user_id, item_name="item"):
    with st.popover("", icon=":material/delete_outline:", help=f"Delete {item_name}"):
        st.markdown(
            f'<div class="wf-del-confirm-msg">Delete <strong>{_html.escape(str(item_name))}</strong>?</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes", icon=":material/check:", type="primary", use_container_width=True, key=f"yes_{button_key}"):
                delete_func(item_id, user_id)
                if "cdel_" in button_key: st.session_state['card_deleted'] = True
                elif "ldel_" in button_key or "del_loan_" in button_key: st.session_state['loan_deleted'] = True
                elif "del_c_txn_" in button_key: st.session_state['card_txn_deleted'] = True
                st.rerun()
        with c2:
            if st.button("No", icon=":material/close:", use_container_width=True, key=f"no_{button_key}"):
                st.rerun()

page = st.session_state['page']

if page == "Dashboard":
    # v1.1 - Dashboard with Daily Analytics
    h1, h2, h3, h4 = st.columns([2, 1.2, 1.2, 1.2])
    with h1: st.markdown('<h1 class="main-header">Command Center</h1>', unsafe_allow_html=True)
    with h2:
        # Year selector with "All" option
        years = FinanceService.get_available_years(uid)
        year_options = [str(y) for y in years] + ["All"]
        if 'selected_year' not in st.session_state:
            st.session_state['selected_year'] = str(datetime.now().year)
        try:
            year_idx = year_options.index(str(st.session_state['selected_year']))
        except:
            year_idx = 0
        sel_year_str = st.selectbox("Year", year_options, index=year_idx, label_visibility="collapsed", key="year_sel")
        sel_year = "All" if sel_year_str == "All" else int(sel_year_str)
        if sel_year != st.session_state['selected_year']:
            st.session_state['selected_year'] = sel_year
            st.rerun()

    # Fiscal Month Toggle
    fiscal_day = FinanceService.get_setting('fiscal_month_start_day', '1', uid)
    fiscal_day = int(fiscal_day) if str(fiscal_day).isdigit() else 1
    
    if 'month_mode' not in st.session_state:
        st.session_state['month_mode'] = "Calendar"
        
    st.session_state['month_mode'] = st.radio(
        "Month Mode", ["Calendar", "Fiscal"], 
        index=0 if st.session_state['month_mode'] == "Calendar" else 1,
        horizontal=True, label_visibility="collapsed", key="month_mode_radio"
    )
    month_mode = st.session_state['month_mode']

    with h3:
        # Month selector with "All" option
        if 'selected_month' not in st.session_state:
            st.session_state['selected_month'] = "All"

        # Fiscal mode: show fiscal period labels
        if month_mode == "Fiscal" and sel_year != "All":
            fiscal_day_val = FinanceService.get_setting('fiscal_month_start_day', '1', uid)
            fiscal_day_val = int(fiscal_day_val) if str(fiscal_day_val).isdigit() else 1
            month_options = ["All"]
            month_map = [None]  # index 0 = All
            for m in range(1, 13):
                label = FinanceService.get_fiscal_month_label(sel_year, m, fiscal_day_val)
                month_options.append(label)
                month_map.append(m)
            try:
                sel = st.session_state['selected_month']
                if sel == "All":
                    idx = 0
                else:
                    idx = month_map.index(int(sel))
            except:
                idx = 0
            sel_label = st.selectbox("Month", month_options, index=idx, label_visibility="collapsed", key="month_sel")
            sel_month = "All" if sel_label == "All" else month_map[month_options.index(sel_label)]
        else:
            month_display = ["All", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            try:
                if st.session_state['selected_month'] == "All":
                    month_idx = 0
                else:
                    month_idx = int(st.session_state['selected_month'])
            except:
                month_idx = 0
            sel_month_disp = st.selectbox("Month", month_display, index=month_idx, label_visibility="collapsed", key="month_sel")
            sel_month = "All" if sel_month_disp == "All" else month_display.index(sel_month_disp)

        if sel_month != st.session_state['selected_month']:
            st.session_state['selected_month'] = sel_month
            st.rerun()

    with h4:
        # Currency selector
        sym_map = {"INR (₹)": "₹", "USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
        try: curr_idx = list(sym_map.values()).index(st.session_state['sym'])
        except: curr_idx = 0
        cur_label = st.selectbox("Currency", list(sym_map.keys()), index=curr_idx, label_visibility="collapsed", key="cur_sel")
        if sym_map[cur_label] != st.session_state['sym']:
            st.session_state['sym'] = sym_map[cur_label]
            st.rerun()

    # Now that sel_year and sel_month are both known, calculate the final fiscal_start_day
    fiscal_start_day = fiscal_day if (month_mode == "Fiscal" and sel_year != "All" and sel_month != "All") else None

    # Bulk-fetch ALL Dashboard KPIs, Credit Cards, Alerts, and Wealth Allocation in ONE DB roundtrip (cached)
    dash = FinanceService.get_dashboard_bundle(uid, sel_year, sel_month, month_mode, fiscal_day)

    net = dash["net_worth"]
    burn = dash["burn"]
    inc = dash["inc"]
    exp = dash["exp"]
    today_spent = dash["today_spent"]
    yesterday_spent = dash["yesterday_spent"]
    day_pct = ((today_spent - yesterday_spent) / yesterday_spent * 100) if yesterday_spent > 0 else 0

    prev_inc = dash["prev_inc"]
    prev_exp = dash["prev_exp"]
    prev_label = dash["prev_label"]
    inc_delta_str, inc_increased = FinanceService.get_comparison_delta(inc, prev_inc)
    exp_delta_str, exp_increased = FinanceService.get_comparison_delta(exp, prev_exp)

    savings_rate = ((inc - exp) / inc * 100) if inc > 0 else 0.0
    prev_savings_rate = ((prev_inc - prev_exp) / prev_inc * 100) if prev_inc > 0 else 0.0
    sr_delta_str, sr_increased = FinanceService.get_comparison_delta(savings_rate, prev_savings_rate)

    total_emi_amt = dash["total_emi_amt"]
    active_emi_count = dash["active_emi_count"]
    active_subs_count = dash["active_subs_count"]

    prev_burn = dash["prev_burn"]
    burn_delta_str = None
    burn_increased = False
    if sel_year != "All" and sel_month != "All":
        burn_delta_str, burn_increased = FinanceService.get_comparison_delta(burn, prev_burn)

    # Primary KPI Strip — Hallmark hairline-divided row (no card wall)
    day_tone = "negative" if day_pct > 0 else ("positive" if day_pct < 0 else "neutral")
    inc_tone = "positive" if inc_increased else ("negative" if inc_delta_str else "neutral")
    exp_tone = "negative" if exp_increased else ("positive" if exp_delta_str else "neutral")
    sr_tone = "positive" if sr_increased else ("negative" if sr_delta_str else "neutral")
    burn_tone = "negative" if burn_increased else ("positive" if burn_delta_str else "neutral")
    sub_delta = f"{burn_delta_str} ({active_subs_count} active)" if burn_delta_str else f"{active_subs_count} active"

    stat_strip([
        {"label": "Net worth", "value": fmt(net), "delta": None, "tone": "neutral"},
        {
            "label": "Today's spend",
            "value": fmt(today_spent),
            "delta": f"{day_pct:+.1f}%" if yesterday_spent > 0 else None,
            "tone": day_tone,
        },
        {"label": "Monthly income", "value": fmt(inc), "delta": inc_delta_str, "tone": inc_tone},
        {"label": "Monthly spend", "value": fmt(exp), "delta": exp_delta_str, "tone": exp_tone},
    ])

    # Secondary KPI Strip — Savings, EMIs & Recurring
    stat_strip([
        {"label": "Savings rate", "value": f"{savings_rate:.1f}%", "delta": sr_delta_str, "tone": sr_tone},
        {"label": "Monthly EMI", "value": fmt(total_emi_amt), "delta": f"{active_emi_count} active", "tone": "accent"},
        {
            "label": "Monthly subscriptions",
            "value": fmt(burn) if burn > 0 else "N/A",
            "delta": sub_delta,
            "tone": burn_tone,
        },
    ])

    # --- Credit Card Summary ---
    st.markdown("---")
    df_cards = dash["cards_df"]
    section_header("Credit card utilization", "Combined limit and current statement balance")
    if not df_cards.empty:
        total_limit = df_cards['card_limit'].sum()
        total_outstanding = df_cards['current_balance'].sum()
        total_available = total_limit + total_outstanding
        utilization = (-total_outstanding / total_limit * 100) if total_limit > 0 else 0
        util_tone = "negative" if utilization > 50 else ("accent" if utilization > 25 else "positive")

        stat_strip([
            {"label": "Total limit", "value": fmt(total_limit)},
            {"label": "Outstanding", "value": fmt(total_outstanding), "delta": f"{utilization:.1f}% used", "tone": util_tone},
            {"label": "Available credit", "value": fmt(total_available), "tone": "positive"},
        ])
        st.progress(max(0.0, min(1.0, utilization/100)))
    else:
        empty_state("No credit cards yet", "Add your first card in Credit Cards to track utilization here.", icon="wallet")

    # Smart Alerts Section (pre-consolidated in bulk bundle — zero N+1 queries)
    section_header("Upcoming dues & alerts", "Renewals, EMIs, loans, and bills due within 30 days")
    all_alerts = dash["all_alerts"]

    with st.container(height=400):
        if not all_alerts:
            st.success("All clear! No alerts for the next 30 days.")
        else:
            for a in all_alerts:
                days = a['days']
                amt_fmt = fmt(a['amount'])
                cat = a['category']
                
                # Use a single column for better visibility of buttons on mobile/small screens
                msg = f"{a['icon']} **{a['name']}** "
                dt = f"`{a['date']}`"
                
                c1, c2 = st.columns([0.75, 0.25])
                with c1:
                    if days <= 2:
                        st.error(f"🔴 {msg} — **DUE SOON** {dt}! ({amt_fmt})")
                    elif days <= 5:
                        st.warning(f"🟠 {msg} — in **{days} days** {dt} ({amt_fmt})")
                    elif days <= 7:
                        st.info(f"🟢 {msg} — in **{days} days** {dt} ({amt_fmt})")
                    else:
                        st.write(f"📅 {msg} — in **{days} days** {dt} ({amt_fmt})")
                
                with c2:
                    if cat == 'Subscription':
                        if st.button("Paid", key=f"btn_sub_{a['id']}", use_container_width=True):
                            FinanceService.mark_alert_actioned(a['id'], uid)
                            FinanceService.add_transaction(
                                amount=a['amount'],
                                category_id="8",
                                description=f"Auto: {a['name']}",
                                date_obj=datetime.now(),
                                txn_type="Expense",
                                user_id=uid
                            )
                            st.rerun()
                    elif cat == 'EMI':
                        if st.button("Paid", key=f"btn_cc_emi_{a['id']}", use_container_width=True):
                            CreditCardService.mark_emi_paid(a['id'])
                            st.rerun()
                    elif cat == 'Loan':
                        btn_label = "Received" if "Given" in a['name'] else "Paid"
                        if st.button(btn_label, key=f"btn_loan_{a['id']}", use_container_width=True):
                            if a.get('is_emi'):
                                LoanService.toggle_payment_status(a['id'], "pending")
                            else:
                                LoanService.update_loan_status(a['id'], 'paid')
                            st.rerun()
                    elif cat == 'Bill':
                        if st.button("Paid", key=f"btn_cc_bill_{a['id']}", use_container_width=True):
                            CreditCardService.add_transaction(uid, a['id'], a['amount'], f"Bill Payment: {a['name']}", "payment", sync_bank=True)
                            st.rerun()
            st.divider()

    st.markdown("<br>", unsafe_allow_html=True)

    # Dashboard Tabs
    t_sp, t_dy, t_ie, t_tr, t_we, t_bu = st.tabs(["Category", "Daily", "Income & Expense", "Trend", "Wealth", "Budget Burn"])
    with t_sp:
        df_sp = FinanceService.get_spending_by_category(uid, sel_year, sel_month, start_day=fiscal_start_day or 1)
        if not df_sp.empty:
            fig = px.bar(df_sp, x='Category', y='Amount', color='Category', text_auto='.2f')
            # Dynamic width with generous right & bottom margin so every bar & label stays inside the box
            chart_width = max(920, len(df_sp) * 86)
            max_sp = float(df_sp['Amount'].max()) if not df_sp.empty else 100.0
            style_plotly(fig, show_legend=False)
            fig.update_layout(
                margin=dict(t=40, b=95, l=20, r=56),
                height=440,
                width=chart_width,
                xaxis=dict(fixedrange=True, tickangle=-32, automargin=True, title=None),
                yaxis=dict(fixedrange=True, range=[0, max_sp * 1.16]),
                bargap=0.42,
            )
            fig.update_traces(textfont_color='#EAECEF', textposition='outside', cliponaxis=False, marker_cornerradius=6)
            st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})
        else: empty_state("No spending data", "Transactions for this period will appear here.", icon="chart")

    with t_dy:
        c1, c2, c3 = st.columns([1.1, 1, 1.4])
        with c1:
            if 'dy_month_mode' not in st.session_state:
                st.session_state['dy_month_mode'] = st.session_state.get('month_mode', "Calendar")

            dy_mode = st.radio(
                "Filter by:", ["Calendar", "Fiscal"],
                index=0 if st.session_state['dy_month_mode'] == "Calendar" else 1,
                horizontal=True, key="dy_month_mode_radio"
            )
            if dy_mode != st.session_state['dy_month_mode']:
                st.session_state['dy_month_mode'] = dy_mode
                st.rerun()

        with c2:
            if 'dy_sel_year' not in st.session_state:
                st.session_state['dy_sel_year'] = sel_year
            try:
                dy_year_idx = year_options.index(str(st.session_state['dy_sel_year']))
            except ValueError:
                dy_year_idx = 0
            dy_year_str = st.selectbox("Select Year", year_options, index=dy_year_idx, key="dy_year_sel")
            dy_sel_year = "All" if dy_year_str == "All" else int(dy_year_str)
            if dy_sel_year != st.session_state['dy_sel_year']:
                st.session_state['dy_sel_year'] = dy_sel_year
                st.rerun()

        with c3:
            if 'dy_sel_month' not in st.session_state:
                st.session_state['dy_sel_month'] = st.session_state.get('selected_month', "All")

            lbl_year = dy_sel_year if dy_sel_year != "All" else datetime.now().year

            if dy_mode == "Fiscal":
                dy_fiscal_day_val = int(FinanceService.get_setting('fiscal_month_start_day', '1', uid))
                month_options = ["All"]
                month_map = [None]
                for m in range(1, 13):
                    label = FinanceService.get_fiscal_month_label(lbl_year, m, dy_fiscal_day_val)
                    month_options.append(label)
                    month_map.append(m)

                try:
                    idx = month_map.index(st.session_state['dy_sel_month']) if st.session_state['dy_sel_month'] != "All" else 0
                except ValueError:
                    idx = 0

                sel_label = st.selectbox("Select Month", month_options, index=idx, key="dy_month_sel")
                dy_sel_month = "All" if sel_label == "All" else month_map[month_options.index(sel_label)]
            else:
                month_display = ["All", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                try:
                    idx = int(st.session_state['dy_sel_month']) if st.session_state['dy_sel_month'] != "All" else 0
                except ValueError:
                    idx = 0
                sel_label = st.selectbox("Select Month", month_display, index=idx, key="dy_month_sel")
                dy_sel_month = "All" if sel_label == "All" else month_display.index(sel_label)

            if dy_sel_month != st.session_state['dy_sel_month']:
                st.session_state['dy_sel_month'] = dy_sel_month
                st.rerun()

        dy_fiscal_start = int(FinanceService.get_setting('fiscal_month_start_day', '1', uid)) if dy_mode == "Fiscal" else 1
        df_dy_full = FinanceService.get_daily_spending_by_category(uid, dy_sel_year, dy_sel_month, start_day=dy_fiscal_start)
        if not df_dy_full.empty:
            # Add dynamic category filter
            all_cat_names = sorted(df_dy_full['Category'].unique().tolist())
            st.markdown("<p style='font-size: 0.9em; color: #94a3b8; margin-bottom: 5px;'>Filter by Category to see specific totals:</p>", unsafe_allow_html=True)
            sel_cats = st.multiselect("Category", all_cat_names, default=[], label_visibility="collapsed", key="dy_cat_sel")
            
            if sel_cats:
                df_dy = df_dy_full[df_dy_full['Category'].isin(sel_cats)].copy()
            else:
                df_dy = df_dy_full.copy()
            
            if not df_dy.empty:
                # Format dates as strings for cleaner categorical display
                df_dy['Date'] = pd.to_datetime(df_dy['Date']).dt.strftime('%Y-%m-%d')
                df_dy = df_dy.sort_values('Date', ascending=False)
                
                if dy_sel_year != "All" and dy_sel_month != "All":
                    start_date = datetime(int(dy_sel_year), dy_sel_month, dy_fiscal_start).date()
                    import calendar
                    if dy_mode == "Fiscal":
                        if dy_sel_month == 12:
                            end_date = datetime(int(dy_sel_year) + 1, 1, dy_fiscal_start).date() - timedelta(days=1)
                        else:
                            end_date = datetime(int(dy_sel_year), dy_sel_month + 1, dy_fiscal_start).date() - timedelta(days=1)
                    else:
                        _, last_day = calendar.monthrange(int(dy_sel_year), dy_sel_month)
                        end_date = datetime(int(dy_sel_year), dy_sel_month, last_day).date()
                    
                    full_date_range = pd.date_range(start_date, end_date).strftime('%Y-%m-%d').tolist()
                    cat_order = full_date_range[::-1]
                else:
                    cat_order = df_dy['Date'].unique().tolist()
                
                unique_days = len(cat_order)

                # Build top year/period badge + compact day-only bottom ticks (zero overlap)
                parsed_dates = [datetime.strptime(d, '%Y-%m-%d') for d in cat_order]
                years_present = sorted({d.year for d in parsed_dates})
                months_present = list(dict.fromkeys(d.strftime('%b') for d in reversed(parsed_dates)))
                if len(years_present) == 1:
                    if len(months_present) == 1:
                        period_label = f"{months_present[0]} {years_present[0]}"
                    else:
                        period_label = f"{years_present[0]} — {months_present[0]} to {months_present[-1]}"
                else:
                    period_label = f"{years_present[0]} – {years_present[-1]}"

                st.markdown(f'<div class="wf-chart-period">{period_label}</div>', unsafe_allow_html=True)

                single_month = len({(d.year, d.month) for d in parsed_dates}) == 1
                short_ticks = []
                prev_ym = None
                for d in parsed_dates:
                    ym = (d.year, d.month)
                    day_str = str(d.day)
                    if not single_month and ym != prev_ym:
                        short_ticks.append(f"{day_str}<br><span style='font-size:10px;color:#7C8798'>{d.strftime('%b')}</span>")
                    else:
                        short_ticks.append(day_str)
                    prev_ym = ym

                # Generous per-day spacing so numbers & bars breathe cleanly
                dynamic_width = max(880, unique_days * 60)
                bar_gap = 0.38

                st_colors = ['#4F86F7', '#44C786', '#F06B66', '#E8B84B', '#55B7B7', '#9B87F5', '#F2994A', '#6EC5E9', '#D97B93', '#A3B1C6']
                cat_list = list(dict.fromkeys(df_dy['Category'].tolist()))
                color_map = {cat: st_colors[i % len(st_colors)] for i, cat in enumerate(cat_list)}

                fig_dy = px.bar(
                    df_dy,
                    x='Date',
                    y='Amount',
                    color='Category',
                    title=None,
                    labels={'Amount': f'Amount ({st.session_state["sym"]})'},
                    barmode='stack',
                    color_discrete_map=color_map,
                )

                # Disable Plotly's cramped horizontal legend — render a clean wrapping HTML legend below
                style_plotly(fig_dy, show_legend=False)
                fig_dy.update_layout(
                    dragmode=False,
                    margin=dict(t=28, b=56, l=48, r=32),
                    height=390,
                    width=dynamic_width,
                    xaxis=dict(
                        type='category',
                        title=None,
                        fixedrange=True,
                        tickangle=0,
                        categoryorder='array',
                        categoryarray=cat_order,
                        tickmode='array',
                        tickvals=cat_order,
                        ticktext=short_ticks,
                        tickfont=dict(size=12, color='#B3BBC9'),
                    ),
                    yaxis=dict(fixedrange=True),
                    bargap=bar_gap,
                )
                fig_dy.update_traces(marker_cornerradius=4)

                # Add totals on top of bars
                totals = df_dy.groupby('Date')['Amount'].sum().reset_index()
                fig_dy.add_trace(go.Scatter(
                    x=totals['Date'],
                    y=totals['Amount'],
                    mode='text',
                    text=totals['Amount'].apply(lambda x: f"{x:,.0f}"),
                    textposition='top center',
                    showlegend=False,
                    hoverinfo='skip',
                    textfont=dict(family="Geist, system-ui, sans-serif", color='#CBD5E1', size=11),
                ))

                # Ensure Y-axis has room for labels
                max_y = totals['Amount'].max() if not totals.empty else 100
                fig_dy.update_yaxes(range=[0, max_y * 1.18])

                raw_html = fig_dy.to_html(include_plotlyjs="cdn", config={'displayModeBar': False}, full_html=False)
                import html as _html_esc
                legend_items_html = "".join(
                    f'<span class="wf-leg-item">'
                    f'<span class="wf-leg-dot" style="background:{color_map[c]};"></span>'
                    f'<span>{_html_esc.escape(str(c))}</span>'
                    f'</span>'
                    for c in cat_list
                )
                styled_html = f"""
                <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap">
                <style>
                    html, body {{
                        margin: 0;
                        padding: 0;
                        background: transparent;
                        color: #EAECEF;
                        font-family: 'Geist', system-ui, sans-serif;
                        overflow: hidden;
                    }}
                    .wf-dy-outer {{
                        background: #141A24;
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 16px;
                        padding: 8px 14px 14px 14px;
                        box-sizing: border-box;
                    }}
                    .wf-dy-scroll {{
                        overflow-x: auto;
                        overflow-y: hidden;
                        scroll-behavior: smooth;
                        padding-bottom: 6px;
                    }}
                    .wf-dy-scroll::-webkit-scrollbar {{ height: 6px; }}
                    .wf-dy-scroll::-webkit-scrollbar-track {{ background: transparent; border-radius: 999px; }}
                    .wf-dy-scroll::-webkit-scrollbar-thumb {{ background: rgba(148, 163, 184, 0.32); border-radius: 999px; }}
                    .wf-dy-scroll::-webkit-scrollbar-thumb:hover {{ background: rgba(148, 163, 184, 0.5); }}
                    .wf-dy-legend {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px 16px;
                        padding-top: 12px;
                        margin-top: 8px;
                        border-top: 1px solid rgba(255, 255, 255, 0.08);
                    }}
                    .wf-leg-item {{
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                        font-size: 12px;
                        color: #B3BBC9;
                        white-space: nowrap;
                    }}
                    .wf-leg-dot {{
                        width: 10px;
                        height: 10px;
                        border-radius: 3px;
                        flex-shrink: 0;
                    }}
                </style>
                <div class="wf-dy-outer">
                    <div class="wf-dy-scroll">{raw_html}</div>
                    <div class="wf-dy-legend">{legend_items_html}</div>
                </div>
                """
                # Dynamic iframe height based on legend rows so nothing clips
                legend_rows = max(1, (len(cat_list) + 6) // 7)
                components.html(styled_html, height=430 + legend_rows * 26, scrolling=False)
            else:
                empty_state("No Data", "No spending data for selected categories.")
        else: empty_state("No Data", "No daily spending data available.")

    with t_ie:
        ie_c1, ie_c2 = st.columns([1, 1])
        with ie_c1:
            if 'ie_sel_year' not in st.session_state:
                st.session_state['ie_sel_year'] = sel_year
            try:
                ie_year_idx = year_options.index(str(st.session_state['ie_sel_year']))
            except ValueError:
                ie_year_idx = 0
            ie_year_str = st.selectbox("Select Year", year_options, index=ie_year_idx, key="ie_year_sel")
            ie_sel_year = "All" if ie_year_str == "All" else int(ie_year_str)
            if ie_sel_year != st.session_state['ie_sel_year']:
                st.session_state['ie_sel_year'] = ie_sel_year
                st.rerun()

        with ie_c2:
            ie_month_display = ["All", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            if 'ie_sel_month' not in st.session_state:
                st.session_state['ie_sel_month'] = sel_month
            try:
                ie_m_idx = int(st.session_state['ie_sel_month']) if st.session_state['ie_sel_month'] != "All" else 0
            except ValueError:
                ie_m_idx = 0
            ie_m_label = st.selectbox("Select Month", ie_month_display, index=ie_m_idx, key="ie_month_sel")
            ie_sel_month = "All" if ie_m_label == "All" else ie_month_display.index(ie_m_label)
            if ie_sel_month != st.session_state['ie_sel_month']:
                st.session_state['ie_sel_month'] = ie_sel_month
                st.rerun()

        df_ie = FinanceService.get_income_expense_by_month(uid, ie_sel_year, ie_sel_month)
        if not df_ie.empty:
            # Format YYYY-MM into crisp readable month labels (e.g., "Apr 2026")
            def _fmt_ym(val):
                try:
                    return datetime.strptime(str(val), "%Y-%m").strftime("%b %Y")
                except Exception:
                    return str(val)

            ie_labels = [_fmt_ym(m) for m in df_ie['Month']]
            max_ie = float(max(df_ie['Income'].max(), df_ie['Expense'].max(), 100.0))

            fig_ie = go.Figure(data=[
                go.Bar(name='Income', x=ie_labels, y=df_ie['Income'], marker_color='#44C786', marker_cornerradius=6, text=df_ie['Income'], texttemplate='%{text:.2s}', textposition='outside', cliponaxis=False),
                go.Bar(name='Expense', x=ie_labels, y=df_ie['Expense'], marker_color='#F06B66', marker_cornerradius=6, text=df_ie['Expense'], texttemplate='%{text:.2s}', textposition='outside', cliponaxis=False)
            ])
            style_plotly(fig_ie, show_legend=True)
            fig_ie.update_layout(
                barmode='group',
                height=420,
                margin=dict(t=48, b=56, l=16, r=28),
                yaxis=dict(fixedrange=True, range=[0, max_ie * 1.18]),
                xaxis=dict(type='category', title=None, fixedrange=True, automargin=True, tickfont=dict(size=12, color='#B3BBC9')),
                legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1),
            )
            st.plotly_chart(fig_ie, use_container_width=True, config={'displayModeBar': False})
        else: empty_state("No cash flow data", "Income and expense comparisons will appear here.", icon="chart")

    with t_tr:
        df_tr = FinanceService.get_spending_trend(uid, sel_year, sel_month)
        if not df_tr.empty:
            max_tr = float(df_tr['Amount'].max()) if not df_tr.empty else 100.0
            fig_tr = px.line(df_tr, x='Month', y='Amount', markers=True, text='Amount')
            style_plotly(fig_tr, show_legend=False)
            fig_tr.update_layout(
                height=420,
                margin=dict(t=40, b=56, l=16, r=24),
                yaxis=dict(fixedrange=True, range=[0, max_tr * 1.18]),
                xaxis=dict(title=None, fixedrange=True, automargin=True, tickfont=dict(size=12, color='#B3BBC9')),
            )
            fig_tr.update_traces(line_color='#4F86F7', line_width=2.5, marker=dict(size=7), textposition='top center', texttemplate='%{text:.2s}', cliponaxis=False)
            st.plotly_chart(fig_tr, use_container_width=True, config={'displayModeBar': False})
        else: empty_state("No trend data", "Monthly spending trend will appear here.", icon="chart")

    with t_we:
        section_header("Wealth distribution", "Asset allocation across tracked holdings")
        asset_data = dash["asset_data"]

        # 2. Convert to DataFrame for plotting (excluding Cash & Bank as requested)
        if asset_data:
            wealth_df = pd.DataFrame(asset_data).sort_values(by='Amount', ascending=False)

            # Bar chart for wealth distribution
            fig3 = px.bar(
                wealth_df,
                x='Category',
                y='Amount',
                color='Category',
                text_auto='.2f',
                color_discrete_sequence=['#4F86F7', '#44C786', '#E8B84B', '#7B93DB', '#55B7B7', '#D97B76']
            )
            style_plotly(fig3, show_legend=False)
            fig3.update_layout(
                margin=dict(t=30, b=20, l=0, r=0),
                yaxis=dict(title="Amount", fixedrange=True),
                xaxis=dict(title=None, fixedrange=True),
            )
            fig3.update_traces(textfont_color='#EAECEF', textposition='outside', marker_cornerradius=6)
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        else:
            empty_state("No assets tracked", "Add your investments in Assets to see your allocation here.", icon="wallet")

    with t_bu:
        budget_month = sel_month if sel_month != "All" else None
        budget_year = sel_year if sel_year != "All" else None
        df_b = BudgetService.get_monthly_budgets(uid, month=budget_month, year=budget_year)
        limit = df_b['Limit'].sum() if not df_b.empty else 0
        if limit > 0:
            fig4 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=exp,
                gauge={
                    'axis': {'range': [None, limit]},
                    'bar': {'color': '#4F86F7'},
                    'bgcolor': '#1A2130',
                    'borderwidth': 0,
                }
            ))
            style_plotly(fig4, show_legend=False)
            st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})
        else: empty_state("No budgets set", "Create monthly limits in Budgets to track burn rate.", icon="chart")

elif page == "Transactions":
    st.markdown('<h1 class="main-header">Ledger</h1>', unsafe_allow_html=True)
    if st.session_state.get('txn_deleted'):
        st.toast("Transaction revoked and balance restored.", icon=":material/check_circle:")
        st.info("Transaction revoked and balance restored.")
        st.session_state['txn_deleted'] = False

    t1, t2 = st.tabs(["Add entry", "History"])

    @st.fragment
    def _render_add_txn_fragment():
        if 'txn_form_v' not in st.session_state:
            st.session_state['txn_form_v'] = 0

        # Show confirmation popup + top banner (never at the bottom)
        logged_msg = st.session_state.pop('txn_logged_msg', None)
        if logged_msg:
            st.toast(logged_msg, icon=":material/check_circle:")
            st.success(logged_msg)

        v = st.session_state['txn_form_v']
        txn_type = st.radio("Type", ["Expense", "Income"], horizontal=True, key="txn_type_toggle")
        all_cats = FinanceService.get_categories(uid)
        filtered = all_cats[all_cats['type'] == txn_type]
        cat_opts = {f"{r['icon']} {r['name']}": r['id'] for _, r in filtered.iterrows()}

        with st.form(f"add_txn_pro_{v}"):
            amt = st.number_input("Amount", min_value=0.0, step=1.0, value=0.0, key=f"txn_amt_{v}")
            dt = st.date_input("Date", value=datetime.now().date(), key=f"txn_dt_{v}")
            cat_sel = st.selectbox("Category", list(cat_opts.keys()) if cat_opts else ["-"], index=0, key=f"txn_cat_{v}")
            desc = st.text_input("Description", value="", placeholder="What was this for?", key=f"txn_desc_{v}")
            if st.form_submit_button("Record Transaction", use_container_width=True, type="primary"):
                if amt is None or amt <= 0:
                    st.error("Please enter an amount greater than 0.")
                elif cat_sel == "-":
                    st.error("Please select a category.")
                else:
                    full_dt = datetime.combine(dt, datetime.now().time())
                    FinanceService.add_transaction(amt, cat_opts[cat_sel], desc.strip(), full_dt, txn_type, uid)
                    st.session_state['txn_form_v'] = v + 1
                    st.session_state['txn_logged_msg'] = f"Transaction logged: {fmt(amt)} ({cat_sel})"
                    st.rerun(scope="fragment")

    with t1:
        _render_add_txn_fragment()

    with t2:
        # Transaction Filters
        st.markdown("#### 🔍 Filter History")
        
        f_search, f_cat = st.columns(2)
        with f_search:
            sel_desc = st.text_input("Search Notes/Description", key="hist_desc")
        with f_cat:
            all_cats_df = FinanceService.get_categories(uid)
            cat_opts = ["All"] + list(all_cats_df['name'].unique()) if not all_cats_df.empty else ["All"]
            sel_cat = st.selectbox("Category", cat_opts, key="hist_cat")
            
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            y_opts = ["All"] + [str(y) for y in FinanceService.get_available_years(uid)]
            sel_y = st.selectbox("Year", y_opts, key="hist_year")
        with f2:
            m_opts = ["All"] + [str(i) for i in range(1, 13)]
            sel_m = st.selectbox("Month", m_opts, key="hist_month")
        with f3:
            d_opts = ["All"] + [str(i) for i in range(1, 32)]
            sel_d = st.selectbox("Day", d_opts, key="hist_day")
        with f4:
            t_opts = ["All", "Expense", "Income"]
            sel_t = st.selectbox("Type", t_opts, key="hist_type")
            
        st.divider()
        
        df_hist = FinanceService.get_filtered_transactions(
            uid, year=sel_y, month=sel_m, day=sel_d, txn_type=sel_t, 
            description_search=sel_desc, category_name=sel_cat, limit=100
        )
        if not df_hist.empty:
            for _, row in df_hist.iterrows():
                c1, c2, c3 = st.columns([1, 4, 1])
                with c1: st.markdown(f"### {row['Icon']}")
                with c2:
                    st.markdown(f"**{row['Description']}**")
                    color = "#f87171" if row['Type'] == 'Expense' else "#4ade80"
                    sign = "-" if row['Type'] == 'Expense' else "+"
                    st.markdown(f"<span style='color:{color}; font-weight:bold;'>{sign}{fmt(row['Amount'])}</span> • {row['Category']} • {row['Date']}", unsafe_allow_html=True)
                with c3:
                    if st.button("", icon=":material/delete_outline:", help="Delete transaction", key=f"del_txn_{row['ID']}_{row['Source']}"):
                        if row['Source'] == 'main':
                            FinanceService.delete_transaction(row['ID'], uid)
                            st.session_state['txn_deleted'] = True
                        else:
                            CreditCardService.delete_transaction(row['ID'], uid)
                            st.session_state['card_txn_deleted'] = True
                        st.rerun()
                st.divider()
        else: empty_state("No History", "Log transactions to see them here.")

elif page == "Budgets":
    st.markdown('<h1 class="main-header">Guardrails</h1>', unsafe_allow_html=True)
    if st.session_state.get('budget_added'):
        st.success("Budget added!")
        st.session_state['budget_added'] = False
    with st.expander("➕ Set New Budget"):
        with st.form("new_budget"):
            all_cats = FinanceService.get_categories(uid)
            exp_cats = all_cats[all_cats['type'] == 'Expense']
            cat_opts = {f"{r['icon']} {r['name']}": r['id'] for _, r in exp_cats.iterrows()}
            sel_cat = st.selectbox("Category", list(cat_opts.keys()))
            limit = st.number_input("Monthly Limit", min_value=0.01, value=None, placeholder="Enter limit")
            if st.form_submit_button("Lock Budget"):
                BudgetService.add_budget(uid, cat_opts[sel_cat], limit, datetime.now().month, datetime.now().year)
                st.session_state['budget_added'] = True
                st.rerun()
    df_b = BudgetService.get_monthly_budgets(uid)
    if not df_b.empty:
        for _, row in df_b.iterrows():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{row['Category']}**")
                st.progress(min(1.0, row['Progress']))
                st.caption(f"{fmt(row['Spent'])} of {fmt(row['Limit'])}")
            with c2:
                render_delete_button(row['id'], f"del_{row['id']}", BudgetService.delete_budget, uid, "this budget")
    else: empty_state("No Budgets", "Track your spending.")

elif page == "Subscriptions":
    st.markdown('<h1 class="main-header">Recurring Bills</h1>', unsafe_allow_html=True)
    if st.session_state.get('sub_added'):
        st.success("Subscription added!")
        st.session_state['sub_added'] = False
    with st.expander("➕ Add Subscription"):
        name = st.text_input("Service Name")
        cost = st.number_input("Amount", min_value=0.01, value=None, placeholder="Enter amount")
        icon = st.text_input("Emoji Icon", value="💳")
        cycle = st.selectbox("Cycle", ["Monthly", "Quarterly", "6 Months", "Yearly", "Custom"])
        custom_months = None
        if cycle == "Custom":
            custom_months = st.number_input("Custom Months", min_value=1, value=3, step=1)
        start = st.date_input("Start Date")
        if st.button("Track Bill", type="primary", use_container_width=True):
            if not name or cost is None:
                st.error("Please provide name and amount.")
            else:
                final_cycle = f"Custom:{custom_months}" if cycle == "Custom" else cycle
                RecurringService.add_subscription(uid, name, cost, final_cycle, start, icon)
                st.session_state['sub_added'] = True
                st.rerun()
    df_s = RecurringService.get_subscriptions(uid)
    if not df_s.empty:
        for _, row in df_s.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            with c1:
                st.markdown(f"**{str(row['Icon']).strip()} {str(row['Name']).strip()}**")
                cycle_display = RecurringService.format_cycle(row['Cycle'])
                if row['Next Date']:
                    st.caption(f"🔄 {cycle_display} • Renews on {row['Next Date']}")
            with c2: st.markdown(f"**{fmt(row['Amount'])}**")
            with c3: st.caption(f"**{cycle_display}**")
            with c4:
                render_delete_button(row['id'], f"sdel_{row['id']}", RecurringService.delete_subscription, uid, row['Name'])
            st.divider()

elif page == "Loans":
    st.markdown('<h1 class="main-header">Loans Tracker</h1>', unsafe_allow_html=True)

    # Edit mode    # Summary
    loans_all = LoanService.get_loans(uid)
    if not loans_all.empty:
        # Only show metrics for non-paid loans for clarity
        active_loans = loans_all[loans_all['status'] != 'paid']
        total_outstanding = active_loans['remaining_amount'].sum()
        total_emi = active_loans[active_loans['emi_active'] == 1]['emi_amount'].sum()
        total_given = active_loans[active_loans['loan_type'] == 'given']['amount'].sum()
        total_taken = active_loans[active_loans['loan_type'] == 'taken']['amount'].sum()
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1: st.metric("Total Given", fmt(total_given))
        with c2: st.metric("Total Taken", fmt(total_taken))
        with c3: st.metric("Outstanding", fmt(total_outstanding))
        with c4: st.metric("Monthly EMI", fmt(total_emi))


    if st.session_state.get('edit_loan_id'):
        loan = LoanService.get_loan_by_id(st.session_state['edit_loan_id'])
        if loan:
            st.markdown("### ✏️ Edit Loan")
            with st.form("edit_loan_form"):
                person = st.text_input("Person/Lender Name", value=loan[1])
                amount = st.number_input("Original Amount", min_value=0.01, value=float(loan[2]))
                interest = st.number_input("Interest Rate (%)", min_value=0.0, value=float(loan[4]))
                start = st.date_input("Start Date", value=datetime.strptime(loan[5], "%Y-%m-%d").date() if loan[5] else datetime.now().date())
                due = st.date_input("Due Date", value=datetime.strptime(loan[6], "%Y-%m-%d").date() if loan[6] else datetime.now().date())
                emi_amt = st.number_input("EMI Amount", min_value=0.0, value=float(loan[7]))
                emi_active = st.checkbox("Has EMI", value=bool(loan[8]))
                tenure = st.number_input("Tenure (Months)", min_value=0, value=int(loan[9] or 0))
                emi_start = st.date_input("EMI Start Date", value=datetime.strptime(loan[10], "%Y-%m-%d").date() if loan[10] else datetime.now().date())
                notes = st.text_area("Notes", value=loan[13] if loan[13] else "")
                if st.form_submit_button("Update Loan"):
                    LoanService.update_loan(st.session_state['edit_loan_id'], person, amount, interest, start, due, emi_amt, emi_active, tenure, emi_start)
                    st.session_state['edit_loan_id'] = None
                    st.rerun()
            if st.button("Cancel"):
                st.session_state['edit_loan_id'] = None
                st.rerun()
            st.stop()

    tab1, tab2 = st.tabs(["💸 Loans Given", "💳 Loans Taken"])

    with tab1:
        # Use version in key to force collapse on success
        with st.expander("➕ Add Loan Given", expanded=False, key=f"exp_given_{st.session_state['loan_given_version']}"):
            emi_active = st.checkbox("Has EMI", key="new_loan_given_emi_active", value=False)
            with st.form("new_loan_given", clear_on_submit=True):
                person = st.text_input("Person Name")
                
                if emi_active:
                    emi_mode = st.radio("EMI Mode", ["Per Month (Auto Total)", "Total Amount (Auto EMI)"], horizontal=True)
                    tenure = st.number_input("Tenure (Months)", min_value=1, value=12)
                    if emi_mode == "Per Month (Auto Total)":
                        emi_amt = st.number_input("Monthly EMI", min_value=0.01, value=100.0)
                        amount = 0 # Calculated
                    else:
                        amount = st.number_input("Total Amount", min_value=0.01, value=None)
                        emi_amt = 0 # Calculated
                    
                    emi_start = st.date_input("EMI Start Date")
                    interest = 0.0
                    start = None
                    due = None
                else:
                    amount = st.number_input("Amount", min_value=0.01, value=None, placeholder="Loan amount")
                    interest = st.number_input("Interest Rate (%)", min_value=0.0, value=0.0)
                    start = st.date_input("Start Date")
                    due = st.date_input("Due Date")
                    tenure = 0
                    emi_amt = 0.0
                    emi_start = None
                
                notes = st.text_area("Notes")
                if st.form_submit_button("Add Loan"):
                    if emi_active:
                        if emi_mode == "Per Month (Auto Total)":
                            amount = emi_amt * tenure
                        else:
                            emi_amt = amount / tenure
                    
                    LoanService.add_loan(uid, person, amount, 'given', interest, start, due, emi_amt, emi_active, tenure, emi_start, notes)
                    st.session_state['loan_added'] = True
                    st.session_state['loan_given_version'] += 1
                    st.rerun()

        loans = LoanService.get_loans(uid, 'given')
        # Debug
        # st.write(f"DEBUG: Found {len(loans)} loans given")
        if not loans.empty:
            for _, row in loans.iterrows():
                st.markdown(f"**{row['person_name']}** — {fmt(row['amount'])}")
                remaining_txt = f" | {row['remaining_tenure']}/{row['tenure']} Remaining" if row['emi_active'] else ""
                st.caption(f"Due: {row['due_date']} | Status: {row['status']} | Remaining: {fmt(row['remaining_amount'])}{remaining_txt}")
                if row['emi_active']:
                    st.caption(f"EMI: {fmt(row['emi_amount'])}/month | Tenure: {row['tenure']} months")
                
                # Payment Schedule
                payments = LoanService.get_loan_payments(row['id'])
                if not payments.empty:
                    with st.expander("📅 View Payment Schedule", expanded=False):
                        cols = st.columns(3)
                        for i, (idx, p) in enumerate(payments.iterrows()):
                            with cols[i % 3]:
                                is_paid = (p['status'] == 'paid')
                                label = f"{p['due_date']}"
                                if st.checkbox(label, value=is_paid, key=f"pay_chk_{p['id']}"):
                                    if not is_paid:
                                        LoanService.toggle_payment_status(p['id'], p['status'])
                                        st.rerun()
                                elif is_paid:
                                    LoanService.toggle_payment_status(p['id'], p['status'])
                                    st.rerun()
                
                c_edit, c_del = st.columns([1, 1])
                with c_edit:
                    if st.button("✏️ Edit", key=f"edit_g_{row['id']}", use_container_width=True):
                        st.session_state['edit_loan_id'] = row['id']
                        st.rerun()
                with c_del:
                    render_delete_button(row['id'], f"ldel_g_{row['id']}", LoanService.delete_loan, uid, row['person_name'])
                st.divider()
        else:
            empty_state("No Loans Given", "Lend money to track here.")

    with tab2:
        with st.expander("➕ Add Loan Taken", expanded=False, key=f"exp_taken_{st.session_state['loan_taken_version']}"):
            emi_active_t = st.checkbox("Has EMI", key="new_loan_taken_emi_active", value=False)
            with st.form("new_loan_taken", clear_on_submit=True):
                person = st.text_input("Lender Name")

                if emi_active_t:
                    emi_mode_t = st.radio("EMI Mode", ["Per Month (Auto Total)", "Total Amount (Auto EMI)"], horizontal=True, key="emi_mode_t")
                    tenure_t = st.number_input("Tenure (Months)", min_value=1, value=12)
                    if emi_mode_t == "Per Month (Auto Total)":
                        emi_amt_t = st.number_input("Monthly EMI", min_value=0.01, value=100.0)
                        amount_t = 0
                    else:
                        amount_t = st.number_input("Total Amount", min_value=0.01, value=None)
                        emi_amt_t = 0
                    
                    emi_start_t = st.date_input("EMI Start Date")
                    interest_t = 0.0
                    start_t = None
                    due_t = None
                else:
                    amount_t = st.number_input("Amount", min_value=0.01, value=None, placeholder="Loan amount")
                    interest_t = st.number_input("Interest Rate (%)", min_value=0.0, value=0.0)
                    start_t = st.date_input("Start Date")
                    due_t = st.date_input("Due Date")
                    tenure_t = 0
                    emi_amt_t = 0.0
                    emi_start_t = None

                notes = st.text_area("Notes")
                if st.form_submit_button("Add Loan"):
                    if emi_active_t:
                        if emi_mode_t == "Per Month (Auto Total)":
                            amount_t = emi_amt_t * tenure_t
                        else:
                            emi_amt_t = amount_t / tenure_t
                    
                    LoanService.add_loan(uid, person, amount_t, 'taken', interest_t, start_t, due_t, emi_amt_t, emi_active_t, tenure_t, emi_start_t, notes)
                    st.session_state['loan_added'] = True
                    st.session_state['loan_taken_version'] += 1
                    st.rerun()

        loans = LoanService.get_loans(uid, 'taken')
        # st.write(f"DEBUG: Found {len(loans)} loans taken")
        if not loans.empty:
            for _, row in loans.iterrows():
                st.markdown(f"**{row['person_name']}** — {fmt(row['amount'])}")
                remaining_txt = f" | {row['remaining_tenure']}/{row['tenure']} Remaining" if row['emi_active'] else ""
                st.caption(f"Due: {row['due_date']} | Status: {row['status']} | Remaining: {fmt(row['remaining_amount'])}{remaining_txt}")
                if row['emi_active']:
                    st.caption(f"EMI: {fmt(row['emi_amount'])}/month | Tenure: {row['tenure']} months")

                # Payment Schedule
                payments = LoanService.get_loan_payments(row['id'])
                if not payments.empty:
                    with st.expander("📅 View Payment Schedule", expanded=False):
                        cols = st.columns(3)
                        for i, (idx, p) in enumerate(payments.iterrows()):
                            with cols[i % 3]:
                                is_paid = (p['status'] == 'paid')
                                label = f"{p['due_date']}"
                                if st.checkbox(label, value=is_paid, key=f"pay_chk_t_{p['id']}"):
                                    if not is_paid:
                                        LoanService.toggle_payment_status(p['id'], p['status'])
                                        st.rerun()
                                elif is_paid:
                                    LoanService.toggle_payment_status(p['id'], p['status'])
                                    st.rerun()

                c_edit, c_del = st.columns([1, 1])
                with c_edit:
                    if st.button("✏️ Edit", key=f"edit_t_{row['id']}", use_container_width=True):
                        st.session_state['edit_loan_id'] = row['id']
                        st.rerun()
                with c_del:
                    render_delete_button(row['id'], f"ldel_t_{row['id']}", LoanService.delete_loan, uid, row['person_name'])
                st.divider()
        else:
            empty_state("No Loans Taken", "Borrow money to track here.")

    # Success Popups centered
    if st.session_state.get('loan_added') or st.session_state.get('loan_deleted') or st.session_state.get('loan_payment_added'):
        st.markdown('<div class="center-popup">', unsafe_allow_html=True)
        if st.session_state.get('loan_added'):
            st.success("Loan added!")
            st.session_state['loan_added'] = False
        if st.session_state.get('loan_deleted'):
            st.info("Loan removed.")
            st.session_state['loan_deleted'] = False
        if st.session_state.get('loan_payment_added'):
            st.success("Payment recorded!")
            st.session_state['loan_payment_added'] = False
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Credit Cards":
    st.markdown('<h1 class="main-header">Credit Card Tracker</h1>', unsafe_allow_html=True)

    if st.session_state.get('card_added'):
        st.success("Card added!")
        st.session_state['card_added'] = False
    if st.session_state.get('card_txn_added'):
        st.success("Transaction recorded!")
        st.session_state['card_txn_added'] = False

    # Edit mode    # Summary
    df_cards = CreditCardService.get_cards(uid)
    if not df_cards.empty:
        total_limit = df_cards['card_limit'].sum()
        total_outstanding = df_cards['current_balance'].sum()
        utilization = (total_outstanding / total_limit * 100) if total_limit > 0 else 0
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: st.metric("Total Limit", fmt(total_limit))
        with c2: st.metric("Total Outstanding", fmt(total_outstanding))
        with c3: st.metric("Utilization", f"{utilization:.1f}%")


    if st.session_state.get('edit_card_id'):
        card = CreditCardService.get_card_by_id(st.session_state['edit_card_id'])
        if card:
            st.markdown("### ✏️ Edit Card")
            with st.form("edit_card_form"):
                cname = st.text_input("Card Name", value=card[1])
                cbank = st.text_input("Bank Name", value=card[2])
                climit = st.number_input("Credit Limit", min_value=0.01, value=float(card[3] or 0.01))
                cbill_day = st.number_input("Billing Date", min_value=1, max_value=31, value=int(card[4] or 1))
                cclose_day = st.number_input("Closing Date", min_value=1, max_value=31, value=int(card[5] or 1))
                if st.form_submit_button("Update Card"):
                    CreditCardService.update_card(st.session_state['edit_card_id'], cname, cbank, climit, cbill_day, cclose_day)
                    st.session_state['edit_card_id'] = None
                    st.rerun()
            if st.button("Cancel"):
                st.session_state['edit_card_id'] = None
                st.rerun()
            st.stop()


    # Upcoming bills alert
    upcoming = CreditCardService.get_upcoming_bills(uid, 15)
    if upcoming:
        st.markdown("### 🔔 Upcoming Bills")
        for bill in upcoming:
            st.warning(f"**{bill['name']}** ({bill['bank']}) — bill due in **{bill['days_left']} days** | Outstanding: {fmt(bill['balance'])}")

    # Add Credit Card form
    with st.expander("➕ Add Credit Card", expanded=False, key=f"exp_card_{st.session_state['card_add_version']}"):
        with st.form("new_card", clear_on_submit=True):
            cname = st.text_input("Card Name (e.g. HDFC Regalia)")
            cbank = st.text_input("Bank")
            climit = st.number_input("Limit", min_value=0.0)
            cbilling = st.number_input("Billing Day (1-31)", min_value=1, max_value=31, value=15)
            cclosing = st.number_input("Closing Day (1-31)", min_value=1, max_value=31, value=1)
            if st.form_submit_button("Add Card"):
                CreditCardService.add_card(uid, cname, cbank, climit, cbilling, cclosing)
                st.session_state['card_added'] = True
                st.session_state['card_add_version'] += 1
                st.rerun()
    df_cards = CreditCardService.get_cards(uid)
    if not df_cards.empty:
        for _, card in df_cards.iterrows():
            with st.expander(f"{card['name']} — {card['bank']}"):
                c1, c2, c3, c4, c5 = st.columns([2, 1, 0.5, 0.5, 0.5])
                with c1:
                    limit_val = card['card_limit'] if card['card_limit'] is not None else 0.0
                    total_out = CreditCardService.get_card_total_outstanding(card['id'])
                    avail = CreditCardService.get_card_available_limit(card['id'])
                    
                    st.markdown(f"**Limit:** {fmt(limit_val)}")
                    st.markdown(f"<span style='color:#f87171;'>**Outstanding:** {fmt(total_out)}</span>", unsafe_allow_html=True)
                    
                    color = "#4ade80" if avail > 0 else "#f87171"
                    st.markdown(f"<span style='color:{color};'>**Available:** {fmt(avail)}</span>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"**Billing Day:** {card['billing_date']}")
                with c3:
                    if st.button("✏️", key=f"edit_card_{card['id']}"):
                        st.session_state['edit_card_id'] = card['id']
                        st.rerun()
                with c4:
                    if st.button("🔄", key=f"sync_card_{card['id']}", help="Sync Balance"):
                        CreditCardService.sync_card_balance(card['id'])
                        st.rerun()
                with c5:
                    render_delete_button(card['id'], f"cdel_{card['id']}", CreditCardService.delete_card, uid, card['name'])

                # Add transaction form
                st.markdown("**Transactions & EMIs**")
                unlink_cc_val = FinanceService.get_setting('cc_unlink_transactions', 'False', uid) == 'True'
                
                if unlink_cc_val:
                    # Only show EMI tab
                    txn_tab3 = st.tabs(["➕ Add EMI"])[0]
                else:
                    txn_tab1, txn_tab2, txn_tab3 = st.tabs(["➕ Add Expense", "➕ Add Payment", "➕ Add EMI"])
                    with txn_tab1:
                        with st.form(f"card_exp_{card['id']}", clear_on_submit=True):
                            exp_desc = st.text_input("Description", key=f"exp_desc_{card['id']}")
                            exp_amt = st.number_input("Amount", min_value=0.01, value=None, key=f"exp_amt_{card['id']}")
                            exp_date = st.date_input("Date", value=datetime.now().date(), key=f"exp_date_{card['id']}")
                            if st.form_submit_button("Record Expense"):
                                if exp_amt and exp_amt > 0:
                                    full_dt = datetime.combine(exp_date, datetime.now().time()).strftime("%Y-%m-%d %H:%M")
                                    CreditCardService.add_transaction(uid, card['id'], exp_amt, exp_desc, 'expense', txn_date=full_dt)
                                    st.session_state['card_txn_added'] = True
                                    st.rerun()
                    with txn_tab2:
                        with st.form(f"card_pay_{card['id']}", clear_on_submit=True):
                            pay_desc = st.text_input("Description", key=f"pay_desc_{card['id']}")
                            pay_amt = st.number_input("Amount", min_value=0.01, value=None, key=f"pay_amt_{card['id']}")
                            pay_date = st.date_input("Date", value=datetime.now().date(), key=f"pay_date_{card['id']}")
                            sync_bank = st.checkbox("Deduct from Main Bank Account", value=True, key=f"sync_bank_{card['id']}")
                            if st.form_submit_button("Record Payment"):
                                if pay_amt and pay_amt > 0:
                                    full_dt = datetime.combine(pay_date, datetime.now().time()).strftime("%Y-%m-%d %H:%M")
                                    CreditCardService.add_transaction(uid, card['id'], pay_amt, pay_desc, 'payment', txn_date=full_dt, sync_bank=sync_bank)
                                    st.session_state['card_txn_added'] = True
                                    st.rerun()
                
                with txn_tab3:
                    with st.form(f"card_emi_{card['id']}", clear_on_submit=True):
                        emi_desc = st.text_input("EMI Description", placeholder="e.g. iPhone 15 Pro", key=f"emi_desc_{card['id']}")
                        emi_total = st.number_input("Total Amount", min_value=0.01, value=None, key=f"emi_total_{card['id']}")
                        emi_monthly = st.number_input("Monthly Installment", min_value=0.01, value=None, key=f"emi_monthly_{card['id']}")
                        emi_tenure = st.number_input("Tenure (Months)", min_value=1, step=1, value=None, key=f"emi_tenure_{card['id']}")
                        emi_date = st.date_input("Start Date", value=datetime.now().date(), key=f"emi_start_{card['id']}")
                        if st.form_submit_button("Start EMI Plan"):
                            if emi_total and emi_monthly and emi_tenure:
                                CreditCardService.add_emi(uid, card['id'], emi_desc, emi_total, emi_monthly, emi_tenure, str(emi_date))
                                st.session_state['card_txn_added'] = True
                                st.rerun()

                # List active EMIs
                df_emis = CreditCardService.get_card_emis(card['id'])
                if not df_emis.empty:
                    st.markdown("### 🗓️ Active EMIs")
                    for _, emi in df_emis.iterrows():
                        with st.expander(f"📌 {emi['Description']} ({fmt(emi['Monthly'])}/mo) — {emi['Remaining']}/{emi['Tenure']} Remaining"):
                            ec1, ec2 = st.columns([3, 1])
                            with ec1:
                                st.write(f"Total: **{fmt(emi['Total'])}** | Tenure: **{emi['Tenure']} months**")
                            with ec2:
                                if st.button("🗑️ Revoke EMI", key=f"del_emi_{emi['id']}"):
                                    CreditCardService.delete_emi(emi['id'])
                                    st.rerun()
                            
                            # Show payments
                            df_p = CreditCardService.get_emi_payments(emi['id'])
                            if not df_p.empty:
                                for _, p in df_p.iterrows():
                                    pc1, pc2, pc3 = st.columns([2, 2, 1])
                                    with pc1: st.write(p['Date'])
                                    with pc2: 
                                        st.write(fmt(p['Amount']))
                                        if p['Status'] == 'paid':
                                            st.caption(f"✅ Paid on {p['Paid Date']}")
                                    with pc3:
                                        if p['Status'] == 'pending':
                                            if st.button("Mark Paid", key=f"pay_emi_p_{p['id']}"):
                                                CreditCardService.mark_emi_paid(p['id'])
                                                st.rerun()
                                    st.divider()

                # List recent transactions
                df_txns = CreditCardService.get_card_transactions(card['id'])
                if df_txns.empty:
                    st.info("No transactions yet.")
                else:
                    for _, row in df_txns.iterrows():
                        c1, c2, c3 = st.columns([4, 2, 1])
                        with c1:
                            st.markdown(f"**{row['description']}**")
                            st.caption(f"{row['date']}")
                        with c2:
                            color = "#f87171" if row['txn_type'] == 'expense' else "#4ade80"
                            sign = "-" if row['txn_type'] == 'expense' else "+"
                            st.markdown(f"<span style='color:{color}; font-weight:bold;'>{sign}{fmt(row['amount'])}</span>", unsafe_allow_html=True)
                        with c3:
                            # Direct confirmation for CC transactions for reliability
                            btn_key = f"del_c_txn_{row['id']}"
                            conf_key = f"conf_del_{row['id']}"
                            
                            if conf_key not in st.session_state:
                                st.session_state[conf_key] = False
                                
                            if not st.session_state[conf_key]:
                                if st.button("🗑️", key=btn_key):
                                    st.session_state[conf_key] = True
                                    st.rerun()
                            else:
                                st.markdown("🗑️ **Delete?**")
                                cy, cn = st.columns(2)
                                with cy:
                                    if st.button("✅", key=f"y_{row['id']}", help="Confirm Delete"):
                                        CreditCardService.delete_transaction(row['id'], uid, description=row['description'], amount=row['amount'])
                                        st.session_state[conf_key] = False
                                        st.session_state['card_txn_deleted'] = True
                                        st.rerun()
                                with cn:
                                    if st.button("❌", key=f"n_{row['id']}", help="Cancel"):
                                        st.session_state[conf_key] = False
                                        st.rerun()
                        st.divider()
    else:
        empty_state("No Credit Cards", "Add your first credit card to start tracking.")

    # Success Popups centered
    if st.session_state.get('card_added') or st.session_state.get('card_deleted') or st.session_state.get('card_txn_added') or st.session_state.get('card_txn_deleted'):
        st.markdown('<div class="center-popup">', unsafe_allow_html=True)
        if st.session_state.get('card_added'):
            st.success("Credit Card added!")
            st.session_state['card_added'] = False
        if st.session_state.get('card_deleted'):
            st.info("Credit Card removed.")
            st.session_state['card_deleted'] = False
        if st.session_state.get('card_txn_added'):
            st.success("Transaction recorded!")
            st.session_state['card_txn_added'] = False
        if st.session_state.get('card_txn_deleted'):
            st.info("Transaction revoked.")
            st.session_state['card_txn_deleted'] = False
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Goals":
    st.markdown('<h1 class="main-header">Piggy Bank</h1>', unsafe_allow_html=True)
    if st.session_state.get('goal_added'):
        st.success("Goal created!")
        st.session_state['goal_added'] = False
    with st.expander("➕ Create New Goal"):
        with st.form("new_goal"):
            gname = st.text_input("Saving for…")
            target = st.number_input("Target Amount", min_value=0.01, value=None, placeholder="Enter target")
            deadline = st.date_input("Target Date")
            icon = st.text_input("Emoji Logo", value="🎯")
            if st.form_submit_button("Create Goal"):
                GoalService.add_goal(uid, gname, target, deadline, icon)
                st.session_state['goal_added'] = True
                st.rerun()
    df_g = GoalService.get_goals(uid)
    if not df_g.empty:
        for _, row in df_g.iterrows():
            st.markdown(f"### {row['Icon']} {row['Name']}")
            prog = min(1.0, row['Current'] / row['Target']) if row['Target'] > 0 else 0
            st.progress(prog)
            st.write(f"Saved: **{fmt(row['Current'])}** / {fmt(row['Target'])}")
            gc1, gc2, gc3 = st.columns([2, 1, 1])
            with gc1: add_val = st.number_input("Add", min_value=0.01, value=None, placeholder="Amount", key=f"add_{row['id']}")
            with gc2:
                if st.button("💰 Save", key=f"btn_{row['id']}"):
                    if add_val and add_val > 0:
                        GoalService.contribute(row['id'], add_val)
                        st.rerun()
                    else:
                        st.warning("Enter a valid amount")
            with gc3:
                render_delete_button(row['id'], f"gdel_{row['id']}", GoalService.delete_goal, uid, row['Name'])
            st.divider()

elif page == "Assets":
    st.markdown('<h1 class="main-header">Wealth Portfolio</h1>', unsafe_allow_html=True)
    if st.session_state.get('asset_added'):
        st.success("Asset added!")
        st.session_state['asset_added'] = False
    if st.session_state['edit_asset_id']:
        df_a = AssetService.get_assets(uid)
        asset_to_edit = df_a[df_a['id'] == st.session_state['edit_asset_id']].iloc[0]
        with st.form("edit_asset_form"):
            en_name = st.text_input("Name", value=asset_to_edit['Name'])
            en_type = st.selectbox("Type", ASSET_TYPES,
                                  index=ASSET_TYPES.index(asset_to_edit['Type']))
            en_val = st.number_input("Value", min_value=0.01, value=float(asset_to_edit['Value']))
            if st.form_submit_button("Update Asset"):
                AssetService.update_asset(st.session_state['edit_asset_id'], en_name, en_type, en_val)
                st.session_state['edit_asset_id'] = None
                st.rerun()
            if st.form_submit_button("Cancel"):
                st.session_state['edit_asset_id'] = None
                st.rerun()
    else:
        with st.expander("➕ Add Asset"):
            with st.form("new_asset"):
                aname = st.text_input("Asset Name")
                atype = st.selectbox("Type", ASSET_TYPES)
                aval = st.number_input("Current Value", min_value=0.01, value=None, placeholder="Enter value")
                if st.form_submit_button("Add Asset"):
                    AssetService.add_asset(aname, atype, aval, uid)
                    st.session_state['asset_added'] = True
                    st.rerun()
    df_a = AssetService.get_assets(uid)
    if not df_a.empty:
        for _, row in df_a.iterrows():
            ac1, ac2, ac3, ac4 = st.columns([3, 2, 1, 1])
            with ac1: st.markdown(f"**{row['Name']}**")
            with ac2: st.markdown(f"**{fmt(row['Value'])}**")
            with ac3:
                if st.button("📝", key=f"edit_{row['id']}"):
                    st.session_state['edit_asset_id'] = row['id']
                    st.rerun()
            with ac4:
                render_delete_button(row['id'], f"adel_{row['id']}", AssetService.delete_asset, uid, row['Name'])
            st.divider()

elif page == "TripFlow":
    st.markdown('<h1 class="main-header">TripFlow</h1>', unsafe_allow_html=True)

    # Top-level trip creation/deletion popups
    if st.session_state.get('trip_added'):
        st.toast("Trip created successfully!", icon=":material/check_circle:")
        st.success("Trip created successfully!")
        st.session_state['trip_added'] = False
    if st.session_state.get('trip_deleted'):
        st.toast("Trip deleted.", icon=":material/info:")
        st.info("Trip deleted.")
        st.session_state['trip_deleted'] = False

    # Fetch all user trips (cached on db.version)
    df_trips = TripService.get_trips(uid)

    # Top Control Bar: Trip Selection & Creation
    tc1, tc2 = st.columns([3, 1.2])

    with tc2:
        with st.popover("➕ Create New Trip", use_container_width=True):
            st.markdown("### 🌴 Plan a New Trip")
            with st.form("new_trip_form", clear_on_submit=True):
                t_name = st.text_input("Trip Name *", placeholder="e.g. Pune Weekend, Goa 2026")
                t_desc = st.text_input("Description / Destination", placeholder="e.g. Road trip with college friends")
                t_target = st.number_input("Target Total Budget (Optional)", min_value=0.0, step=500.0, value=0.0)
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    t_start = st.date_input("Start Date", value=datetime.now().date())
                with col_d2:
                    t_end = st.date_input("End Date", value=datetime.now().date() + timedelta(days=2))

                if st.form_submit_button("Create Trip", use_container_width=True, type="primary"):
                    if not t_name or not t_name.strip():
                        st.error("Please provide a trip name.")
                    else:
                        user_display_name = st.session_state.user.get('username', 'Me')
                        new_tid = TripService.create_trip_with_creator(
                            uid, t_name, user_display_name, t_desc, t_target or 0.0, t_start, t_end
                        )
                        st.session_state['active_trip_id'] = new_tid
                        st.session_state['trip_added'] = True
                        st.rerun()

    with tc1:
        if not df_trips.empty:
            trip_map = {f"{r['name']} ({'🟢 Active' if r['status'] == 'active' else '🔒 Settled'})": r['id'] for _, r in df_trips.iterrows()}

            current_idx = 0
            if st.session_state.get('active_trip_id'):
                try:
                    current_idx = list(trip_map.values()).index(st.session_state['active_trip_id'])
                except ValueError:
                    current_idx = 0

            sel_trip_label = st.selectbox("Select Trip", list(trip_map.keys()), index=current_idx, label_visibility="collapsed", key="trip_selector_sel")
            selected_trip_id = trip_map[sel_trip_label]
            if selected_trip_id != st.session_state.get('active_trip_id'):
                st.session_state['active_trip_id'] = selected_trip_id
                st.rerun()
        else:
            st.info("No trips found. Click **➕ Create New Trip** to get started!")

    active_tid = st.session_state.get('active_trip_id')

    def _render_frag_delete_button(item_id, button_key, delete_func, item_name="item", toast_msg="Item deleted."):
        with st.popover("", icon=":material/delete_outline:", help=f"Delete {item_name}"):
            st.markdown(
                f'<div class="wf-del-confirm-msg">Delete <strong>{_html.escape(str(item_name))}</strong>?</div>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes", icon=":material/check:", type="primary", use_container_width=True, key=f"yes_{button_key}"):
                    delete_func(item_id)
                    st.session_state['trip_toast_msg'] = toast_msg
                    st.rerun(scope="fragment")
            with c2:
                if st.button("No", icon=":material/close:", use_container_width=True, key=f"no_{button_key}"):
                    st.rerun(scope="fragment")

    @st.fragment
    def _render_trip_workspace(trip_id):
        # Single bulk DB roundtrip for the entire trip (cached on db.version)
        bundle = TripService.get_trip_bundle(trip_id)
        if not bundle or not bundle.get('summary') or not bundle['summary'].get('trip'):
            return

        # Fire floating top-right toast popup on any trip action
        toast_msg = st.session_state.pop('trip_toast_msg', None)
        if toast_msg:
            st.toast(toast_msg, icon=":material/check_circle:")

        summary = bundle['summary']
        current_trip = summary['trip']
        is_active_trip = (current_trip['status'] == 'active')

        # Trip Header Card with Edit, Status Toggle, Refresh and Delete Options
        st.markdown("<br>", unsafe_allow_html=True)
        th1, th2, th3 = st.columns([2.3, 2.2, 0.7])
        with th1:
            dates_str = f"📅 {current_trip['start_date']}" + (f" → {current_trip['end_date']}" if current_trip['end_date'] else "")
            desc_str = f" • {current_trip['description']}" if current_trip['description'] else ""
            st.markdown(f"### {current_trip['name']}")
            st.caption(f"{dates_str}{desc_str}")
        with th2:
            btn_c1, btn_c2, btn_c3 = st.columns(3)
            with btn_c1:
                with st.popover("✏️ Edit", use_container_width=True, help="Edit trip details and target budget"):
                    st.markdown(f"#### ✏️ Edit {current_trip['name']}")
                    with st.form(f"edit_trip_form_{trip_id}"):
                        et_name = st.text_input("Trip Name *", value=current_trip['name'])
                        et_desc = st.text_input("Description / Destination", value=current_trip['description'] or "")
                        et_tgt = st.number_input("Target Total Budget", min_value=0.0, value=float(current_trip['target_budget'] or 0.0), step=500.0)

                        s_val = datetime.strptime(current_trip['start_date'], "%Y-%m-%d").date() if current_trip['start_date'] else datetime.now().date()
                        e_val = datetime.strptime(current_trip['end_date'], "%Y-%m-%d").date() if current_trip['end_date'] else datetime.now().date()

                        col_es1, col_es2 = st.columns(2)
                        with col_es1:
                            et_start = st.date_input("Start Date", value=s_val)
                        with col_es2:
                            et_end = st.date_input("End Date", value=e_val)

                        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                            if not et_name or not et_name.strip():
                                st.error("Trip name cannot be empty.")
                            else:
                                TripService.update_trip(trip_id, et_name, et_desc, et_tgt, et_start, et_end)
                                st.session_state['trip_toast_msg'] = "Trip details updated!"
                                st.rerun(scope="fragment")

            with btn_c2:
                if st.button("🔄 Refresh", key=f"rebalance_btn_{trip_id}", use_container_width=True, help="Re-sync and recalculate all splits"):
                    TripService.rebalance_all_splits(trip_id)
                    db.bump_version()
                    st.session_state['trip_toast_msg'] = "Splits rebalanced & synced!"
                    st.rerun(scope="fragment")
            with btn_c3:
                status_label = "🔒 Settle" if is_active_trip else "🟢 Reopen"
                status_btn_type = "secondary" if is_active_trip else "primary"
                if st.button(status_label, key=f"status_toggle_{trip_id}", use_container_width=True, type=status_btn_type):
                    new_st = 'settled' if is_active_trip else 'active'
                    TripService.update_trip_status(trip_id, new_st)
                    st.session_state['trip_toast_msg'] = f"Trip marked as {new_st}!"
                    st.rerun()
        with th3:
            render_delete_button(trip_id, f"del_trip_{trip_id}", TripService.delete_trip, uid, current_trip['name'])

        # 4 Overview Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            card_metric("Total Trip Cost", fmt(summary['total_spent']))
        with m2:
            tgt_display = fmt(summary['target_budget']) if summary['target_budget'] > 0 else "No Limit"
            card_metric("Target Budget", tgt_display)
        with m3:
            if summary['target_budget'] > 0:
                rem_color = "normal" if summary['remaining_budget'] > 0 else "inverse"
                card_metric("Remaining Budget", fmt(summary['remaining_budget']), delta=f"{summary['burn_pct']*100:.1f}% Spent", delta_color=rem_color)
            else:
                card_metric("Remaining Budget", "N/A")
        with m4:
            card_metric("Pool Cash in Hand", fmt(summary['pool_cash_in_hand']), delta=f"{fmt(summary['total_advances'])} Pooled", delta_color="normal")

        # Target Budget Burn Bar
        if summary['target_budget'] > 0:
            st.progress(summary['burn_pct'])
            if summary['total_spent'] > summary['target_budget']:
                st.warning(f"⚠️ Budget Alert: Trip expenses have exceeded the target budget by {fmt(summary['total_spent'] - summary['target_budget'])}!")

        # Limit Deficit Alert (L1)
        if summary.get('has_cap_deficit'):
            st.warning(f"⚠️ **Budget Cap Deficit Alert (L1):** All members have budget limits that total {fmt(sum((m['max_budget'] or 0.0) for m in summary['members']))}, which is less than the total trip spend of {fmt(summary['total_spent'])}. There is an uncovered deficit of **{fmt(summary['deficit_amount'])}** that cannot be capped. Please adjust individual caps.")

        st.markdown("<br>", unsafe_allow_html=True)

        # State-persisted Trip Section Switcher (NEVER jumps back to Settlement & Summary!)
        trip_tab_options = [
            "📊 Settlement & Summary",
            "➕ Add Expense / Advance",
            "📜 Trip Ledger",
            "👥 Friends & Limits",
        ]
        if 'trip_active_tab' not in st.session_state or st.session_state['trip_active_tab'] not in trip_tab_options:
            st.session_state['trip_active_tab'] = trip_tab_options[0]

        picked_tab = st.segmented_control(
            "Trip Sections",
            trip_tab_options,
            default=st.session_state['trip_active_tab'],
            label_visibility="collapsed",
            key=f"trip_nav_seg_{trip_id}",
        )
        if picked_tab is not None:
            st.session_state['trip_active_tab'] = picked_tab
        active_tab = st.session_state['trip_active_tab']

        # ---------------------------------------------------------
        # VIEW 1: SETTLEMENT & SUMMARY
        # ---------------------------------------------------------
        if active_tab == trip_tab_options[0]:
            if not summary['members']:
                empty_state("No Friends Added", "Add friends to this trip in the '👥 Friends & Limits' tab to calculate splits.")
            else:
                st.markdown("#### 👥 Member Balance Matrix")

                for m in summary['members']:
                    with st.container():
                        mc1, mc2, mc3, mc4 = st.columns([2.5, 2, 2, 2.5])
                        with mc1:
                            cap_badge = f" <span style='background: rgba(59,130,246,0.2); color: #60a5fa; padding: 2px 6px; border-radius: 6px; font-size: 0.75rem;'>Capped at {fmt(m['max_budget'])}</span>" if m['max_budget'] else ""
                            weight_badge = f" <span style='background: rgba(255,255,255,0.1); color: #cbd5e1; padding: 2px 6px; border-radius: 6px; font-size: 0.75rem;'>{m['weight']}x</span>" if m['weight'] != 1.0 else ""
                            st.markdown(f"**{m['name']}**{weight_badge}{cap_badge}", unsafe_allow_html=True)
                            st.caption(f"Advance: {fmt(m['advance_given'])} | Out-of-pocket: {fmt(m['out_of_pocket'])}")
                        with mc2:
                            st.markdown(f"**Paid:** {fmt(m['total_paid'])}")
                        with mc3:
                            st.markdown(f"**Fair Share:** {fmt(m['final_share'])}")
                        with mc4:
                            cur_status = m.get('current_status', 'settled')
                            rem_bal = m.get('remaining_balance', 0.0)
                            paid_stl = m.get('settlements_paid', 0.0)
                            rec_stl = m.get('settlements_received', 0.0)

                            if cur_status == 'settled':
                                st.markdown("<span style='color: #4ade80; font-weight: bold;'>✅ All Settled (₹0.00)</span>", unsafe_allow_html=True)
                                if paid_stl > 0:
                                    st.caption(f"Cleared debt: {fmt(paid_stl)}")
                                elif rec_stl > 0:
                                    st.caption(f"Received refund: {fmt(rec_stl)}")
                            elif cur_status == 'refund':
                                st.markdown(f"<span style='color: #4ade80; font-weight: bold;'>🟢 Gets Back {fmt(rem_bal)}</span>", unsafe_allow_html=True)
                                if rec_stl > 0:
                                    st.caption(f"Received {fmt(rec_stl)} of {fmt(m['net_balance'])}")
                            elif cur_status == 'owes':
                                st.markdown(f"<span style='color: #f87171; font-weight: bold;'>🔴 Owes {fmt(-rem_bal)}</span>", unsafe_allow_html=True)
                                if paid_stl > 0:
                                    st.caption(f"Paid {fmt(paid_stl)} of {fmt(-m['net_balance'])}")
                        st.divider()

                # Settle-Up Transfers Plan with Badges & "Paid" Button
                st.markdown("#### 🤝 Simplified Settle-Up Plan")

                if not summary['settlements'] or summary.get('is_all_settled'):
                    st.success("🎉 **All accounts are fully settled!** Everyone is all settled (0 to 0 balance reached).")

                if summary['settlements']:
                    for idx, s in enumerate(summary['settlements']):
                        sc1, sc2 = st.columns([3.5, 1.2])

                        is_pool = (s['transfer_type'] == 'pool_cash')
                        badge_html = "<span style='background: rgba(14, 165, 233, 0.2); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;'>💼 Cash in Hand</span>" if is_pool else "<span style='background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;'>👤 Friend Transfer</span>"

                        border_color = "#10b981" if s['is_paid'] else ("#0ea5e9" if is_pool else "#8b5cf6")

                        with sc1:
                            action_text = f"Pull cash in hand & pay <span style='font-weight: 600; color: #4ade80;'>{s['to_name']}</span>" if is_pool else f"<span style='font-weight: 600; color: #f87171;'>{s['from_name']}</span> pays <span style='font-weight: 600; color: #4ade80;'>{s['to_name']}</span>"

                            st.markdown(f"""
                            <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-left: 4px solid {border_color}; border-radius: 10px; padding: 12px; margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        {badge_html} &nbsp; {action_text}
                                    </div>
                                    <div style="font-size: 1.15rem; font-weight: bold; color: #ffffff;">
                                        {fmt(s['amount'])}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        with sc2:
                            if s['is_paid']:
                                st.markdown("<div style='padding-top: 10px; text-align: center;'><span style='color: #4ade80; font-weight: bold; font-size: 1rem;'>✅ Paid</span></div>", unsafe_allow_html=True)
                            else:
                                if st.button("✅ Paid", key=f"pay_settle_btn_{trip_id}_{idx}", type="secondary", use_container_width=True, help=f"Record that {s['from_name']} has paid {s['to_name']} {fmt(s['remaining_amount'])}"):
                                    TripService.record_settlement(trip_id, s['from_name'], s['to_name'], s['remaining_amount'])
                                    st.session_state['trip_toast_msg'] = "Settlement payment recorded!"
                                    st.rerun(scope="fragment")

                st.markdown("<br>", unsafe_allow_html=True)

                # Export & WhatsApp Section (reuses bulk bundle — ZERO extra DB calls)
                st.markdown("#### 📱 Share & Export (100% Local)")

                wa_text = TripService.generate_whatsapp_summary(trip_id, st.session_state['sym'], bundle=bundle)

                wa_text_json = json.dumps(wa_text)
                copy_component_html = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; display: flex; align-items: center; gap: 12px; margin-top: 4px; margin-bottom: 8px;">
                    <button id="copyBtn" onclick="copyToClipboard()" style="
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        color: #ffffff;
                        border: none;
                        padding: 9px 18px;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 0.9rem;
                        cursor: pointer;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
                        transition: background 0.2s ease;
                    ">
                        📋 Copy Summary to Clipboard
                    </button>
                    <span id="copyMsg" style="color: #4ade80; font-weight: 600; font-size: 0.88rem; display: none;">
                        ✅ Copied to clipboard!
                    </span>
                </div>
                <script>
                function copyToClipboard() {{
                    const text = {wa_text_json};
                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(text).then(showDone, fallbackCopy);
                    }} else {{
                        fallbackCopy();
                    }}
                }}
                function fallbackCopy() {{
                    const text = {wa_text_json};
                    const ta = document.createElement("textarea");
                    ta.value = text;
                    ta.style.position = "fixed";
                    ta.style.left = "-999999px";
                    ta.style.top = "-999999px";
                    document.body.appendChild(ta);
                    ta.focus();
                    ta.select();
                    try {{
                        document.execCommand('copy');
                        showDone();
                    }} catch (e) {{
                        console.error('Copy failed', e);
                    }}
                    ta.remove();
                }}
                function showDone() {{
                    const btn = document.getElementById('copyBtn');
                    const msg = document.getElementById('copyMsg');
                    btn.innerHTML = '✅ Copied!';
                    btn.style.background = '#047857';
                    msg.style.display = 'inline';
                    setTimeout(() => {{
                        btn.innerHTML = '📋 Copy Summary to Clipboard';
                        btn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
                        msg.style.display = 'none';
                    }}, 2500);
                }}
                </script>
                """
                components.html(copy_component_html, height=52)

                st.text_area("📋 WhatsApp Formatted Summary Preview", value=wa_text, height=180, key=f"wa_summary_text_{trip_id}_{hash(wa_text)}")
                st.caption("💡 Click **📋 Copy Summary to Clipboard** above to copy the message, then paste it directly into your WhatsApp trip group!")

                csv_data = TripService.get_trip_csv_data(trip_id, st.session_state['sym'], bundle=bundle)
                clean_trip_filename = "".join(c for c in current_trip['name'] if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')
                st.download_button(
                    label="📥 Download Trip CSV Report",
                    data=csv_data,
                    file_name=f"{clean_trip_filename}_Settlement.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        # ---------------------------------------------------------
        # VIEW 2: ADD EXPENSE / ADVANCE (Stays in place, zero blanking, full reset to 0)
        # ---------------------------------------------------------
        elif active_tab == trip_tab_options[1]:
            if not is_active_trip:
                st.info("🔒 This trip is marked as Settled. Reopen the trip using the button above to add new expenses or advances.")
            elif not summary['members']:
                st.warning("Please add friends in the '👥 Friends & Limits' tab first before recording expenses.")
            else:
                sub_options = ["💸 Log Expense", "📥 Log Advance / Pool Money"]
                if 'trip_add_subtab' not in st.session_state or st.session_state['trip_add_subtab'] not in sub_options:
                    st.session_state['trip_add_subtab'] = sub_options[0]

                picked_sub = st.segmented_control(
                    "Entry Type",
                    sub_options,
                    default=st.session_state['trip_add_subtab'],
                    label_visibility="collapsed",
                    key=f"trip_add_sub_seg_{trip_id}",
                )
                if picked_sub is not None:
                    st.session_state['trip_add_subtab'] = picked_sub
                active_sub = st.session_state['trip_add_subtab']

                member_names = [m['name'] for m in summary['members']]

                # 1. Log Expense
                if active_sub == sub_options[0]:
                    exp_banner = st.session_state.pop('trip_exp_banner', None)
                    if exp_banner:
                        st.success(exp_banner)

                    st.markdown("##### 💸 Record a Trip Expense")
                    ev = st.session_state.get('trip_exp_form_v', 0)
                    use_custom_weights = st.checkbox(
                        "Use custom weights for this expense (e.g. 2x for couples/extra shares)",
                        value=False,
                        key=f"te_cw_{trip_id}_{ev}",
                    )
                    with st.form(f"trip_add_expense_form_{trip_id}_{ev}"):
                        exp_desc = st.text_input(
                            "Expense Description / Label *",
                            value="",
                            placeholder="e.g. Auto to station, Bikes rental, Resort, Lunch",
                            key=f"te_desc_{trip_id}_{ev}",
                        )
                        exp_amt = st.number_input(
                            "Amount *",
                            min_value=0.0,
                            step=1.0,
                            value=0.0,
                            key=f"te_amt_{trip_id}_{ev}",
                        )
                        exp_date = st.date_input(
                            "Date",
                            value=datetime.now().date(),
                            key=f"te_date_{trip_id}_{ev}",
                        )

                        payer_opts = ["💼 Pool Fund (from collected advances)"] + member_names
                        payer_sel = st.selectbox(
                            "Paid By *",
                            payer_opts,
                            index=0,
                            key=f"te_payer_{trip_id}_{ev}",
                        )

                        st.markdown("**Split Among Friends:**")
                        included_friends = st.multiselect(
                            "Included in Split",
                            member_names,
                            default=member_names,
                            key=f"te_inc_{trip_id}_{ev}",
                        )

                        custom_weights = {}
                        if use_custom_weights and included_friends:
                            st.caption("Set share weight for each included friend (1.0 = standard single share):")
                            w_cols = st.columns(min(4, len(included_friends)))
                            for idx, f_name in enumerate(included_friends):
                                matching_m = next(m for m in summary['members'] if m['name'] == f_name)
                                with w_cols[idx % len(w_cols)]:
                                    w_val = st.number_input(
                                        f"{f_name}",
                                        min_value=0.1,
                                        value=float(matching_m['weight']),
                                        step=0.5,
                                        key=f"te_w_{trip_id}_{ev}_{matching_m['id']}",
                                    )
                                    custom_weights[matching_m['id']] = w_val

                        if st.form_submit_button("Record Expense", type="primary", use_container_width=True):
                            if not exp_desc or not exp_desc.strip():
                                st.error("Please enter a description label for this expense.")
                            elif exp_amt is None or exp_amt <= 0:
                                st.error("Please enter a valid amount greater than 0.")
                            elif not included_friends:
                                st.error("Please select at least one friend to split this expense with.")
                            else:
                                paid_from_pool = (payer_sel == "💼 Pool Fund (from collected advances)")
                                payer_id = None if paid_from_pool else next(m['id'] for m in summary['members'] if m['name'] == payer_sel)

                                if use_custom_weights:
                                    final_weights = custom_weights
                                else:
                                    final_weights = {m['id']: m['weight'] for m in summary['members'] if m['name'] in included_friends}

                                is_custom = (use_custom_weights or len(included_friends) < len(summary['members']))
                                s_type = "custom" if is_custom else "equal"

                                TripService.add_expense(
                                    trip_id, payer_id, paid_from_pool, exp_amt, exp_desc, exp_date,
                                    split_type=s_type, member_weights=final_weights
                                )
                                st.session_state['trip_exp_form_v'] = ev + 1
                                st.session_state['trip_toast_msg'] = f"Expense has been recorded! ({exp_desc.strip()} — {fmt(exp_amt)})"
                                st.session_state['trip_exp_banner'] = f"Expense has been recorded: **{exp_desc.strip()}** ({fmt(exp_amt)})"
                                st.rerun(scope="fragment")

                # 2. Log Advance / Pool Contribution
                else:
                    adv_banner = st.session_state.pop('trip_adv_banner', None)
                    if adv_banner:
                        st.success(adv_banner)

                    st.markdown("##### 📥 Record Advance / Pool Money Given")
                    av = st.session_state.get('trip_adv_form_v', 0)
                    with st.form(f"trip_add_advance_form_{trip_id}_{av}"):
                        adv_m_name = st.selectbox(
                            "Friend Who Gave Money *",
                            member_names,
                            index=0,
                            key=f"ta_mem_{trip_id}_{av}",
                        )
                        adv_amt = st.number_input(
                            "Advance Amount *",
                            min_value=0.0,
                            step=100.0,
                            value=0.0,
                            key=f"ta_amt_{trip_id}_{av}",
                        )
                        adv_desc = st.text_input(
                            "Notes / Description",
                            value="",
                            placeholder="e.g. Initial Pool Advance, GPay transfer, Cash",
                            key=f"ta_desc_{trip_id}_{av}",
                        )
                        adv_date = st.date_input(
                            "Date",
                            value=datetime.now().date(),
                            key=f"ta_date_{trip_id}_{av}",
                        )

                        if st.form_submit_button("Record Advance", type="primary", use_container_width=True):
                            if adv_amt is None or adv_amt <= 0:
                                st.error("Please enter a valid advance amount greater than 0.")
                            else:
                                m_id = next(m['id'] for m in summary['members'] if m['name'] == adv_m_name)
                                note = adv_desc.strip() or "Pool Advance"
                                TripService.add_advance(trip_id, m_id, adv_amt, note, adv_date)
                                st.session_state['trip_adv_form_v'] = av + 1
                                st.session_state['trip_toast_msg'] = f"Advance has been recorded! ({adv_m_name} — {fmt(adv_amt)})"
                                st.session_state['trip_adv_banner'] = f"Advance pool contribution recorded: **{adv_m_name}** ({fmt(adv_amt)})"
                                st.rerun(scope="fragment")

        # ---------------------------------------------------------
        # VIEW 3: TRIP LEDGER (Zero extra DB calls — uses bundle)
        # ---------------------------------------------------------
        elif active_tab == trip_tab_options[2]:
            df_exp = bundle['expenses_df']
            df_adv = bundle['advances_df']
            df_settle = bundle['settlements_df']

            st.markdown("#### 💸 Itemized Expenses")
            if df_exp.empty:
                st.info("No expenses recorded for this trip yet.")
            else:
                for _, row in df_exp.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
                    with c1:
                        st.markdown(f"**{row['description']}**")
                        st.caption(f"📅 {row['date']}")
                    with c2:
                        st.markdown(f"<span style='color: #f87171; font-weight: bold;'>{fmt(row['amount'])}</span>", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"**Paid By:** {row['payer_name']}")
                        if row['splits_summary']:
                            st.caption(f"Splits: {row['splits_summary']}")
                    with c4:
                        _render_frag_delete_button(row['id'], f"del_exp_{row['id']}", TripService.delete_expense, row['description'], "Expense removed.")
                    st.divider()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📥 Advances & Pool Contributions")
            if df_adv.empty:
                st.info("No advances pooled yet.")
            else:
                for _, row in df_adv.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
                    with c1:
                        st.markdown(f"**{row['member_name']}**")
                        st.caption(f"📅 {row['date']}")
                    with c2:
                        st.markdown(f"<span style='color: #4ade80; font-weight: bold;'>+{fmt(row['amount'])}</span>", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"{row['description'] or 'Pool Contribution'}")
                    with c4:
                        _render_frag_delete_button(row['id'], f"del_adv_{row['id']}", TripService.delete_advance, "this advance", "Advance removed.")
                    st.divider()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 🤝 Completed Settlement Payments")
            if df_settle.empty:
                st.caption("No payments marked as paid yet. Click '✅ Paid' on any transfer in the Settle-Up plan to record payments.")
            else:
                for _, row in df_settle.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
                    with c1:
                        st.markdown(f"**{row['from_name']} ➡️ {row['to_name']}**")
                        st.caption(f"📅 {row['settled_at']}")
                    with c2:
                        st.markdown(f"<span style='color: #4ade80; font-weight: bold;'>{fmt(row['amount'])}</span>", unsafe_allow_html=True)
                    with c3:
                        st.markdown("<span style='color: #94a3b8;'>Status: Completed</span>", unsafe_allow_html=True)
                    with c4:
                        _render_frag_delete_button(row['id'], f"del_stl_{row['id']}", TripService.delete_settlement, "this payment", "Settlement reverted.")
                    st.divider()

        # ---------------------------------------------------------
        # VIEW 4: FRIENDS & LIMITS (Stays in place, zero blanking, precomputed activity)
        # ---------------------------------------------------------
        elif active_tab == trip_tab_options[3]:
            mem_banner = st.session_state.pop('trip_mem_banner', None)
            if mem_banner:
                st.success(mem_banner)

            st.markdown("#### ➕ Add a Friend to this Trip")
            mv = st.session_state.get('trip_mem_form_v', 0)
            with st.form(f"trip_add_member_form_{trip_id}_{mv}"):
                m_name = st.text_input("Friend's Name *", value="", placeholder="e.g. Bharat, Omsi, Rahul", key=f"tm_name_{trip_id}_{mv}")
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    m_weight = st.number_input(
                        "Share Multiplier / Weight",
                        min_value=0.1,
                        value=1.0,
                        step=0.5,
                        help="1.0 for single friend, 2.0 for a couple/pair sharing costs.",
                        key=f"tm_w_{trip_id}_{mv}",
                    )
                with m_col2:
                    m_cap = st.number_input(
                        "Max Budget Cap (0 = No Cap)",
                        min_value=0.0,
                        step=500.0,
                        value=0.0,
                        help="Limit this friend's total liability. Leave at 0 for no cap.",
                        key=f"tm_cap_{trip_id}_{mv}",
                    )

                if st.form_submit_button("Add Friend", use_container_width=True, type="primary"):
                    if not m_name or not m_name.strip():
                        st.error("Please provide a name.")
                    else:
                        cap_val = m_cap if (m_cap is not None and m_cap > 0) else None
                        TripService.add_member(trip_id, m_name, weight=m_weight, max_budget=cap_val)
                        st.session_state['trip_mem_form_v'] = mv + 1
                        st.session_state['trip_toast_msg'] = f"Friend '{m_name.strip()}' has been added!"
                        st.session_state['trip_mem_banner'] = f"Friend added to trip: **{m_name.strip()}**"
                        st.rerun(scope="fragment")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 👥 Current Trip Friends")
            members_df = bundle['members_df']
            member_activity_map = bundle['member_activity']
            if members_df.empty:
                st.info("No friends added yet.")
            else:
                for _, row in members_df.iterrows():
                    mc1, mc2, mc3, mc4, mc5 = st.columns([2.5, 2, 2, 0.8, 0.8])
                    with mc1:
                        st.markdown(f"**{row['name']}**")
                    with mc2:
                        st.markdown(f"**Weight:** {row['weight']}x" + (" (Couple/Pair)" if row['weight'] == 2.0 else ""))
                    with mc3:
                        cap_txt = fmt(row['max_budget']) if pd.notnull(row['max_budget']) and row['max_budget'] else "No Cap"
                        st.markdown(f"**Budget Cap:** {cap_txt}")
                    with mc4:
                        with st.popover("✏️", help=f"Edit {row['name']}"):
                            st.markdown(f"**Edit {row['name']}**")
                            with st.form(f"edit_mem_form_{row['id']}"):
                                edit_name = st.text_input("Name", value=row['name'], key=f"em_name_{row['id']}")
                                edit_weight = st.number_input("Share Multiplier / Weight", min_value=0.1, value=float(row['weight'] or 1.0), step=0.5, key=f"em_w_{row['id']}")
                                cur_cap = float(row['max_budget']) if pd.notnull(row['max_budget']) and row['max_budget'] is not None else 0.0
                                edit_cap = st.number_input("Max Budget Cap (0 = No Cap)", min_value=0.0, step=500.0, value=cur_cap, key=f"em_cap_{row['id']}")
                                if st.form_submit_button("Save Changes", use_container_width=True, type="primary"):
                                    TripService.update_member(row['id'], edit_name, edit_weight, edit_cap if edit_cap > 0 else None)
                                    st.session_state['trip_toast_msg'] = f"{edit_name.strip()} updated!"
                                    st.rerun(scope="fragment")
                    with mc5:
                        with st.popover("🗑️", help=f"Remove {row['name']}"):
                            activity = member_activity_map.get(row['id'])
                            st.markdown(f"#### 🗑️ Remove **{row['name']}**")

                            if activity and (activity['expense_total'] > 0 or activity['advance_total'] > 0):
                                st.warning(
                                    f"⚠️ **{row['name']}** has recorded **{fmt(activity['expense_total'])}** in expenses "
                                    f"and **{fmt(activity['advance_total'])}** in pool advances."
                                )
                                st.markdown("**To whom should this expense liability be transferred?**")

                                other_friends = [(r['id'], r['name']) for _, r in members_df.iterrows() if r['id'] != row['id']]
                                reassign_choices = ["💼 Pool Fund (Shared by all friends - Default)"] + [f"👤 {fn}" for fid, fn in other_friends] + ["🗑️ Delete expenses completely"]

                                sel_reassign = st.selectbox("Reassign To", reassign_choices, key=f"reassign_sel_{row['id']}")

                                if st.button("⚠️ Confirm Delete & Reassign", key=f"conf_del_reassign_{row['id']}", type="primary", use_container_width=True):
                                    if sel_reassign == "💼 Pool Fund (Shared by all friends - Default)":
                                        TripService.delete_member_with_reassignment(row['id'], reassign_to_pool=True)
                                    elif sel_reassign == "🗑️ Delete expenses completely":
                                        TripService.delete_member_with_reassignment(row['id'], delete_expenses=True)
                                    else:
                                        target_name = sel_reassign.replace("👤 ", "")
                                        target_id = next(fid for fid, fn in other_friends if fn == target_name)
                                        TripService.delete_member_with_reassignment(row['id'], reassign_payer_id=target_id)

                                    st.session_state['trip_toast_msg'] = f"{row['name']} removed and expenses reassigned."
                                    st.rerun(scope="fragment")
                            else:
                                st.markdown(f"Are you sure you want to remove **{row['name']}** from this trip?")
                                if st.button("Confirm Delete", key=f"conf_del_mem_{row['id']}", type="primary", use_container_width=True):
                                    TripService.delete_member(row['id'])
                                    st.session_state['trip_toast_msg'] = f"{row['name']} removed."
                                    st.rerun(scope="fragment")
                    st.divider()

    if active_tid:
        _render_trip_workspace(active_tid)



elif page == "Settings":
    st.markdown('<h1 class="main-header">Preferences</h1>', unsafe_allow_html=True)

    if st.session_state.get('cat_added'):
        st.success("Category added!")
        st.session_state['cat_added'] = False

    # Unified Account Management
    st.markdown("### 👤 Account Command Center")
    st.caption("Manage your entire identity and security in one place.")
    with st.form("unified_profile"):
        u_name = st.text_input("Username", value=st.session_state.user['username'])
        u_mail = st.text_input("Email", value=st.session_state.user.get('email', '') or "")
        u_ph = st.text_input("Phone", value=st.session_state.user.get('phone', '') or "")
        u_pass = st.text_input("New Password", type="password", placeholder="Leave blank to keep current")
        
        if st.form_submit_button("Update All Profile Details", use_container_width=True):
            # Update Profile Info
            res = AuthService.update_profile(uid, u_name, u_mail, u_ph)
            if res is True:
                st.session_state.user['username'] = u_name
                st.session_state.user['email'] = u_mail
                st.session_state.user['phone'] = u_ph
                
                # Update Password if provided
                if u_pass:
                    AuthService.update_password(uid, u_pass)
                
                st.success("Profile and Security updated successfully!")
                st.rerun()
            else:
                st.error(str(res))
    st.divider()

    # Currency Settings
    cur_opts = {"INR (₹)": "₹", "USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
    sel_cur = st.selectbox("Preferred Symbol", list(cur_opts.keys()), index=list(cur_opts.values()).index(st.session_state['sym']))
    if st.button("Save Settings"):
        st.session_state['sym'] = cur_opts[sel_cur]
        FinanceService.set_setting('currency_symbol', cur_opts[sel_cur], uid)
        st.rerun()

    st.divider()

    # Fiscal Month Settings
    st.markdown("### 📅 Fiscal Month")
    st.caption("Set the day your salary arrives. Fiscal month starts on this day.")
    cur_day = FinanceService.get_setting('fiscal_month_start_day', '1', uid)
    cur_day = int(cur_day) if str(cur_day).isdigit() else 1
    new_day = st.number_input("Fiscal Month Start Day", min_value=1, max_value=28, value=cur_day)
    if st.button("Save Fiscal Day"):
        FinanceService.set_setting('fiscal_month_start_day', str(new_day), uid)
        st.success(f"Fiscal month start day set to {new_day}!")
        st.rerun()

    st.divider()

    # Credit Card Settings
    st.markdown("### 💳 Credit Card Settings")
    st.caption("Enable this to focus only on EMIs for Credit Cards.")
    unlink_cc = FinanceService.get_setting('cc_unlink_transactions', 'False', uid) == 'True'
    new_unlink = st.checkbox("Unlink Transactions from Credit Card", value=unlink_cc, 
                            help="If enabled, you can only add EMIs to Credit Cards. Standard Expense/Payment tabs will be hidden.")
    if new_unlink != unlink_cc:
        FinanceService.set_setting('cc_unlink_transactions', str(new_unlink), uid)
        st.rerun()

    st.divider()

    # Dynamic Categories
    st.markdown("### 📁 Manage Categories")

    # Add Category Form
    with st.expander("➕ Add Category"):
        with st.form("new_cat"):
            cat_name = st.text_input("Category Name")
            cat_type = st.selectbox("Type", ["Income", "Expense"])
            cat_icon = st.text_input("Icon", value="📁")
            if st.form_submit_button("Add Category"):
                if cat_name.strip():
                    import uuid
                    cid = str(uuid.uuid4())
                    db.execute(
                        "INSERT INTO categories (id, user_id, name, type, icon) VALUES (?, ?, ?, ?, ?)",
                        (cid, uid, cat_name.strip(), cat_type, cat_icon)
                    )
                    st.session_state["cat_added"] = True
                    st.rerun()

    # List Existing Categories
    df_cats = FinanceService.get_categories(uid)
    if not df_cats.empty:
        with st.expander("📋 View & Manage Existing Categories", expanded=False):
            for _, row in df_cats.iterrows():
                c1, c2, c3 = st.columns([3, 1, 5])
                with c1:
                    st.markdown(f"{row['icon']} **{row['name']}** ({row['type']})")
                with c2:
                    if st.button("🗑️", key=f"del_cat_{row['id']}"):
                        # Verify ownership
                        res = db.execute("SELECT id FROM categories WHERE id = ? AND user_id = ?", (row['id'], uid))
                        if res and res.rows:
                            db.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (row['id'], uid))
                            st.rerun()
                        else:
                            st.error("Cannot delete system categories.")
                st.divider()

elif page == "Admin" and st.session_state.user['role'] == 'admin':
    st.markdown('<h1 class="main-header">User Management</h1>', unsafe_allow_html=True)
    
    with st.expander("➕ Create New User"):
        with st.form("admin_create_user"):
            new_u = st.text_input("Username")
            new_p = st.text_input("Password", type="password")
            new_e = st.text_input("Email")
            new_ph = st.text_input("Phone")
            new_r = st.selectbox("Role", ["user", "admin"])
            if st.form_submit_button("Create"):
                uid_res = AuthService.signup(new_u.strip(), new_p, new_e, new_ph)
                if isinstance(uid_res, str) and len(uid_res) > 30:
                    if new_r == 'admin':
                        db.execute("UPDATE wf_users SET role = 'admin' WHERE id = ?", (uid_res,))
                    st.success("User created!")
                    st.rerun()
                else:
                    st.error(str(uid_res))

    st.divider()
    
    users = AuthService.get_all_users()
    for u in users:
        uid_raw, uname, urole, uemail, uphone, usid, ustatus, ucreated = u
        color = "green" if ustatus == 'active' else "red"
        with st.container():
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 1.2rem; font-weight: bold;">{uname}</span> 
                        <span style="color: #94a3b8; font-size: 0.8rem;">(ID: {usid})</span>
                        <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; margin-left: 10px;">{ustatus.upper()}</span>
                    </div>
                    <div style="color: #94a3b8; font-size: 0.8rem;">{ucreated}</div>
                </div>
                <div style="margin-top: 5px; color: #cbd5e1; font-size: 0.9rem;">
                    📧 {uemail or 'N/A'} | 📱 {uphone or 'N/A'} | 🛡️ {urole}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if ustatus == 'active' and uid_raw != 'admin':
                    if st.button(f"Archive {uname}", key=f"arch_{uid_raw}"):
                        AuthService.delete_user(uid_raw)
                        st.rerun()
                elif ustatus == 'archived':
                    if st.button(f"✅ Unarchive {uname}", key=f"unarch_{uid_raw}", type="primary"):
                        AuthService.unarchive_user(uid_raw)
                        st.rerun()
            with c2:
                # Full Profile update for admin
                u_uname = st.text_input("Username", value=uname, key=f"un_{uid_raw}")
                u_email = st.text_input("Email", value=uemail or "", key=f"e_{uid_raw}")
                u_phone = st.text_input("Phone", value=uphone or "", key=f"ph_{uid_raw}")
                if st.button("Update Profile Info", key=f"uc_{uid_raw}"):
                    res = AuthService.update_profile(uid_raw, u_uname, u_email, u_phone)
                    if res is True:
                        st.success("User Profile updated!")
                        st.rerun()
                    else:
                        st.error(str(res))
                
                # Password reset for user
                new_upass = st.text_input("New Pass", type="password", key=f"p_{uid_raw}", placeholder="Leave blank to keep")
                if st.button("Update Pass", key=f"btn_p_{uid_raw}"):
                    if new_upass:
                        AuthService.update_password(uid_raw, new_upass)
                        st.success("Password updated!")
                
                if st.button("Refresh List", key=f"re_{uid_raw}"):
                    st.rerun()
        st.divider()
