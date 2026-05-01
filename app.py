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
    h1, h2, h3, h4 = st.columns([2, 1.2, 1.2, 1.2])
    with h1: st.markdown('<h1 class="main-header">Command Center</h1>', unsafe_allow_html=True)
    with h2:
        # Year selector with "All" option
        years = FinanceService.get_available_years()
        year_options = ["All"] + [str(y) for y in years]
        if 'selected_year' not in st.session_state:
            st.session_state['selected_year'] = "All"
        try:
            year_idx = year_options.index(str(st.session_state['selected_year']))
        except:
            year_idx = 0
        sel_year_str = st.selectbox("Year", year_options, index=year_idx, label_visibility="collapsed", key="year_sel")
        sel_year = "All" if sel_year_str == "All" else int(sel_year_str)
        if sel_year != st.session_state['selected_year']:
            st.session_state['selected_year'] = sel_year
            st.rerun()

    with h3:
        # Month selector with "All" option
        month_display = ["All", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        if 'selected_month' not in st.session_state:
            st.session_state['selected_month'] = "All"
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

    # Get all metrics with filtering
    net = FinanceService.get_net_worth()
    burn = RecurringService.get_monthly_recurring_total()
    inc, exp = FinanceService.get_monthly_income_vs_expense(
        sel_year, sel_month
    )
    today_spent, yesterday_spent = FinanceService.get_today_vs_yesterday()
    day_pct = ((today_spent - yesterday_spent) / yesterday_spent * 100) if yesterday_spent > 0 else 0

    # Get comparison data
    prev_inc, prev_exp, prev_label = FinanceService.get_previous_period_data(sel_year, sel_month)
    inc_delta_str, inc_increased = FinanceService.get_comparison_delta(inc, prev_inc)
    exp_delta_str, exp_increased = FinanceService.get_comparison_delta(exp, prev_exp)

    # Savings rate and comparison
    savings_rate = ((inc - exp) / inc * 100) if inc > 0 else 0.0
    prev_savings_rate = ((prev_inc - prev_exp) / prev_inc * 100) if prev_inc > 0 else 0.0
    sr_delta_str, sr_increased = FinanceService.get_comparison_delta(savings_rate, prev_savings_rate)

    # Top category and comparison
    top_cat, top_amt, prev_top_amt, top_delta_str, top_increased = FinanceService.get_top_category_comparison(
        sel_year, sel_month
    )

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
    with a2: card_metric("Top Category", top_cat if top_cat else "N/A",
                         delta=top_delta_str)
    with a3: card_metric("Subscriptions", fmt(burn) if burn > 0 else "N/A",
                         delta=burn_delta_str,
                         delta_color="inverse")

    # Smart Alerts Section
    st.markdown("### 🔔 Smart Alerts")
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
    else:
        st.caption("No upcoming renewals")

    st.markdown("<br>", unsafe_allow_html=True)

    # Dashboard Tabs
    t_sp, t_ie, t_tr, t_we, t_bu = st.tabs(["📊 Spending", "📊 Income/Expense", "📈 Trend", "💰 Wealth", "🔥 Burn"])
    with t_sp:
        df_sp = FinanceService.get_spending_by_category(
            sel_year if sel_year != "All" else None,
            sel_month if sel_month != "All" else None
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
            sel_month if sel_month != "All" else None
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
            sel_month if sel_month != "All" else None
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
            disp_df = df_hist.copy()
            disp_df['Amount'] = disp_df.apply(lambda r: f"{-r['Amount']:,.2f}" if r['Type']=='Expense' else f"{r['Amount']:,.2f}", axis=1)
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
            limit = st.number_input("Monthly Limit", min_value=0.01, value=None, placeholder="Enter limit")
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
                render_delete_button(row['id'], f"del_{row['id']}", BudgetService.delete_budget, "this budget")
    else: empty_state("No Budgets", "Track your spending.")

elif page == "Subscriptions":
    st.markdown('<h1 class="main-header">Recurring Bills</h1>', unsafe_allow_html=True)
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

elif page == "Goals":
    st.markdown('<h1 class="main-header">Piggy Bank</h1>', unsafe_allow_html=True)
    with st.expander("➕ Create New Goal"):
        with st.form("new_goal"):
            gname = st.text_input("Saving for…")
            target = st.number_input("Target Amount", min_value=0.01, value=None, placeholder="Enter target")
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
    cur_opts = {"INR (₹)": "₹", "USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
    sel_cur = st.selectbox("Preferred Symbol", list(cur_opts.keys()), index=list(cur_opts.values()).index(st.session_state['sym']))
    if st.button("Save Settings"):
        st.session_state['sym'] = cur_opts[sel_cur]
        st.rerun()
