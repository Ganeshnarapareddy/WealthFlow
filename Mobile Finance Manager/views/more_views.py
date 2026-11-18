import html
from datetime import datetime
import streamlit as st

from components.mobile_ui import fmt, m_section, m_empty, m_kpi_strip, m_delete_popover
from components.mobile_nav import SYM_MAP, CODE_BY_SYM


def render_more_hub(user_data: dict):
    """Artboard 6: Clean 2-column iOS More Hub."""
    tiles = [
        ("Budgets", "Budgets", ":material/pie_chart:"),
        ("Subscriptions", "Subscriptions", ":material/autorenew:"),
        ("Loans", "Loans & EMI", ":material/account_balance:"),
        ("Credit Cards", "Credit Cards", ":material/credit_card:"),
        ("Goals", "Goals", ":material/flag:"),
        ("Assets", "Assets", ":material/show_chart:"),
        ("Settings", "Settings", ":material/tune:"),
    ]
    if user_data.get("role") == "admin":
        tiles.append(("Admin", "Users", ":material/group:"))

    for i in range(0, len(tiles), 2):
        c1, c2 = st.columns(2)
        for col, item in zip((c1, c2), tiles[i : i + 2]):
            pid, lbl, ic = item
            with col:
                if st.button(lbl, icon=ic, key=f"m_hub_{pid}", use_container_width=True):
                    st.session_state["m_page"] = pid
                    st.rerun()


def render_budgets_mobile(uid: str, finance_service, budget_service):
    now = datetime.now()
    with st.expander("Set monthly budget", icon=":material/add:"):
        all_cats = finance_service.get_categories(uid)
        exp_cats = all_cats[all_cats["type"] == "Expense"] if not all_cats.empty else all_cats
        cat_map = {f"{r['icon']} {r['name']}": r["id"] for _, r in exp_cats.iterrows()} if not exp_cats.empty else {}
        with st.form("m_new_budget", clear_on_submit=True):
            sel_c = st.selectbox("Category", list(cat_map.keys()) if cat_map else ["-"])
            lim = st.number_input("Monthly Limit", min_value=1.0, value=None, placeholder="0.00", step=500.0)
            if st.form_submit_button("Save Budget", type="primary", use_container_width=True):
                if lim and sel_c != "-":
                    budget_service.add_budget(uid, cat_map[sel_c], lim, now.month, now.year)
                    st.session_state["m_toast"] = "Budget saved!"
                    st.rerun()
                else:
                    st.error("Enter a valid limit.")

    df = budget_service.get_monthly_budgets(uid, now.month, now.year)
    if df.empty:
        m_empty("No budgets this month", "Expand 'Set monthly budget' above to add spending limits.")
        return

    for _, row in df.iterrows():
        pct = min(1.0, max(0.0, float(row["Progress"]) / 100.0))
        tone = "negative" if row["Progress"] >= 100 else ("warning" if row["Progress"] >= 80 else "positive")
        c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<div class="m-list-card">'
                f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(row["Category"]))}</div>'
                f'<div class="m-list-sub">Spent {html.escape(fmt(row["Spent"]))} of {html.escape(fmt(row["Limit"]))}</div></div>'
                f'<span class="m-chip {tone} m-mono">{row["Progress"]:.0f}%</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            m_delete_popover(row["id"], f"mbud_{row['id']}", budget_service.delete_budget, str(row["Category"]), pass_user_id=uid, toast_msg="Budget removed.")
        st.progress(pct)


def render_subscriptions_mobile(uid: str, recurring_service):
    df = recurring_service.get_subscriptions(uid)
    monthly = recurring_service.get_monthly_recurring_total(uid)
    m_kpi_strip(
        hero_label="Monthly recurring burn",
        hero_value=fmt(monthly),
        hero_badge=f"{len(df)} active",
        items=[],
    )

    with st.expander("Add subscription", icon=":material/add:"):
        with st.form("m_new_sub", clear_on_submit=True):
            name = st.text_input("Name *", placeholder="e.g. Netflix, Health Insurance")
            amt = st.number_input("Amount *", min_value=0.01, value=None, placeholder="0.00", step=10.0)
            cycle = st.selectbox("Cycle", ["Monthly", "Quarterly", "6 Months", "Yearly"])
            dt = st.date_input("Start / Last Billed Date", value=datetime.now().date())
            if st.form_submit_button("Add Subscription", type="primary", use_container_width=True):
                if not name.strip() or not amt:
                    st.error("Name and amount are required.")
                else:
                    recurring_service.add_subscription(uid, name.strip(), amt, cycle, dt)
                    st.session_state["m_toast"] = f"Added {name.strip()}!"
                    st.rerun()

    if df.empty:
        m_empty("No subscriptions yet", "Track recurring bills to get renewal alerts on Home.")
        return

    for _, row in df.iterrows():
        cyc_lbl = recurring_service.format_cycle(row["Cycle"])
        c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<div class="m-list-card">'
                f'<div class="m-list-left"><div class="m-list-icon">{html.escape(str(row["Icon"] or "🔄"))}</div>'
                f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(row["Name"]))}</div>'
                f'<div class="m-list-sub">{html.escape(cyc_lbl)} · Next {html.escape(str(row["Next Date"]))}</div></div></div>'
                f'<div class="m-list-amt">{html.escape(fmt(row["Amount"]))}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            m_delete_popover(row["id"], f"msub_{row['id']}", recurring_service.delete_subscription, str(row["Name"]), pass_user_id=uid, toast_msg="Subscription deleted.")


def render_loans_mobile(uid: str, loan_service):
    t_given, t_taken = st.tabs(["Loans Given", "Loans Taken"])
    for tab, ltype, label in ((t_given, "given", "Given"), (t_taken, "taken", "Taken")):
        with tab:
            with st.expander(f"Add Loan {label}", icon=":material/add:"):
                with st.form(f"m_add_loan_{ltype}", clear_on_submit=True):
                    person = st.text_input("Person / Bank *", placeholder="e.g. Sudhir, HDFC")
                    amt = st.number_input("Amount *", min_value=0.01, value=None, placeholder="0.00", step=500.0)
                    due = st.date_input("Due Date", value=datetime.now().date())
                    emi_on = st.checkbox("EMI Loan")
                    emi_amt = st.number_input("Monthly EMI (if EMI)", min_value=0.0, value=None, placeholder="0.00")
                    tenure = st.number_input("Tenure (months)", min_value=0, value=0, step=1)
                    notes = st.text_input("Notes", placeholder="Optional")
                    if st.form_submit_button(f"Save Loan {label}", type="primary", use_container_width=True):
                        if not person.strip() or not amt:
                            st.error("Name and amount are required.")
                        else:
                            loan_service.add_loan(
                                uid, person.strip(), amt, ltype, 0.0, str(datetime.now().date()), str(due),
                                float(emi_amt or 0.0), 1 if emi_on else 0, int(tenure), str(datetime.now().date()), notes.strip()
                            )
                            st.session_state["m_toast"] = f"Loan {label.lower()} saved!"
                            st.rerun()

            df = loan_service.get_loans(uid, ltype)
            if df.empty:
                m_empty(f"No loans {label.lower()}", f"Tap 'Add Loan {label}' above to track balances and due dates.")
            else:
                for _, r in df.iterrows():
                    is_paid = r["status"] == "paid"
                    tone = "positive" if is_paid else "warning"
                    c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
                    with c1:
                        st.markdown(
                            f'<div class="m-list-card">'
                            f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(r["person_name"]))}</div>'
                            f'<div class="m-list-sub">Due {html.escape(str(r["due_date"] or "—"))} · <span class="m-chip {tone}">{html.escape(str(r["status"]).title())}</span></div></div>'
                            f'<div class="m-list-amt">{html.escape(fmt(r["remaining_amount"]))}</div></div>',
                            unsafe_allow_html=True,
                        )
                    with c2:
                        m_delete_popover(r["id"], f"mloan_{r['id']}", loan_service.delete_loan, str(r["person_name"]), pass_user_id=uid, toast_msg="Loan deleted.")


def render_credit_cards_mobile(uid: str, cc_service):
    cards = cc_service.get_cards(uid)
    with st.expander("Add credit card", icon=":material/add:"):
        with st.form("m_add_cc", clear_on_submit=True):
            cname = st.text_input("Card Name *", placeholder="e.g. Millennia, Amex")
            bank = st.text_input("Bank *", placeholder="e.g. HDFC, ICICI")
            lim = st.number_input("Credit Limit *", min_value=1.0, value=None, placeholder="0.00", step=5000.0)
            c1, c2 = st.columns(2)
            with c1:
                bday = st.number_input("Bill Day", min_value=1, max_value=31, value=15)
            with c2:
                cday = st.number_input("Due Day", min_value=1, max_value=31, value=5)
            if st.form_submit_button("Add Card", type="primary", use_container_width=True):
                if not cname.strip() or not bank.strip() or not lim:
                    st.error("Card name, bank, and limit are required.")
                else:
                    cc_service.add_card(uid, cname.strip(), bank.strip(), lim, int(bday), int(cday))
                    st.session_state["m_toast"] = f"Card '{cname.strip()}' added!"
                    st.rerun()

    if cards.empty:
        m_empty("No credit cards yet", "Add a card above to track limits, bills, and EMIs.")
        return

    for _, card in cards.iterrows():
        used = max(0.0, -float(card["current_balance"] or 0.0))
        lim = float(card["card_limit"] or 0.0)
        util = (used / lim * 100) if lim > 0 else 0.0
        tone = "negative" if util >= 75 else ("warning" if util >= 40 else "positive")

        c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<div class="m-list-card">'
                f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(card["name"]))} · {html.escape(str(card["bank"]))}</div>'
                f'<div class="m-list-sub">Limit {html.escape(fmt(lim))} · Due day {int(card["closing_date"] or 1)}</div></div>'
                f'<div style="text-align:right;"><div class="m-list-amt">{html.escape(fmt(used))}</div>'
                f'<span class="m-chip {tone}">{util:.0f}%</span></div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            m_delete_popover(card["id"], f"mcc_{card['id']}", cc_service.delete_card, str(card["name"]), pass_user_id=uid, toast_msg="Card deleted.")
        st.progress(min(1.0, max(0.0, util / 100.0)))

        with st.expander(f"Log swipe or bill payment · {card['name']}"):
            with st.form(f"m_cc_txn_{card['id']}", clear_on_submit=True):
                ttype = st.radio("Type", ["expense", "payment"], horizontal=True, key=f"m_cct_{card['id']}")
                tamt = st.number_input("Amount *", min_value=0.01, value=None, placeholder="0.00", key=f"m_cca_{card['id']}")
                tdesc = st.text_input("Description", placeholder="Merchant or bill payment", key=f"m_ccd_{card['id']}")
                if st.form_submit_button("Save", type="primary", use_container_width=True):
                    if tamt and tamt > 0:
                        cc_service.add_transaction(uid, card["id"], tamt, tdesc.strip() or ttype.title(), ttype, sync_bank=(ttype == "payment"))
                        st.session_state["m_toast"] = f"Card {ttype} logged!"
                        st.rerun()
                    else:
                        st.error("Enter a valid amount.")


def render_goals_mobile(uid: str, goal_service):
    with st.expander("New savings goal", icon=":material/add:"):
        with st.form("m_new_goal", clear_on_submit=True):
            gname = st.text_input("Goal Name *", placeholder="e.g. Emergency Fund, MacBook")
            gtgt = st.number_input("Target Amount *", min_value=1.0, value=None, placeholder="0.00", step=1000.0)
            gdl = st.date_input("Target Date", value=datetime.now().date())
            if st.form_submit_button("Create Goal", type="primary", use_container_width=True):
                if not gname.strip() or not gtgt:
                    st.error("Name and target are required.")
                else:
                    goal_service.add_goal(uid, gname.strip(), gtgt, gdl)
                    st.session_state["m_toast"] = f"Goal '{gname.strip()}' added!"
                    st.rerun()

    df = goal_service.get_goals(uid)
    if df.empty:
        m_empty("No goals yet", "Create a savings goal above to track your progress.")
        return

    for _, row in df.iterrows():
        cur = float(row["Current"] or 0.0)
        tgt = float(row["Target"] or 1.0)
        pct = min(1.0, max(0.0, cur / tgt))
        c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<div class="m-list-card">'
                f'<div class="m-list-left"><div class="m-list-icon">{html.escape(str(row["Icon"] or "🎯"))}</div>'
                f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(row["Name"]))}</div>'
                f'<div class="m-list-sub">{html.escape(fmt(cur))} / {html.escape(fmt(tgt))}</div></div></div>'
                f'<span class="m-chip accent m-mono">{pct*100:.0f}%</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            m_delete_popover(row["id"], f"mgoal_{row['id']}", goal_service.delete_goal, str(row["Name"]), pass_user_id=uid, toast_msg="Goal deleted.")
        st.progress(pct)
        gc1, gc2 = st.columns([0.65, 0.35], vertical_alignment="center")
        with gc1:
            add_v = st.number_input("Top up", min_value=0.01, value=None, placeholder="Top-up amount", label_visibility="collapsed", key=f"m_gadd_{row['id']}")
        with gc2:
            if st.button("+ Add", key=f"m_gbtn_{row['id']}", use_container_width=True):
                if add_v and add_v > 0:
                    goal_service.contribute(row["id"], add_v)
                    st.session_state["m_toast"] = f"Added {fmt(add_v)} to {row['Name']}!"
                    st.rerun()


def render_assets_mobile(uid: str, asset_service):
    df = asset_service.get_assets(uid)
    total = float(df["Value"].sum()) if not df.empty else 0.0
    m_kpi_strip(hero_label="Total assets", hero_value=fmt(total), hero_badge=f"{len(df)} holdings", items=[])

    with st.expander("Add asset", icon=":material/add:"):
        with st.form("m_new_asset", clear_on_submit=True):
            aname = st.text_input("Asset Name *", placeholder="e.g. Nifty 50 Index, Gold")
            atype = st.selectbox("Type", ["Stocks", "Mutual Funds", "Real Estate", "Gold", "Crypto", "FD / Cash", "Other"])
            aval = st.number_input("Current Value *", min_value=0.01, value=None, placeholder="0.00", step=1000.0)
            if st.form_submit_button("Add Asset", type="primary", use_container_width=True):
                if not aname.strip() or not aval:
                    st.error("Asset name and value are required.")
                else:
                    asset_service.add_asset(aname.strip(), atype, aval, uid)
                    st.session_state["m_toast"] = f"Asset '{aname.strip()}' added!"
                    st.rerun()

    if df.empty:
        m_empty("No assets tracked", "Add your investments and holdings above.")
        return

    for _, row in df.iterrows():
        c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<div class="m-list-card">'
                f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(row["Name"]))}</div>'
                f'<div class="m-list-sub">{html.escape(str(row["Type"]))}</div></div>'
                f'<div class="m-list-amt" style="color:#34D399;">{html.escape(fmt(row["Value"]))}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            m_delete_popover(row["id"], f"mast_{row['id']}", asset_service.delete_asset, str(row["Name"]), pass_user_id=uid, toast_msg="Asset removed.")


def render_settings_mobile(uid: str, user_data: dict, finance_service, auth_service):
    m_section("Preferences")
    labels = list(SYM_MAP.keys())
    cur_sym = st.session_state.get("sym", "₹")
    try:
        c_idx = list(SYM_MAP.values()).index(cur_sym)
    except ValueError:
        c_idx = 0
    sel_c = st.selectbox("Display Currency", labels, index=c_idx, key="m_set_curr")
    if SYM_MAP[sel_c] != cur_sym:
        new_sym = SYM_MAP[sel_c]
        st.session_state["sym"] = new_sym
        finance_service.set_setting("currency_symbol", new_sym, uid)
        finance_service.set_setting("currency", CODE_BY_SYM.get(new_sym, "INR"), uid)
        st.session_state["m_toast"] = f"Currency switched to {sel_c}."
        st.rerun()

    fday_raw = finance_service.get_setting("fiscal_month_start_day", "1", uid)
    fday_cur = int(fday_raw) if str(fday_raw).isdigit() else 1
    with st.form("m_fiscal_form"):
        fday = st.number_input("Fiscal Month Start Day (1–28)", min_value=1, max_value=28, value=min(28, max(1, fday_cur)))
        if st.form_submit_button("Save Fiscal Day", type="primary", use_container_width=True):
            finance_service.set_setting("fiscal_month_start_day", str(int(fday)), uid)
            st.session_state["m_toast"] = f"Fiscal start day set to {int(fday)}."
            st.rerun()

    m_section("Edit profile")
    with st.form("m_edit_prof_form"):
        u_name = st.text_input("Username", value=user_data.get("username", ""))
        u_email = st.text_input("Email", value=user_data.get("email", "") or "")
        u_phone = st.text_input("Phone", value=user_data.get("phone", "") or "")
        if st.form_submit_button("Update Profile", type="primary", use_container_width=True):
            ok, msg = auth_service.update_profile(uid, u_name.strip(), u_email.strip(), u_phone.strip())
            if ok:
                st.session_state.user["username"] = u_name.strip()
                st.session_state.user["email"] = u_email.strip()
                st.session_state.user["phone"] = u_phone.strip()
                st.session_state["m_toast"] = "Profile updated!"
                st.rerun()
            else:
                st.error(msg)


def render_admin_mobile(auth_service):
    users = auth_service.get_all_users()
    if not users:
        m_empty("No users found", "User accounts appear here.")
        return
    for u in users:
        uname = u[1] if len(u) > 1 else "User"
        role = u[3] if len(u) > 3 else "user"
        status = u[6] if len(u) > 6 else "active"
        st.markdown(
            f'<div class="m-list-card">'
            f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(uname))}</div>'
            f'<div class="m-list-sub">Role: {html.escape(str(role))} · Status: {html.escape(str(status))}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
