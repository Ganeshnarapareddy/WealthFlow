import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit_cookies_manager as scm
from streamlit_javascript import st_javascript
from datetime import datetime, timedelta
import base64
import os

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

# --- LOGO HELPER ---
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

# AUTO-REPAIR: Database integrity fixes
try:
    # Trim usernames
    db.execute("UPDATE wf_users SET username = TRIM(username)")
    # Set Master Admin ID and update current session
    db.execute("UPDATE wf_users SET short_id = '00001' WHERE role = 'admin' AND (short_id IS NULL OR short_id = 'None')")
    if st.session_state.get('user') and st.session_state.user['role'] == 'admin':
        if st.session_state.user.get('short_id') in [None, 'None']:
            st.session_state.user['short_id'] = '00001'
except Exception:
    pass

# Import UI Components
from components.styles import apply_styles
from components.ui_elements import card_metric, section_header, empty_state

# Constants
ASSET_TYPES = ["Mutual Fund", "Stock", "Crypto", "Gold", "Real Estate", "FD", "Other"]

# --- CONFIG ---
st.set_page_config(
    page_title="WealthFlow Pro",
    page_icon=LOGO_B64 if LOGO_B64 else "💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- APPLE HOME SCREEN ICON ---
if LOGO_B64:
    st.markdown(f'<link rel="apple-touch-icon" href="{LOGO_B64}">', unsafe_allow_html=True)

# --- GLOBAL STYLES ---
st.markdown("""<style>
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], button[kind="header"] {
        display: none !important;
    }
    .main .block-container {
        padding-top: 0 !important;
    }
</style>""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
def login_page():
    st.markdown("""<style>
        .auth-container {
            max-width: 400px;
            margin: 5vh auto;
            padding: 2.5rem;
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .auth-logo { font-size: 2.5rem; text-align: center; margin-bottom: 0.5rem; }
        .auth-logo img { width: 80px; margin-bottom: 10px; mix-blend-mode: screen; border-radius: 12px; }
        
        @media (max-width: 768px) {
            .auth-container {
                margin-top: 1vh !important;
                padding: 1.5rem !important;
                max-width: 95%;
            }
            .auth-logo { 
                font-size: 1.8rem !important; 
                margin-bottom: 0.2rem !important;
            }
            .auth-logo img {
                width: 50px !important;
                margin-bottom: 5px !important;
            }
        }
    </style>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_html = f'<img src="{LOGO_B64}">' if LOGO_B64 else "💎"
        st.markdown(f'<div class="auth-container"><div class="auth-logo">{logo_html}<br>WealthFlow</div>', unsafe_allow_html=True)
        
        tab_login, tab_signup, tab_forgot = st.tabs(["Login", "Signup", "Reset"])
        
        with tab_login:
            user_in = st.text_input("Username", key="l_user")
            pass_in = st.text_input("Password", type="password", key="l_pass")
            l_remember = st.checkbox("Remember me for 30 days", value=True, key="l_remember")
            if st.button("Login", use_container_width=True, type="primary"):
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
            st.info("💡 Providing Email or Phone ensures your data can be recovered if you delete your account.")
            if st.button("Create Account", use_container_width=True):
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
            st.markdown("### 🔐 Secure Recovery")
            st.caption("Enter your registered Email or Phone to reset your password.")
            f_contact = st.text_input("Registered Email or Phone", key="f_contact")
            f_pass = st.text_input("New Password", type="password", key="f_pass")
            if st.button("Verify & Reset Password", use_container_width=True):
                if not f_contact:
                    st.error("Please enter your contact info.")
                else:
                    from database import db
                    # Find user by email or phone
                    res = db.execute("SELECT id FROM wf_users WHERE (email = ? OR phone = ?) AND status = 'active'", (f_contact, f_contact))
                    if res and res.rows:
                        AuthService.update_password(res.rows[0][0], f_pass)
                        st.success("Password updated successfully! Please login.")
                    else:
                        st.error("Contact information not found.")
        
        st.markdown('</div>', unsafe_allow_html=True)

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

apply_styles()

# --- HIDE DEFAULT SIDEBAR & HEADER ---
st.markdown("""
    <style>
    /* Native MENU Tag Button */
    .stButton > button:first-child:not([key="close_ov"]):not([key^="ov_"]) {
        /* This selector is a bit generic, let's target the tag specifically if possible */
    }
    
    .stButton > button {
        transition: all 0.2s ease !important;
    }
    </style>
""", unsafe_allow_html=True)

# Function to handle navigation
def nav_to(p):
    st.session_state['page'] = p
    st.session_state['show_menu'] = False
    # Reset transaction filters when moving between pages
    for k in ["hist_year", "hist_month", "hist_day", "hist_type"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# Delete confirmation helper
def render_delete_button(item_id, button_key, delete_func, user_id, item_name="item"):
    conf_key = f"del_conf_{item_id}"
    if conf_key not in st.session_state['delete_confirm']:
        st.session_state['delete_confirm'][conf_key] = False

    if not st.session_state['delete_confirm'][conf_key]:
        if st.button("🗑️", key=button_key):
            st.session_state['delete_confirm'][conf_key] = True
            st.rerun()
    else:
        st.warning(f"Delete {item_name}?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes", key=f"yes_{item_id}"):
                delete_func(item_id, user_id)
                st.session_state['delete_confirm'][conf_key] = False
                # Set delete flag for popup
                if "cdel_" in button_key: st.session_state['card_deleted'] = True
                elif "ldel_" in button_key or "del_loan_" in button_key: st.session_state['loan_deleted'] = True
                elif "del_c_txn_" in button_key: st.session_state['card_txn_deleted'] = True
                st.rerun()
        with c2:
            if st.button("❌ No", key=f"no_{item_id}"):
                st.session_state['delete_confirm'][conf_key] = False
                st.rerun()

# --- CUSTOM MENU TAG ---
if not st.session_state['show_menu']:
    # Use a clear key for the tag button
    if st.button("💎 MENU", key="main_menu_tag"):
        st.session_state['show_menu'] = True
        st.rerun()
    
    # Position the tag button
    st.markdown("""
        <style>
        .stButton > button[key="main_menu_tag"] {
            position: fixed !important;
            top: 25px !important;
            left: 0 !important;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: white !important;
            border-radius: 0 12px 12px 0 !important;
            width: 100px !important;
            height: 45px !important;
            z-index: 1000 !important;
            border: none !important;
            font-weight: 800 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- OVERLAY MENU ---
if st.session_state['show_menu']:
    # The 'X' button needs to be at the very top of the DOM to be interactive
    # And we use a standard Streamlit layout to ensure it's a real button
    
    col_space, col_close = st.columns([10, 2])
    with col_close:
        if st.button("✕ CLOSE", key="close_ov", use_container_width=True):
            st.session_state['show_menu'] = False
            st.rerun()
            
    # Centered Logo and Credit
    logo_top = f'<img src="{LOGO_B64}" style="width: 100px; display: block; margin: 0 auto; mix-blend-mode: screen; border-radius: 20px;">' if LOGO_B64 else "💎"
    st.markdown(f"<div style='text-align:center; margin-top:20px;'>{logo_top}</div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; color:white; font-size:2.8rem; margin-top:0px;'>WealthFlow</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.9rem; margin-top:-10px; font-style:italic;'>Made by Ganesh Narapareddy</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation Buttons (Mobile Optimized)
    _, c_btns, _ = st.columns([0.1, 0.8, 0.1])
    with c_btns:
        pages = {
            "Dashboard": "📊 Dashboard",
            "Transactions": "💸 Transactions",
            "Budgets": "📋 Budgets",
            "Subscriptions": "💳 Subscriptions",
            "Loans": "💰 Loans and EMI",
            "Credit Cards": "💳 Credit Cards",
            "Goals": "🎯 Goals",
            "Assets": "📈 Assets",
            "Settings": "⚙️ Settings"
        }
        
        for p_id, p_label in pages.items():
            if st.button(p_label, key=f"ov_{p_id}", use_container_width=True):
                nav_to(p_id)
        
        # Admin User Management
        if st.session_state.user['role'] == 'admin':
            if st.button("👥 User Management", key="ov_Admin", use_container_width=True):
                nav_to("Admin")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔓 Logout", key="ov_Logout", use_container_width=True, type="secondary"):
            token = cookies.get('wealthflow_remember_token')
            AuthService.clear_session(token)
            if token:
                del cookies['wealthflow_remember_token']
                cookies.save()
            # Clear localStorage backup
            st_javascript("localStorage.removeItem('wealthflow_remember_token');")
            st.session_state.user = None
            st.rerun()
    
    st.stop()

# --- PAGE CONTENT ---

def fmt(val):
    if val is None:
        return f"{st.session_state['sym']}0.00"
    return f"{st.session_state['sym']}{val:,.2f}"

page = st.session_state['page']

if page == "Dashboard":
    # v1.1 - Dashboard with Daily Analytics
    # Top Profile Bar
    t1, t2 = st.columns([0.85, 0.15])
    with t2:
        with st.popover("👤 Profile", use_container_width=True):
            st.markdown(f"**Username:** `{st.session_state.user['username']}`")
            # Safety check for short_id in existing sessions
            sid_display = st.session_state.user.get('short_id', '58184')
            st.markdown(f"**System ID:** `{sid_display}`")
            st.markdown("---")
            new_name = st.text_input("Change Username", value=st.session_state.user['username'])
            if st.button("Update Name", use_container_width=True):
                if AuthService.update_username(uid, new_name):
                    st.session_state.user['username'] = new_name
                    st.success("Name updated!")
                    st.rerun()
                else:
                    st.error("Name already taken")
            st.markdown("---")
            if st.button("Logout", use_container_width=True, type="primary"):
                token = cookies.get('wealthflow_remember_token')
                AuthService.clear_session(token)
                if token:
                    del cookies['wealthflow_remember_token']
                    cookies.save()
                # Clear localStorage backup
                st_javascript("localStorage.removeItem('wealthflow_remember_token');")
                st.session_state['user'] = None
                st.rerun()

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

    # Get all metrics with filtering
    # 1. Dashboard Metrics
    net = FinanceService.get_net_worth(uid)
    burn = RecurringService.get_monthly_recurring_total(uid)
    inc, exp = FinanceService.get_period_data(uid, sel_year, sel_month)
    
    # Check for Fiscal Mode
    if st.session_state.get('month_mode_radio', 'Calendar') == 'Fiscal':
        fiscal_day = FinanceService.get_setting('fiscal_month_start_day', '1', uid)
        fiscal_day = int(fiscal_day) if str(fiscal_day).isdigit() else 1
        f_inc, f_exp = FinanceService.get_fiscal_data(uid, sel_year, sel_month, fiscal_day)
        inc, exp = f_inc, f_exp

    today_spent, yesterday_spent = FinanceService.get_today_vs_yesterday(uid)
    day_pct = ((today_spent - yesterday_spent) / yesterday_spent * 100) if yesterday_spent > 0 else 0

    # Get comparison data
    prev_inc, prev_exp, prev_label = FinanceService.get_previous_period_data(uid, sel_year, sel_month)
    inc_delta_str, inc_increased = FinanceService.get_comparison_delta(inc, prev_inc)
    exp_delta_str, exp_increased = FinanceService.get_comparison_delta(exp, prev_exp)

    # Savings rate and comparison
    savings_rate = ((inc - exp) / inc * 100) if inc > 0 else 0.0
    prev_savings_rate = ((prev_inc - prev_exp) / prev_inc * 100) if prev_inc > 0 else 0.0
    sr_delta_str, sr_increased = FinanceService.get_comparison_delta(savings_rate, prev_savings_rate)

    # EMI stats
    df_cc_emis = CreditCardService.get_all_active_emis(uid)
    df_loan_emis = LoanService.get_active_emi_stats(uid)
    total_emi_amt = df_cc_emis['Monthly'].sum() + df_loan_emis['Monthly'].sum()
    active_emi_count = len(df_cc_emis) + len(df_loan_emis)
    
    # Subscription count
    df_subs = RecurringService.get_subscriptions(uid)
    active_subs_count = len(df_subs)

    # Subscription comparison
    prev_burn = 0.0
    burn_delta_str = None
    burn_increased = False
    if sel_year != "All" and sel_month != "All":
        prev_month = sel_month - 1
        prev_year = sel_year
        if prev_month == 0:
            prev_month = 12
            prev_year = sel_year - 1
        prev_burn = RecurringService.get_monthly_recurring_total_for_period(uid, prev_year, prev_month)
        burn_delta_str, burn_increased = FinanceService.get_comparison_delta(burn, prev_burn)

    m1, m2, m3, m4 = st.columns([1, 1, 1, 1])
    with m1: card_metric("Net Worth", fmt(net))
    with m2: card_metric("Today's Spent", fmt(today_spent),
                        delta=f"{day_pct:+.1f}%" if yesterday_spent > 0 else None,
                        delta_color="inverse")
    with m3: card_metric("Monthly Income", fmt(inc),
                        delta=inc_delta_str,
                        delta_color="normal")
    with m4: card_metric("Monthly Spent", fmt(exp),
                        delta=exp_delta_str,
                        delta_color="inverse")

    # Second row - Additional Analytics
    a1, a2, a3 = st.columns([1, 1, 1])
    with a1: card_metric("Savings Rate", f"{savings_rate:.1f}%",
                         delta=sr_delta_str,
                         delta_color="normal")
    with a2: card_metric("Total EMI per Month", fmt(total_emi_amt),
                         delta=f"{active_emi_count} Active")
    with a3: 
        sub_delta = f"{burn_delta_str} ({active_subs_count} Active)" if burn_delta_str else f"{active_subs_count} Active"
        card_metric("Total Subscriptions per month", fmt(burn) if burn > 0 else "N/A",
                         delta=sub_delta,
                         delta_color="inverse")

    # --- Credit Card Summary ---
    st.markdown("---")
    df_cards = CreditCardService.get_cards(uid)
    st.markdown("#### 💳 Credit Card Statistics")
    if not df_cards.empty:
        total_limit = df_cards['card_limit'].sum()
        total_outstanding = df_cards['current_balance'].sum()
        total_available = total_limit + total_outstanding
        utilization = (-total_outstanding / total_limit * 100) if total_limit > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Limit", fmt(total_limit))
        c2.metric("Outstanding", fmt(total_outstanding), delta=f"{utilization:.1f}% Use", delta_color="inverse")
        c3.metric("Available", fmt(total_available))
        st.progress(max(0.0, min(1.0, utilization/100)))
    else:
        st.info("No credit cards tracked yet.")

    # Smart Alerts Section
    st.markdown("### 🔔 Smart Alerts")

    # Consolidate all alerts
    all_alerts = []
    
    # 1. Subscriptions
    subs = RecurringService.get_upcoming_renewals(uid, 30)
    for s in subs:
        aid = f"sub_{s['id']}"
        auto_desc = f"Auto: {s['name']}"
        if not FinanceService.is_alert_actioned(aid, uid) and not FinanceService.auto_txn_exists(auto_desc, uid):
            all_alerts.append({
                'category': 'Subscription', 'days': s['days_left'],
                'date': s['next_date'].strftime("%d %b"), 'name': s['name'],
                'amount': s['amount'], 'id': aid, 'icon': "💳"
            })
        
    # 2. Loans
    loan_alerts = LoanService.get_upcoming_dues(uid, 30)
    for l in loan_alerts:
        auto_desc = f"Auto: {l['person_name']}"
        if not FinanceService.auto_txn_exists(auto_desc, uid):
            all_alerts.append({
                'category': 'Loan', 'days': l['days_left'],
                'date': datetime.strptime(l['due_date'], "%Y-%m-%d").strftime("%d %b"),
                'name': f"{l['person_name']} ({'Given' if l['loan_type'] == 'given' else 'Taken'})",
                'amount': l['remaining'], 'id': l['id'], 'icon': "💰", 'is_emi': l.get('is_emi', False)
            })
        
    # 3. CC EMIs
    emi_alerts = CreditCardService.get_upcoming_emi_payments(uid, 30)
    for _, e in emi_alerts.iterrows():
        due_dt = datetime.strptime(e['Due Date'], "%Y-%m-%d").date()
        days = (due_dt - datetime.now().date()).days
        auto_desc = f"Auto: {e['Description']}"
        if not FinanceService.auto_txn_exists(auto_desc, uid):
            all_alerts.append({
                'category': 'EMI', 'days': days, 'date': due_dt.strftime("%d %b"),
                'name': f"{e['Description']} ({e['Card']})", 'amount': e['Amount'], 'id': e['id'], 'icon': "🗓️"
            })
        
    # 4. CC Bills
    card_alerts = CreditCardService.get_upcoming_bills(uid, 30)
    for b in card_alerts:
        all_alerts.append({
            'category': 'Bill', 'days': b['days_left'],
            'date': b['due_date'].strftime("%d %b"),
            'name': f"{b['name']} Bill", 'amount': b['balance'], 'id': b['id'], 'icon': "💳"
        })

    # Sort by urgency
    all_alerts.sort(key=lambda x: x['days'])

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
    t_sp, t_dy, t_ie, t_tr, t_we, t_bu = st.tabs(["📊 Category", "📅 Daily", "📊 Income/Expense", "📈 Trend", "💰 Wealth", "🔥 Burn"])
    with t_sp:
        df_sp = FinanceService.get_spending_by_category(uid, sel_year, sel_month)
        if not df_sp.empty:
            fig = px.bar(df_sp, x='Category', y='Amount', color='Category', text_auto='.2f')
            # Dynamic width to ensure readability with many categories
            chart_width = max(len(df_sp) * 100, 700) 
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color="#e2e8f0", showlegend=False,
                margin=dict(t=30,b=20,l=0,r=0),
                width=chart_width,
                xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True)
            )
            fig.update_traces(textfont_color='white', textposition='outside')
            
            # Use custom HTML for horizontal scrolling
            st.markdown('<div style="overflow-x: auto; width: 100%; border-radius: 12px;">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        else: empty_state("No Data", "No spending data available.")

    with t_dy:
        df_dy = FinanceService.get_daily_spending_by_category(uid, sel_year, sel_month)
        if not df_dy.empty:
            # Format dates as strings for cleaner categorical display
            df_dy['Date'] = pd.to_datetime(df_dy['Date']).dt.strftime('%Y-%m-%d')
            df_dy = df_dy.sort_values('Date')
            
            unique_days = df_dy['Date'].nunique()
            # Calculate dynamic width: minimum 800px, or 100px per day
            dynamic_width = max(unique_days * 100, 800)
            
            fig_dy = px.bar(df_dy, x='Date', y='Amount', color='Category', 
                            title=None,
                            labels={'Amount': f'Amount ({st.session_state["sym"]})'},
                            barmode='stack')
            
            fig_dy.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color="#e2e8f0",
                margin=dict(t=30,b=10,l=0,r=0), # Increased top margin for labels
                width=dynamic_width,
                height=450,
                xaxis=dict(type='category', title=None, fixedrange=True, tickangle=0),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', fixedrange=True),
                legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1),
                bargap=0.6  # Make bars smaller by increasing gap
            )
            
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
                textfont=dict(color='#94a3b8', size=11)
            ))
            
            # Ensure Y-axis has room for labels
            max_y = totals['Amount'].max() if not totals.empty else 100
            fig_dy.update_yaxes(range=[0, max_y * 1.15])
            
            # Wrap in a scrollable container
            st.markdown(f'<div style="overflow-x: auto; width: 100%; padding-bottom: 20px;">', unsafe_allow_html=True)
            st.plotly_chart(fig_dy, use_container_width=False, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        else: empty_state("No Data", "No daily spending data available.")

    with t_ie:
        df_ie = FinanceService.get_income_expense_by_month(uid, sel_year, sel_month)
        if not df_ie.empty:
            fig_ie = go.Figure(data=[
                go.Bar(name='Income', x=df_ie['Month'], y=df_ie['Income'], marker_color='#4ade80', text=df_ie['Income'], texttemplate='%{text:.2s}', textposition='outside'),
                go.Bar(name='Expense', x=df_ie['Month'], y=df_ie['Expense'], marker_color='#f87171', text=df_ie['Expense'], texttemplate='%{text:.2s}', textposition='outside')
            ])
            fig_ie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color="#e2e8f0", barmode='group',
                margin=dict(t=30,b=20,l=0,r=0),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', fixedrange=True),
                xaxis=dict(fixedrange=True)
            )
            st.plotly_chart(fig_ie, use_container_width=True, config={'displayModeBar': False})
        else: empty_state("No Data", "Income/expense data will appear here.")

    with t_tr:
        df_tr = FinanceService.get_spending_trend(uid, sel_year, sel_month)
        if not df_tr.empty:
            fig_tr = px.line(df_tr, x='Month', y='Amount', markers=True, text='Amount')
            fig_tr.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', font_color="#e2e8f0",
                plot_bgcolor='rgba(255,255,255,0.05)',
                margin=dict(t=30,b=20,l=0,r=0),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', fixedrange=True),
                xaxis=dict(fixedrange=True)
            )
            fig_tr.update_traces(line_color='#3b82f6', textposition='top center', texttemplate='%{text:.2s}')
            st.plotly_chart(fig_tr, use_container_width=True, config={'displayModeBar': False})
        else: empty_state("No Data", "Spend trend will appear here.")
        
    with t_we:
        st.markdown("#### 💰 Wealth Distribution")
        res_assets = db.execute("SELECT type, SUM(value) FROM assets WHERE user_id = ? GROUP BY type", (uid,))
        asset_data = []
        total_assets = 0
        if res_assets and res_assets.rows:
            for row in res_assets.rows:
                asset_data.append({'Category': row[0], 'Amount': row[1]})
                total_assets += row[1]
        
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
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig3.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color="#e2e8f0", showlegend=False,
                margin=dict(t=30,b=20,l=0,r=0),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="Amount", fixedrange=True),
                xaxis=dict(title=None, fixedrange=True)
            )
            fig3.update_traces(textfont_color='white', textposition='outside')
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        else:
            empty_state("No Assets", "Add your investments in the Assets tab to see the breakdown here.")

    with t_bu:
        budget_month = sel_month if sel_month != "All" else None
        budget_year = sel_year if sel_year != "All" else None
        df_b = BudgetService.get_monthly_budgets(uid, month=budget_month, year=budget_year)
        limit = df_b['Limit'].sum() if not df_b.empty else 0
        if limit > 0:
            fig4 = go.Figure(go.Indicator(mode="gauge+number", value=exp, gauge={'axis': {'range': [None, limit]}}))
            fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#e2e8f0"})
            st.plotly_chart(fig4, use_container_width=True)
        else: empty_state("No Budgets", "Set limits to track burn.")

elif page == "Transactions":
    st.markdown('<h1 class="main-header">Ledger</h1>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["➕ Add Entry", "📜 History"])
    
    with t1:
        txn_type = st.radio("Type", ["Expense", "Income"], horizontal=True, key="txn_type_toggle")
        with st.form("add_txn_pro", clear_on_submit=True):
            amt = st.number_input("Amount", min_value=0.01, step=1.0, value=None, placeholder="Enter amount")
            dt = st.date_input("Date", value=datetime.now().date())
            all_cats = FinanceService.get_categories(uid)
            filtered = all_cats[all_cats['type'] == txn_type]
            cat_opts = {f"{r['icon']} {r['name']}": r['id'] for _, r in filtered.iterrows()}
            cat_sel = st.selectbox("Category", list(cat_opts.keys()) if cat_opts else ["-"])
            desc = st.text_input("Description", placeholder="What was this for?")
            if st.form_submit_button("Record Transaction", use_container_width=True):
                if cat_sel != "-":
                    full_dt = datetime.combine(dt, datetime.now().time())
                    FinanceService.add_transaction(amt, cat_opts[cat_sel], desc, full_dt, txn_type, uid)
                    st.success("Transaction Logged!")

    with t2:
        # Transaction Filters
        st.markdown("#### 🔍 Filter History")
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
            uid, year=sel_y, month=sel_m, day=sel_d, txn_type=sel_t, limit=100
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
                    if st.button("🗑️", key=f"del_txn_{row['ID']}_{row['Source']}"):
                        if row['Source'] == 'main':
                            FinanceService.delete_transaction(row['ID'], uid)
                            st.session_state['txn_deleted'] = True
                        else:
                            CreditCardService.delete_transaction(row['ID'], uid)
                            st.session_state['card_txn_deleted'] = True
                        st.rerun()
                st.divider()
        else: empty_state("No History", "Log transactions to see them here.")

    # Centered Popup for deletion
    if st.session_state.get('txn_deleted'):
        st.markdown('<div class="center-popup">', unsafe_allow_html=True)
        st.info("Transaction revoked and balance restored.")
        st.session_state['txn_deleted'] = False
        st.markdown('</div>', unsafe_allow_html=True)

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
                st.markdown(f"**{row['Icon']} {row['Name']}**")
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
