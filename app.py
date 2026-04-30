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
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'sym' not in st.session_state: st.session_state['sym'] = '₹'
if 'edit_asset_id' not in st.session_state: st.session_state['edit_asset_id'] = None

apply_styles()

def fmt(val):
    return f"{st.session_state['sym']}{val:,.2f}"

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='margin:0; color:white; font-weight:800; font-size:2.2rem;'>💎 WealthFlow</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-bottom:0;'>Smart Personal Finance</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 0.75rem; font-style: italic;'>made by Ganesh Narapareddy</p>", unsafe_allow_html=True)
    
    st.divider()
    
    page = st.radio(
        "Navigation",
        ["Dashboard", "Transactions", "Budgets", "Subscriptions", "Goals", "Assets", "Settings"],
        index=0
    )
    
    st.divider()
    if st.button("🔄 Hard Reset Cache", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# --- PAGES ---

if page == "Dashboard":
    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown('<h1 class="main-header">Command Center</h1>', unsafe_allow_html=True)
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
    
    tab_spend, tab_flow, tab_wealth, tab_burn = st.tabs([
        "📊 Spending Mix", "📉 Cash Flow", "💰 Wealth Split", "🔥 Burn Rate"
    ])
    
    with tab_spend:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            df_sp = FinanceService.get_spending_by_category()
            if not df_sp.empty:
                fig = px.pie(df_sp, values='Amount', names='Category', hole=0.5,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                  font_color="#e2e8f0", margin=dict(t=10, b=10, l=0, r=0),
                                  legend=dict(orientation="h", y=-0.1))
                st.plotly_chart(fig, use_container_width=True)
            else:
                empty_state("No Data", "Log transactions to see spending distribution.")
        with c2:
            section_header("Recent Pulse")
            df_r = FinanceService.get_recent_transactions(6)
            if not df_r.empty:
                for _, r in df_r.iterrows():
                    color = "#f87171" if r['Type'] == 'Expense' else "#4ade80"
                    sign = "-" if r['Type'] == 'Expense' else "+"
                    st.markdown(
                        f"<div style='display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05);'>"
                        f"<span>{r['Icon']} {r['Description'] or r['Category']}</span>"
                        f"<span style='color:{color}; font-weight:600'>{sign}{fmt(r['Amount'])}</span>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No recent transactions.")

    with tab_flow:
        if inc > 0 or exp > 0:
            fig2 = go.Figure(data=[
                go.Bar(name='Income', x=['This Month'], y=[inc], marker_color='#4ade80', text=fmt(inc), textposition='auto'),
                go.Bar(name='Expense', x=['This Month'], y=[exp], marker_color='#f87171', text=fmt(exp), textposition='auto')
            ])
            fig2.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', 
                               plot_bgcolor='rgba(0,0,0,0)', font_color="#e2e8f0",
                               margin=dict(t=20, b=20))
            st.plotly_chart(fig2, use_container_width=True)
            
            surplus = inc - exp
            s_color = "#4ade80" if surplus >= 0 else "#f87171"
            st.markdown(f"<div style='text-align:center; font-size:1.4rem; font-weight:700; color:{s_color}'>Surplus: {fmt(surplus)}</div>", unsafe_allow_html=True)
        else:
            empty_state("No Flow Data", "Income & expense data will appear here.")

    with tab_wealth:
        acc_bal = net - AssetService.get_total_assets_value()
        ast_val = AssetService.get_total_assets_value()
        fig3 = px.pie(values=[acc_bal, ast_val], names=['Liquid Cash', 'Invested Assets'],
                      color_discrete_sequence=['#3b82f6', '#8b5cf6'], hole=0.6)
        fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                           font_color="#e2e8f0", margin=dict(t=10, b=10, l=0, r=0))
        st.plotly_chart(fig3, use_container_width=True)

    with tab_burn:
        df_b = BudgetService.get_monthly_budgets()
        total_limit = df_b['Limit'].sum() if not df_b.empty else 0
        if total_limit > 0:
            fig4 = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = exp,
                gauge = {'axis': {'range': [None, total_limit]}, 'bar': {'color': "#3b82f6"}}
            ))
            fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#e2e8f0"})
            st.plotly_chart(fig4, use_container_width=True)
        else:
            empty_state("No Budgets", "Set budgets to see burn rate.")

elif page == "Transactions":
    st.markdown('<h1 class="main-header">Ledger</h1>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["➕ Add Entry", "📜 History"])
    
    with t1:
        # Use a simpler layout for the form to avoid React loops on mobile
        with st.form("add_txn_pro", clear_on_submit=True):
            txn_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
            amt = st.number_input("Amount", min_value=0.0, step=1.0)
            
            # Use columns only if not on a very small screen (Streamlit handles this, but let's be safe)
            c1, c2 = st.columns(2)
            with c1: dt = st.date_input("Date", value=datetime.now())
            with c2: tm = st.time_input("Time", value=datetime.now().time())
            
            all_cats = FinanceService.get_categories()
            filtered = all_cats[all_cats['type'] == txn_type]
            cat_opts = {f"{r['icon']} {r['name']}": r['id'] for _, r in filtered.iterrows()}
            cat_sel = st.selectbox("Category", list(cat_opts.keys()) if cat_opts else ["-"])
            desc = st.text_input("Description", placeholder="What was this for?")
            
            if st.form_submit_button("Record Transaction", use_container_width=True):
                if cat_sel != "-":
                    full_dt = datetime.combine(dt, tm)
                    FinanceService.add_transaction(amt, cat_opts[cat_sel], desc, full_dt, txn_type)
                    st.success("Transaction Logged!")
                    # No st.rerun() here - let the form submission handle the refresh

    with t2:
        df_hist = FinanceService.get_recent_transactions(100)
        if not df_hist.empty:
            disp_df = df_hist.copy()
            disp_df['Amount'] = disp_df.apply(lambda r: f"{'-' if r['Type']=='Expense' else '+'} {fmt(r['Amount'])}", axis=1)
            st.dataframe(disp_df[['Date', 'Icon', 'Description', 'Category', 'Amount']], use_container_width=True, hide_index=True)
        else:
            empty_state("No History", "Start logging transactions to see them here.")

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
                prog = min(1.0, row['Progress'])
                st.progress(prog)
                st.caption(f"{fmt(row['Spent'])} of {fmt(row['Limit'])}")
            with c2:
                if st.button("🗑️", key=f"del_{row['id']}"):
                    BudgetService.delete_budget(row['id'])
                    st.rerun()
    else:
        empty_state("No Budgets", "Set limits to track your spending.")

elif page == "Subscriptions":
    st.markdown('<h1 class="main-header">Recurring Bills</h1>', unsafe_allow_html=True)
    with st.expander("➕ Add Subscription"):
        with st.form("new_sub"):
            name = st.text_input("Service Name")
            cost = st.number_input("Amount", min_value=0.0)
            icon = st.text_input("Emoji Icon", value="💳")
            cycle = st.selectbox("Billing Cycle", ["Monthly", "Quarterly", "6 Months", "Yearly"])
            start = st.date_input("Start Date")
            if st.form_submit_button("Track Bill"):
                RecurringService.add_subscription(name, cost, cycle, start, icon)
                st.rerun()
                
    df_s = RecurringService.get_subscriptions()
    if not df_s.empty:
        for _, row in df_s.iterrows():
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.markdown(f"**{row['Icon']} {row['Name']}**")
                st.caption(f"{row['Cycle']}")
            with c2:
                st.markdown(f"**{fmt(row['Amount'])}**")
                st.caption(f"Next: {row['Next Date']}")
            with c3:
                if st.button("🗑️", key=f"sdel_{row['id']}"):
                    RecurringService.delete_subscription(row['id'])
                    st.rerun()
            st.divider()

elif page == "Goals":
    st.markdown('<h1 class="main-header">Piggy Bank</h1>', unsafe_allow_html=True)
    with st.expander("➕ Create New Goal"):
        with st.form("new_goal"):
            gname = st.text_input("What are we saving for?")
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
            with ac1:
                st.markdown(f"**{row['Name']}**")
                st.caption(row['Type'])
            with ac2:
                st.markdown(f"**{fmt(row['Value'])}**")
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
