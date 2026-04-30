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

# Import UI Components
from components.styles import apply_styles
from components.ui_elements import card_metric, section_header, empty_state

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
    return f"{st.session_state['sym']}{val:,.2f}"

page = st.session_state['page']

if page == "Dashboard":
    h1, h2 = st.columns([3, 1])
    with h1: st.markdown('<h1 class="main-header">Command Center</h1>', unsafe_allow_html=True)
    with h2:
        sym_map = {"INR (₹)": "₹", "USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
        try: curr_idx = list(sym_map.values()).index(st.session_state['sym'])
        except: curr_idx = 0
        cur_label = st.selectbox("Currency", list(sym_map.keys()), index=curr_idx, label_visibility="collapsed")
        if sym_map[cur_label] != st.session_state['sym']:
            st.session_state['sym'] = sym_map[cur_label]
            st.rerun()

    net = FinanceService.get_net_worth()
    burn = RecurringService.get_monthly_recurring_total()
    inc, exp = FinanceService.get_monthly_income_vs_expense()

    m1, m2, m3, m4 = st.columns([1, 1, 1, 1])
    with m1: card_metric("Net Worth", fmt(net))
    with m2: card_metric("Monthly Burn", fmt(burn))
    with m3: card_metric("Monthly Income", fmt(inc))
    with m4: card_metric("Monthly Spent", fmt(exp))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    t_sp, t_fl, t_we, t_bu = st.tabs(["📊 Spending", "📉 Cash Flow", "💰 Wealth", "🔥 Burn"])
    with t_sp:
        df_sp = FinanceService.get_spending_by_category()
        if not df_sp.empty:
            fig = px.pie(df_sp, values='Amount', names='Category', hole=0.5)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="#e2e8f0", margin=dict(t=0,b=0,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)
        else: empty_state("No Data", "Log entries to see mix.")
        
    with t_fl:
        if inc > 0 or exp > 0:
            fig2 = go.Figure(data=[
                go.Bar(name='In', x=['Month'], y=[inc], marker_color='#4ade80'),
                go.Bar(name='Out', x=['Month'], y=[exp], marker_color='#f87171')
            ])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#e2e8f0")
            st.plotly_chart(fig2, use_container_width=True)
        else: empty_state("No Data", "Flow data will appear here.")
        
    with t_we:
        ast_val = AssetService.get_total_assets_value()
        fig3 = px.pie(values=[net-ast_val, ast_val], names=['Cash', 'Invested'], hole=0.6)
        fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="#e2e8f0")
        st.plotly_chart(fig3, use_container_width=True)

    with t_bu:
        df_b = BudgetService.get_monthly_budgets()
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
            amt = st.number_input("Amount", min_value=0.0, step=1.0)
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
            disp_df = df_hist.copy()
            disp_df['Amount'] = disp_df.apply(lambda r: f"{'-' if r['Type']=='Expense' else '+'} {fmt(r['Amount'])}", axis=1)
            st.dataframe(disp_df[['Date', 'Icon', 'Description', 'Category', 'Amount']], use_container_width=True, hide_index=True)
        else: empty_state("No History", "Log transactions to see them here.")

elif page == "Budgets":
    st.markdown('<h1 class="main-header">Guardrails</h1>', unsafe_allow_html=True)
    with st.expander("➕ Set New Budget"):
        with st.form("new_budget"):
            all_cats = FinanceService.get_categories()
            exp_cats = all_cats[all_cats['type'] == 'Expense']
            cat_opts = {f"{r['icon']} {r['name']}": r['id'] for _, r in exp_cats.iterrows()}
            sel_cat = st.selectbox("Category", list(cat_opts.keys()))
            limit = st.number_input("Monthly Limit", min_value=1.0)
            if st.form_submit_button("Lock Budget"):
                BudgetService.add_budget(cat_opts[sel_cat], limit, datetime.now().month, datetime.now().year)
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
                if st.button("🗑️", key=f"del_{row['id']}"):
                    BudgetService.delete_budget(row['id'])
                    st.rerun()
    else: empty_state("No Budgets", "Track your spending.")

elif page == "Subscriptions":
    st.markdown('<h1 class="main-header">Recurring Bills</h1>', unsafe_allow_html=True)
    with st.expander("➕ Add Subscription"):
        with st.form("new_sub"):
            name = st.text_input("Service Name")
            cost = st.number_input("Amount", min_value=0.0)
            icon = st.text_input("Emoji Icon", value="💳")
            cycle = st.selectbox("Cycle", ["Monthly", "Quarterly", "6 Months", "Yearly"])
            start = st.date_input("Start Date")
            if st.form_submit_button("Track Bill"):
                RecurringService.add_subscription(name, cost, cycle, start, icon)
                st.rerun()
    df_s = RecurringService.get_subscriptions()
    if not df_s.empty:
        for _, row in df_s.iterrows():
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1: st.markdown(f"**{row['Icon']} {row['Name']}**")
            with c2: st.markdown(f"**{fmt(row['Amount'])}**")
            with c3:
                if st.button("🗑️", key=f"sdel_{row['id']}"):
                    RecurringService.delete_subscription(row['id'])
                    st.rerun()
            st.divider()

elif page == "Goals":
    st.markdown('<h1 class="main-header">Piggy Bank</h1>', unsafe_allow_html=True)
    with st.expander("➕ Create New Goal"):
        with st.form("new_goal"):
            gname = st.text_input("Saving for…")
            target = st.number_input("Target Amount", min_value=1.0)
            deadline = st.date_input("Target Date")
            icon = st.text_input("Emoji Logo", value="🎯")
            if st.form_submit_button("Create Goal"):
                GoalService.add_goal(gname, target, deadline, icon)
                st.rerun()
    df_g = GoalService.get_goals()
    if not df_g.empty:
        for _, row in df_g.iterrows():
            st.markdown(f"### {row['Icon']} {row['Name']}")
            prog = min(1.0, row['Current'] / row['Target']) if row['Target'] > 0 else 0
            st.progress(prog)
            st.write(f"Saved: **{fmt(row['Current'])}** / {fmt(row['Target'])}")
            gc1, gc2, gc3 = st.columns([2, 1, 1])
            with gc1: add_val = st.number_input("Add", min_value=0.0, key=f"add_{row['id']}")
            with gc2: 
                if st.button("💰 Save", key=f"btn_{row['id']}"):
                    GoalService.contribute(row['id'], add_val)
                    st.rerun()
            with gc3:
                if st.button("🗑️", key=f"gdel_{row['id']}"):
                    GoalService.delete_goal(row['id'])
                    st.rerun()
            st.divider()

elif page == "Assets":
    st.markdown('<h1 class="main-header">Wealth Portfolio</h1>', unsafe_allow_html=True)
    if st.session_state['edit_asset_id']:
        df_a = AssetService.get_assets()
        asset_to_edit = df_a[df_a['id'] == st.session_state['edit_asset_id']].iloc[0]
        with st.form("edit_asset_form"):
            en_name = st.text_input("Name", value=asset_to_edit['Name'])
            en_type = st.selectbox("Type", ["Mutual Fund", "Stock", "Crypto", "Gold", "Real Estate", "FD", "Other"], 
                                  index=["Mutual Fund", "Stock", "Crypto", "Gold", "Real Estate", "FD", "Other"].index(asset_to_edit['Type']))
            en_val = st.number_input("Value", min_value=0.0, value=float(asset_to_edit['Value']))
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
                atype = st.selectbox("Type", ["Mutual Fund", "Stock", "Crypto", "Gold", "Real Estate", "FD", "Other"])
                aval = st.number_input("Current Value", min_value=0.0)
                if st.form_submit_button("Add Asset"):
                    AssetService.add_asset(aname, atype, aval)
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
                if st.button("🗑️", key=f"adel_{row['id']}"):
                    AssetService.delete_asset(row['id'])
                    st.rerun()
            st.divider()

elif page == "Settings":
    st.markdown('<h1 class="main-header">Preferences</h1>', unsafe_allow_html=True)
    cur_opts = {"INR (₹)": "₹", "USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
    sel_cur = st.selectbox("Preferred Symbol", list(cur_opts.keys()), index=list(cur_opts.values()).index(st.session_state['sym']))
    if st.button("Save Settings"):
        st.session_state['sym'] = cur_opts[sel_cur]
        st.rerun()
