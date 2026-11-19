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


def render_credit_cards_mobile(uid: str, cc_service, finance_service=None):
    unlink_cc = False
    if finance_service:
        unlink_cc = finance_service.get_setting("cc_unlink_transactions", "False", uid) == "True"

    if unlink_cc:
        st.markdown(
            '<div style="margin-bottom:12px;display:flex;align-items:center;gap:8px;">'
            '<span class="m-chip accent">EMIs Only</span>'
            '<span style="font-size:12px;color:var(--m-ink-3);">Card swipe logging disabled per settings.</span>'
            '</div>',
            unsafe_allow_html=True,
        )

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

        if not unlink_cc:
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

    m_section("Credit Card Settings")
    unlink_cc = finance_service.get_setting("cc_unlink_transactions", "False", uid) == "True"
    new_unlink = st.toggle(
        "Unlink Transactions from Credit Card",
        value=unlink_cc,
        key="m_cc_unlink_pref",
        help="When enabled, credit cards focus strictly on EMIs. Standard expense swipe logging is hidden.",
    )
    if new_unlink != unlink_cc:
        finance_service.set_setting("cc_unlink_transactions", str(new_unlink), uid)
        st.session_state["m_toast"] = f"Credit card transactions {'unlinked' if new_unlink else 'linked'}."
        st.rerun()

    m_section("Categories")
    cat_view = st.segmented_control(
        "Category Filter",
        ["All", "Expense", "Income"],
        default="All",
        key="m_cat_filter_seg",
        label_visibility="collapsed",
    )

    with st.expander("New category", icon=":material/add:"):
        with st.form("m_new_cat_form", clear_on_submit=True):
            c_name = st.text_input("Category Name *", placeholder="e.g. Dining Out, Freelance")
            c_type = st.radio("Type", ["Expense", "Income"], horizontal=True, key="m_new_cat_type")
            c_icon = st.text_input("Emoji / Icon", value="🏷️", max_chars=4, placeholder="e.g. 🍔, 🚗, 💼")
            if st.form_submit_button("Add Category", type="primary", use_container_width=True):
                if not c_name.strip():
                    st.error("Category name is required.")
                else:
                    ok, msg = finance_service.add_category(c_name.strip(), c_type, c_icon.strip(), uid)
                    if ok:
                        st.session_state["m_toast"] = f"Category '{c_name.strip()}' added!"
                        st.rerun()
                    else:
                        st.error(msg)

    df_cats = finance_service.get_categories(uid)
    if not df_cats.empty:
        if cat_view and cat_view != "All":
            df_cats = df_cats[df_cats["type"].str.lower() == cat_view.lower()]
        with st.expander(f"View & Manage Categories ({len(df_cats)})", expanded=False, icon=":material/format_list_bulleted:"):
            for _, row in df_cats.iterrows():
                cid = row["id"]
                cname = str(row["name"])
                ctype = str(row["type"])
                cicon = str(row["icon"] or "🏷️")
                is_system = not row.get("user_id")
                type_tone = "negative" if ctype.lower() == "expense" else "positive"

                if is_system:
                    st.markdown(
                        f'<div class="m-list-card">'
                        f'<div class="m-list-left">'
                        f'<div class="m-list-icon">{html.escape(cicon)}</div>'
                        f'<div style="min-width:0;"><div class="m-list-title">{html.escape(cname)}</div>'
                        f'<div class="m-list-sub"><span class="m-chip {type_tone}">{html.escape(ctype)}</span>'
                        f'<span class="m-chip neutral" style="margin-left:4px;">Core</span></div></div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    c_main, c_edit, c_del = st.columns([0.72, 0.14, 0.14], vertical_alignment="center")
                    with c_main:
                        st.markdown(
                            f'<div class="m-list-card">'
                            f'<div class="m-list-left">'
                            f'<div class="m-list-icon">{html.escape(cicon)}</div>'
                            f'<div style="min-width:0;"><div class="m-list-title">{html.escape(cname)}</div>'
                            f'<div class="m-list-sub"><span class="m-chip {type_tone}">{html.escape(ctype)}</span>'
                            f'<span class="m-chip accent" style="margin-left:4px;">Custom</span></div></div>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )
                    with c_edit:
                        with st.popover("", icon=":material/edit:", help=f"Edit {cname}"):
                            with st.form(f"m_edit_cat_form_{cid}"):
                                ed_name = st.text_input("Name", value=cname, key=f"m_ed_name_{cid}")
                                ed_icon = st.text_input("Icon", value=cicon, max_chars=4, key=f"m_ed_ico_{cid}")
                                if st.form_submit_button("Save", type="primary", use_container_width=True):
                                    ok, msg = finance_service.update_category(cid, ed_name.strip(), ed_icon.strip(), uid)
                                    if ok:
                                        st.session_state["m_toast"] = f"Updated '{ed_name.strip()}'!"
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    with c_del:
                        m_delete_popover(
                            cid,
                            f"m_cat_del_{cid}",
                            finance_service.delete_category,
                            item_name=cname,
                            pass_user_id=uid,
                            toast_msg=f"Category '{cname}' deleted.",
                        )
    else:
        m_empty("No categories", "Tap + to create a custom category.")

    m_section("Edit profile")
    with st.form("m_edit_prof_form"):
        u_name = st.text_input("Username", value=user_data.get("username", ""))
        u_email = st.text_input("Email", value=user_data.get("email", "") or "")
        u_phone = st.text_input("Phone", value=user_data.get("phone", "") or "")
        if st.form_submit_button("Update Profile", type="primary", use_container_width=True):
            res = auth_service.update_profile(uid, u_name.strip(), u_email.strip(), u_phone.strip())
            if res is True:
                st.session_state.user["username"] = u_name.strip()
                st.session_state.user["email"] = u_email.strip()
                st.session_state.user["phone"] = u_phone.strip()
                st.session_state["m_toast"] = "Profile updated!"
                st.rerun()
            else:
                st.error(str(res))


def render_admin_mobile(auth_service):
    with st.expander("Create new user", icon=":material/person_add:"):
        with st.form("m_admin_new_user", clear_on_submit=True):
            new_u = st.text_input("Username *", placeholder="Choose username")
            new_p = st.text_input("Password *", type="password", placeholder="At least 6 characters")
            new_e = st.text_input("Email", placeholder="you@example.com")
            new_ph = st.text_input("Phone", placeholder="+91...")
            new_r = st.selectbox("Role", ["user", "admin"])
            if st.form_submit_button("Create User", type="primary", use_container_width=True):
                if not new_u.strip():
                    st.error("Username is required.")
                elif not new_p or len(new_p) < 6:
                    st.error("Password must be at least 6 characters.")
                elif not new_e.strip() and not new_ph.strip():
                    st.error("Email or Phone is mandatory.")
                else:
                    uid_res = auth_service.signup(new_u.strip(), new_p, new_e.strip(), new_ph.strip(), role=new_r)
                    if isinstance(uid_res, str) and len(uid_res) == 36 and "-" in uid_res:
                        st.session_state["m_toast"] = f"User '{new_u.strip()}' created!"
                        st.rerun()
                    else:
                        st.error(str(uid_res))

    users = auth_service.get_all_users()
    if not users:
        m_empty("No users found", "User accounts appear here.")
        return

    active_cnt = sum(1 for u in users if len(u) > 6 and str(u[6]).lower() == "active")
    arch_cnt = len(users) - active_cnt
    m_kpi_strip([
        {"label": "Total Accounts", "value": str(len(users))},
        {"label": "Active Users", "value": str(active_cnt), "delta": "active", "tone": "positive"},
        {"label": "Archived Users", "value": str(arch_cnt), "delta": "archived" if arch_cnt > 0 else "none", "tone": "negative" if arch_cnt > 0 else "neutral"},
    ])

    m_section("Registered users")
    for u in users:
        uid_raw = str(u[0])
        uname = str(u[1]) if len(u) > 1 and u[1] else "User"
        urole = str(u[2]).lower() if len(u) > 2 and u[2] else "user"
        uemail = str(u[3]) if len(u) > 3 and u[3] else ""
        uphone = str(u[4]) if len(u) > 4 and u[4] else ""
        usid = str(u[5]) if len(u) > 5 and u[5] else ""
        ustatus = str(u[6]).lower() if len(u) > 6 and u[6] else "active"
        ucreated = str(u[7]) if len(u) > 7 and u[7] else ""

        role_chip = '<span class="m-chip positive" style="font-size:10px; padding:2px 6px;">ADMIN</span>' if urole == 'admin' else '<span class="m-chip muted" style="font-size:10px; padding:2px 6px;">USER</span>'
        status_chip = '<span class="m-chip positive" style="font-size:10px; padding:2px 6px;">ACTIVE</span>' if ustatus == 'active' else '<span class="m-chip negative" style="font-size:10px; padding:2px 6px;">ARCHIVED</span>'

        meta_parts = []
        if usid:
            meta_parts.append(f"ID: {html.escape(str(usid))}")
        if uemail:
            meta_parts.append(f"📧 {html.escape(uemail)}")
        if uphone:
            meta_parts.append(f"📱 {html.escape(uphone)}")
        meta_text = " · ".join(meta_parts) if meta_parts else "No contact details"

        st.markdown(
            f'<div class="m-list-card" style="margin-bottom: 4px;">'
            f'  <div style="min-width:0; flex:1;">'
            f'    <div style="display:flex; align-items:center; gap:6px; margin-bottom:2px;">'
            f'      <span class="m-list-title" style="font-size:15px; font-weight:600;">{html.escape(uname)}</span>'
            f'      {role_chip}'
            f'      {status_chip}'
            f'    </div>'
            f'    <div class="m-list-sub" style="font-size:11px; color:var(--m-muted-fg);">{meta_text}</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander(f"Edit {uname}", icon=":material/edit:"):
            with st.form(f"m_form_edit_u_{uid_raw}"):
                st.caption("Account Details")
                e_name = st.text_input("Username", value=uname, key=f"eun_{uid_raw}")
                e_email = st.text_input("Email", value=uemail, key=f"eue_{uid_raw}")
                e_phone = st.text_input("Phone", value=uphone, key=f"euph_{uid_raw}")
                e_role = st.selectbox("Role", ["user", "admin"], index=1 if urole == "admin" else 0, key=f"eur_{uid_raw}")
                if st.form_submit_button("Save Details", type="primary", use_container_width=True):
                    res_p = auth_service.update_profile(uid_raw, e_name.strip(), e_email.strip(), e_phone.strip())
                    if res_p is True:
                        auth_service.update_role(uid_raw, e_role)
                        st.session_state["m_toast"] = f"User '{e_name.strip()}' updated!"
                        st.rerun()
                    else:
                        st.error(str(res_p))

            with st.form(f"m_form_pwd_{uid_raw}"):
                st.caption("Change Password")
                e_pwd = st.text_input("New Password", type="password", placeholder="Enter new password (min 6 chars)", key=f"eup_{uid_raw}")
                if st.form_submit_button("Reset Password", use_container_width=True):
                    if not e_pwd or len(e_pwd) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        auth_service.update_password(uid_raw, e_pwd)
                        st.session_state["m_toast"] = f"Password updated for {uname}!"
                        st.rerun()

            if ustatus == "active":
                if uid_raw != "admin" and uname.lower() != "root":
                    if st.button(f"Archive {uname}", key=f"btn_arch_{uid_raw}", use_container_width=True):
                        auth_service.delete_user(uid_raw)
                        st.session_state["m_toast"] = f"User '{uname}' archived."
                        st.rerun()
                else:
                    st.caption("🛡️ Primary admin account cannot be archived.")
            else:
                if st.button(f"Restore {uname}", key=f"btn_unarch_{uid_raw}", type="primary", use_container_width=True):
                    auth_service.unarchive_user(uid_raw)
                    st.session_state["m_toast"] = f"User '{uname}' restored."
                    st.rerun()
