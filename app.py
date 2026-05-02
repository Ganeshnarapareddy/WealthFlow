import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import Services
from database import db
from services.finance_service import FinanceService
from services.budget_service import BudgetService
from services.recurring_service import RecurringService
from services.goal_service import GoalService
from services.asset_service import AssetService
from services.loan_service import LoanService
from services.credit_card_service import CreditCardService

# Import UI Components
from components.styles import apply_styles
from components.ui_elements import card_metric, section_header, empty_state

# Constants
ASSET_TYPES = ["Mutual Fund", "Stock", "Crypto", "Gold", "Real Estate", "FD", "Other"]

# --- CONFIG ---
st.set_page_config(
    page_title="WealthFlow Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if 'sym' not in st.session_state: st.session_state['sym'] = '₹'
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
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], button[kind="header"] {
        display: none !important;
    }
    
    /* Native MENU Tag Button */
    .stButton > button:first-child:not([key="close_ov"]):not([key^="ov_"]) {
        /* This selector is a bit generic, let's target the tag specifically if possible */
    }
    
    .stButton > button {
        transition: all 0.2s ease !important;
    }

    /* Padding for main content */
    .main .block-container {
        padding-top: 5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Function to handle navigation
def nav_to(p):
    st.session_state['page'] = p
    st.session_state['show_menu'] = False
    st.rerun()

# Delete confirmation helper
def render_delete_button(item_id, button_key, delete_func, item_name="item"):
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
                delete_func(item_id)
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
    st.markdown("<h1 style='text-align:center; color:white; font-size:2.8rem; margin-top:20px;'>💎 WealthFlow</h1>", unsafe_allow_html=True)
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
    
    st.stop()

# --- PAGE CONTENT ---

def fmt(val):
    if val is None:
        return f"{st.session_state['sym']}0.00"
    return f"{st.session_state['sym']}{val:,.2f}"

page = st.session_state['page']

if page == "Dashboard":
    h1, h2, h3, h4 = st.columns([2, 1.2, 1.2, 1.2])
    with h1: st.markdown('<h1 class="main-header">Command Center</h1>', unsafe_allow_html=True)
    with h2:
        # Year selector with "All" option
        years = FinanceService.get_available_years()
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
    fiscal_day = FinanceService.get_setting('fiscal_month_start_day', '1')
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
            fiscal_day_val = FinanceService.get_setting('fiscal_month_start_day', '1')
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
    net = FinanceService.get_net_worth()
    burn = RecurringService.get_monthly_recurring_total()
    inc, exp = FinanceService.get_monthly_income_vs_expense(
        sel_year, sel_month, fiscal_start_day
    )
    today_spent, yesterday_spent = FinanceService.get_today_vs_yesterday()
    day_pct = ((today_spent - yesterday_spent) / yesterday_spent * 100) if yesterday_spent > 0 else 0

    # Get comparison data
    prev_inc, prev_exp, prev_label = FinanceService.get_previous_period_data(sel_year, sel_month, fiscal_start_day)
    inc_delta_str, inc_increased = FinanceService.get_comparison_delta(inc, prev_inc)
    exp_delta_str, exp_increased = FinanceService.get_comparison_delta(exp, prev_exp)

    # Savings rate and comparison
    savings_rate = ((inc - exp) / inc * 100) if inc > 0 else 0.0
    prev_savings_rate = ((prev_inc - prev_exp) / prev_inc * 100) if prev_inc > 0 else 0.0
    sr_delta_str, sr_increased = FinanceService.get_comparison_delta(savings_rate, prev_savings_rate)

    # EMI stats
    df_cc_emis = CreditCardService.get_all_active_emis()
    df_loan_emis = LoanService.get_active_emi_stats()
    total_emi_amt = df_cc_emis['Monthly'].sum() + df_loan_emis['Monthly'].sum()
    active_emi_count = len(df_cc_emis) + len(df_loan_emis)
    
    # Subscription count
    df_subs = RecurringService.get_subscriptions()
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
        prev_burn = RecurringService.get_monthly_recurring_total_for_period(prev_year, prev_month)
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
    cc_col1, cc_col2 = st.columns([2, 1])
    df_cards = CreditCardService.get_cards()
    with cc_col1:
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
            
    with cc_col2:
        st.markdown("#### 🔔 Bill Alerts")
        card_alerts = CreditCardService.get_upcoming_bills(15)
        if card_alerts:
            for bill in card_alerts[:2]:
                st.warning(f"**{bill['name']}** in {bill['days_left']}d")
        else:
            st.success("All bills clear!")

    # Smart Alerts Section
    st.markdown("### 🔔 Smart Alerts")

    # Subscription renewals
    alerts = RecurringService.get_upcoming_renewals(30)
    if alerts:
        for alert in alerts[:5]:
            days = alert['days_left']
            amt_fmt = fmt(alert['amount'])
            if days <= 0:
                st.warning(f"🔴 **{alert['name']}** renews **today**! ({amt_fmt})")
            elif days == 1:
                st.warning(f"🟡 **{alert['name']}** renews **tomorrow**! ({days} day left - {amt_fmt})")
            elif days <= 7:
                st.info(f"🟢 **{alert['name']}** renews in **{days} days** ({amt_fmt})")
            else:
                st.write(f"📅 **{alert['name']}** renews in **{days} days** ({amt_fmt})")

    # Loan due date alerts
    loan_alerts = LoanService.get_upcoming_dues(30)
    for alert in loan_alerts:
        days = alert['days_left']
        amt_fmt = fmt(alert['remaining'])
        label = "Loan Given" if alert['loan_type'] == 'given' else "Loan Taken"
        if days <= 0:
            st.error(f"🔴 **{alert['person_name']}** ({label}) — **OVERDUE**! Outstanding: {amt_fmt}")
        elif days <= 3:
            st.warning(f"🔴 **{alert['person_name']}** ({label}) due in **{days} days**! Outstanding: {amt_fmt}")
        elif days <= 7:
            st.info(f"🟢 **{alert['person_name']}** ({label}) due in **{days} days**")
        else:
            st.write(f"📅 **{alert['person_name']}** ({label}) due in **{days} days**")

    # Credit card bill alerts
    card_alerts = CreditCardService.get_upcoming_bills(15)
    for bill in card_alerts:
        days = bill['days_left']
        if days <= 0:
            st.error(f"🔴 **{bill['name']}** ({bill['bank']}) bill **due today**! Outstanding: {fmt(bill['balance'])}")
        elif days <= 3:
            st.warning(f"🔴 **{bill['name']}** ({bill['bank']}) bill due in **{days} days**! Outstanding: {fmt(bill['balance'])}")
        elif days <= 7:
            st.info(f"🟢 **{bill['name']}** ({bill['bank']}) bill due in **{days} days**")
        else:
            st.write(f"📅 **{bill['name']}** ({bill['bank']}) bill in **{days} days**")

    st.markdown("<br>", unsafe_allow_html=True)

    # Dashboard Tabs
    t_sp, t_ie, t_tr, t_we, t_bu = st.tabs(["📊 Spending", "📊 Income/Expense", "📈 Trend", "💰 Wealth", "🔥 Burn"])
    with t_sp:
        df_sp = FinanceService.get_spending_by_category(
            sel_year if sel_year != "All" else None,
            sel_month if sel_month != "All" else None,
            fiscal_start_day
        )
        if not df_sp.empty:
            fig = px.bar(df_sp, x='Category', y='Amount', color='Amount',
                         color_continuous_scale='blues', text_auto='.2f')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="#e2e8f0",
                              margin=dict(t=0,b=0,l=0,r=0), plot_bgcolor='rgba(0,0,0,0)')
            fig.update_traces(textfont_color='white')
            st.plotly_chart(fig, use_container_width=True)
        else: empty_state("No Data", "No spending data available.")

    with t_ie:
        df_ie = FinanceService.get_income_expense_by_month(
            sel_year if sel_year != "All" else None,
            sel_month if sel_month != "All" else None,
            fiscal_start_day
        )
        if not df_ie.empty:
            fig_ie = go.Figure(data=[
                go.Bar(name='Income', x=df_ie['Month'], y=df_ie['Income'], marker_color='#4ade80'),
                go.Bar(name='Expense', x=df_ie['Month'], y=df_ie['Expense'], marker_color='#f87171')
            ])
            fig_ie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                 font_color="#e2e8f0", barmode='group',
                                 yaxis=dict(gridcolor='rgba(255,255,255,0.1)'))
            st.plotly_chart(fig_ie, use_container_width=True)
        else: empty_state("No Data", "Income/expense data will appear here.")

    with t_tr:
        df_tr = FinanceService.get_spending_trend(
            sel_year if sel_year != "All" else None,
            sel_month if sel_month != "All" else None,
            fiscal_start_day=fiscal_start_day
        )
        if not df_tr.empty:
            fig_tr = px.line(df_tr, x='Month', y='Amount', markers=True)
            fig_tr.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="#e2e8f0",
                                plot_bgcolor='rgba(255,255,255,0.05)',
                                yaxis=dict(gridcolor='rgba(255,255,255,0.1)'))
            fig_tr.update_traces(line_color='#3b82f6')
            st.plotly_chart(fig_tr, use_container_width=True)
        else: empty_state("No Data", "Spend trend will appear here.")
        
    with t_we:
        ast_val = AssetService.get_total_assets_value()
        fig3 = px.pie(values=[net-ast_val, ast_val], names=['Cash', 'Invested'], hole=0.6)
        fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="#e2e8f0")
        st.plotly_chart(fig3, use_container_width=True)

    with t_bu:
        budget_month = sel_month if sel_month != "All" else None
        budget_year = sel_year if sel_year != "All" else None
        df_b = BudgetService.get_monthly_budgets(month=budget_month, year=budget_year)
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
            all_cats = FinanceService.get_categories()
            filtered = all_cats[all_cats['type'] == txn_type]
            cat_opts = {f"{r['icon']} {r['name']}": r['id'] for _, r in filtered.iterrows()}
            cat_sel = st.selectbox("Category", list(cat_opts.keys()) if cat_opts else ["-"])
            desc = st.text_input("Description", placeholder="What was this for?")
            if st.form_submit_button("Record Transaction", use_container_width=True):
                if cat_sel != "-":
                    full_dt = datetime.combine(dt, datetime.now().time())
                    FinanceService.add_transaction(amt, cat_opts[cat_sel], desc, full_dt, txn_type)
                    st.success("Transaction Logged!")

    with t2:
        df_hist = FinanceService.get_recent_transactions(100)
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
                            FinanceService.delete_transaction(row['ID'])
                            st.session_state['txn_deleted'] = True
                        else:
                            CreditCardService.delete_transaction(row['ID'])
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
            all_cats = FinanceService.get_categories()
            exp_cats = all_cats[all_cats['type'] == 'Expense']
            cat_opts = {f"{r['icon']} {r['name']}": r['id'] for _, r in exp_cats.iterrows()}
            sel_cat = st.selectbox("Category", list(cat_opts.keys()))
            limit = st.number_input("Monthly Limit", min_value=0.01, value=None, placeholder="Enter limit")
            if st.form_submit_button("Lock Budget"):
                BudgetService.add_budget(cat_opts[sel_cat], limit, datetime.now().month, datetime.now().year)
                st.session_state['budget_added'] = True
                st.rerun()
    df_b = BudgetService.get_monthly_budgets()
    if not df_b.empty:
        for _, row in df_b.iterrows():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{row['Category']}**")
                st.progress(min(1.0, row['Progress']))
                st.caption(f"{fmt(row['Spent'])} of {fmt(row['Limit'])}")
            with c2:
                render_delete_button(row['id'], f"del_{row['id']}", BudgetService.delete_budget, "this budget")
    else: empty_state("No Budgets", "Track your spending.")

elif page == "Subscriptions":
    st.markdown('<h1 class="main-header">Recurring Bills</h1>', unsafe_allow_html=True)
    if st.session_state.get('sub_added'):
        st.success("Subscription added!")
        st.session_state['sub_added'] = False
    with st.expander("➕ Add Subscription"):
        with st.form("new_sub"):
            name = st.text_input("Service Name")
            cost = st.number_input("Amount", min_value=0.01, value=None, placeholder="Enter amount")
            icon = st.text_input("Emoji Icon", value="💳")
            cycle = st.selectbox("Cycle", ["Monthly", "Quarterly", "6 Months", "Yearly", "Custom"])
            custom_months = None
            if cycle == "Custom":
                custom_months = st.number_input("Custom Months", min_value=1, value=3, step=1)
            start = st.date_input("Start Date")
            if st.form_submit_button("Track Bill"):
                final_cycle = f"Custom:{custom_months}" if cycle == "Custom" else cycle
                RecurringService.add_subscription(name, cost, final_cycle, start, icon)
                st.session_state['sub_added'] = True
                st.rerun()
    df_s = RecurringService.get_subscriptions()
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
                render_delete_button(row['id'], f"sdel_{row['id']}", RecurringService.delete_subscription, row['Name'])
            st.divider()

elif page == "Loans":
    st.markdown('<h1 class="main-header">Loans Tracker</h1>', unsafe_allow_html=True)

    # Edit mode    # Summary
    loans_all = LoanService.get_loans()
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
                    
                    LoanService.add_loan(person, amount, 'given', interest, start, due, emi_amt, emi_active, tenure, emi_start, notes)
                    st.session_state['loan_added'] = True
                    st.session_state['loan_given_version'] += 1
                    st.rerun()

        loans = LoanService.get_loans('given')
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
                    render_delete_button(row['id'], f"ldel_g_{row['id']}", LoanService.delete_loan, row['person_name'])
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
                    
                    LoanService.add_loan(person, amount_t, 'taken', interest_t, start_t, due_t, emi_amt_t, emi_active_t, tenure_t, emi_start_t, notes)
                    st.session_state['loan_added'] = True
                    st.session_state['loan_taken_version'] += 1
                    st.rerun()

        loans = LoanService.get_loans('taken')
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
                    render_delete_button(row['id'], f"ldel_t_{row['id']}", LoanService.delete_loan, row['person_name'])
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
    df_cards = CreditCardService.get_cards()
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
    upcoming = CreditCardService.get_upcoming_bills(15)
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
                CreditCardService.add_card(cname, cbank, climit, cbilling, cclosing)
                st.session_state['card_added'] = True
                st.session_state['card_add_version'] += 1
                st.rerun()
    df_cards = CreditCardService.get_cards()
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
                    render_delete_button(card['id'], f"cdel_{card['id']}", CreditCardService.delete_card, card['name'])

                # Add transaction form
                st.markdown("**Transactions & EMIs**")
                unlink_cc_val = FinanceService.get_setting('cc_unlink_transactions', 'False') == 'True'
                
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
                                    CreditCardService.add_transaction(card['id'], exp_amt, exp_desc, 'expense', txn_date=full_dt)
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
                                    CreditCardService.add_transaction(card['id'], pay_amt, pay_desc, 'payment', txn_date=full_dt, sync_bank=sync_bank)
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
                                CreditCardService.add_emi(card['id'], emi_desc, emi_total, emi_monthly, emi_tenure, str(emi_date))
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
                                        CreditCardService.delete_transaction(row['id'], description=row['description'], amount=row['amount'])
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
                GoalService.add_goal(gname, target, deadline, icon)
                st.session_state['goal_added'] = True
                st.rerun()
    df_g = GoalService.get_goals()
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
                render_delete_button(row['id'], f"gdel_{row['id']}", GoalService.delete_goal, row['Name'])
            st.divider()

elif page == "Assets":
    st.markdown('<h1 class="main-header">Wealth Portfolio</h1>', unsafe_allow_html=True)
    if st.session_state.get('asset_added'):
        st.success("Asset added!")
        st.session_state['asset_added'] = False
    if st.session_state['edit_asset_id']:
        df_a = AssetService.get_assets()
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
                    AssetService.add_asset(aname, atype, aval)
                    st.session_state['asset_added'] = True
                    st.rerun()
    df_a = AssetService.get_assets()
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
                render_delete_button(row['id'], f"adel_{row['id']}", AssetService.delete_asset, row['Name'])
            st.divider()

elif page == "Settings":
    st.markdown('<h1 class="main-header">Preferences</h1>', unsafe_allow_html=True)

    if st.session_state.get('cat_added'):
        st.success("Category added!")
        st.session_state['cat_added'] = False

    # Currency Settings
    cur_opts = {"INR (₹)": "₹", "USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
    sel_cur = st.selectbox("Preferred Symbol", list(cur_opts.keys()), index=list(cur_opts.values()).index(st.session_state['sym']))
    if st.button("Save Settings"):
        st.session_state['sym'] = cur_opts[sel_cur]
        st.rerun()

    st.divider()

    # Fiscal Month Settings
    st.markdown("### 📅 Fiscal Month")
    st.caption("Set the day your salary arrives. Fiscal month starts on this day.")
    cur_day = FinanceService.get_setting('fiscal_month_start_day', '1')
    cur_day = int(cur_day) if str(cur_day).isdigit() else 1
    new_day = st.number_input("Fiscal Month Start Day", min_value=1, max_value=28, value=cur_day)
    if st.button("Save Fiscal Day"):
        FinanceService.set_setting('fiscal_month_start_day', str(new_day))
        st.success(f"Fiscal month start day set to {new_day}!")
        st.rerun()

    st.divider()

    # Credit Card Settings
    st.markdown("### 💳 Credit Card Settings")
    st.caption("Enable this to focus only on EMIs for Credit Cards.")
    unlink_cc = FinanceService.get_setting('cc_unlink_transactions', 'False') == 'True'
    new_unlink = st.checkbox("Unlink Transactions from Credit Card", value=unlink_cc, 
                            help="If enabled, you can only add EMIs to Credit Cards. Standard Expense/Payment tabs will be hidden.")
    if new_unlink != unlink_cc:
        FinanceService.set_setting('cc_unlink_transactions', str(new_unlink))
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
                if cat_name:
                    import uuid
                    cid = str(uuid.uuid4())
                    db.execute(
                        "INSERT INTO categories (id, name, type, icon) VALUES (?, ?, ?, ?)",
                        (cid, cat_name, cat_type, cat_icon)
                    )
                    st.session_state["cat_added"] = True
                    st.rerun()

    # List Existing Categories
    df_cats = FinanceService.get_categories()
    if not df_cats.empty:
        for _, row in df_cats.iterrows():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"{row['icon']} **{row['name']}** ({row['type']})")
            with c2:
                if st.button("🗑️", key=f"del_cat_{row['id']}"):
                    db.execute("DELETE FROM categories WHERE id = ?", (row['id'],))
                    st.rerun()
