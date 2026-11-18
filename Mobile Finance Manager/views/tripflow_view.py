import html
import json
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from components.mobile_ui import fmt, m_section, m_empty, m_kpi_strip, m_delete_popover


def render_tripflow_view(uid: str, user_data: dict, trip_service, db):
    """Artboard 5: Mobile TripFlow — Fragment-isolated expense/advance/friend logging with zero blanking."""
    trips_df = trip_service.get_trips(uid)

    # Top Trip Selector + Create New Trip Popover
    c_sel, c_new = st.columns([0.74, 0.26], vertical_alignment="center")
    with c_sel:
        if trips_df.empty:
            st.info("Create your first trip to split expenses.")
            active_tid = None
        else:
            trip_opts = {
                f"{'🟢' if r['status'] == 'active' else '🔒'} {r['name']}": r["id"]
                for _, r in trips_df.iterrows()
            }
            labels = list(trip_opts.keys())
            cur_id = st.session_state.get("m_active_trip_id")
            idx = 0
            if cur_id in trip_opts.values():
                idx = list(trip_opts.values()).index(cur_id)
            picked = st.selectbox("Trip", labels, index=idx, label_visibility="collapsed", key="m_trip_picker")
            active_tid = trip_opts[picked]
            st.session_state["m_active_trip_id"] = active_tid

    with c_new:
        with st.popover("+ New", use_container_width=True):
            st.markdown("**Create New Trip**")
            with st.form("m_new_trip_form", clear_on_submit=True):
                tn = st.text_input("Trip Name *", placeholder="e.g. Goa 2026")
                td = st.text_input("Destination / Note", placeholder="Optional")
                tb = st.number_input("Target Budget", min_value=0.0, value=None, placeholder="0.00", step=500.0)
                ts = st.date_input("Start Date", value=datetime.now().date())
                te = st.date_input("End Date", value=datetime.now().date())
                if st.form_submit_button("Create Trip", type="primary", use_container_width=True):
                    if not tn or not tn.strip():
                        st.error("Trip name is required.")
                    else:
                        creator = user_data.get("username", "Me")
                        new_id = trip_service.create_trip_with_creator(
                            uid, tn.strip(), creator, td.strip(), float(tb or 0.0), ts, te
                        )
                        st.session_state["m_active_trip_id"] = new_id
                        st.session_state["m_toast"] = f"Trip '{tn.strip()}' created!"
                        st.rerun()

    if not active_tid:
        m_empty("No trips yet", "Tap '+ New' above to start splitting group trip expenses.")
        return

    @st.fragment
    def _trip_workspace(trip_id: str):
        bundle = trip_service.get_trip_bundle(trip_id)
        if not bundle or not bundle.get("summary") or not bundle["summary"].get("trip"):
            return

        t_msg = st.session_state.pop("m_trip_toast", None)
        if t_msg:
            st.toast(t_msg, icon=":material/check_circle:")

        summary = bundle["summary"]
        trip = summary["trip"]
        is_active = trip["status"] == "active"

        # Trip KPI Hero
        m_kpi_strip(
            hero_label=trip["name"],
            hero_value=fmt(summary["total_spent"]),
            hero_badge="Active" if is_active else "Settled",
            items=[
                {"label": "Target budget", "value": fmt(summary["target_budget"]) if summary["target_budget"] > 0 else "No limit"},
                {"label": "Pool cash", "value": fmt(summary["pool_cash_in_hand"]), "delta": f"{fmt(summary['total_advances'])} pooled", "tone": "accent"},
            ],
        )

        # Quick Actions Strip (Refresh / Settle / Delete Trip)
        a1, a2, a3 = st.columns([0.4, 0.4, 0.2], vertical_alignment="center")
        with a1:
            if st.button("Sync", icon=":material/sync:", key=f"m_tsync_{trip_id}", use_container_width=True):
                trip_service.rebalance_all_splits(trip_id)
                db.bump_version()
                st.session_state["m_trip_toast"] = "Splits synced!"
                st.rerun(scope="fragment")
        with a2:
            if st.button("Settle" if is_active else "Reopen", icon=":material/lock:" if is_active else ":material/lock_open:", key=f"m_tstat_{trip_id}", use_container_width=True):
                new_st = "settled" if is_active else "active"
                trip_service.update_trip_status(trip_id, new_st)
                st.session_state["m_toast"] = f"Trip marked {new_st}."
                st.rerun()
        with a3:
            m_delete_popover(trip_id, f"mtrip_{trip_id}", trip_service.delete_trip, trip["name"], pass_user_id=uid, toast_msg="Trip deleted.")

        # 4-tab native touch switcher — guaranteed active highlight, zero blanking
        t_sum, t_add, t_led, t_fri = st.tabs(["Summary", "Add", "Ledger", "Friends"])

        # 1. SUMMARY & SETTLE-UP
        with t_sum:
            if not summary["members"]:
                m_empty("No friends yet", "Switch to Friends tab to add trip members.")
            else:
                m_section("Member balances")
                for m in summary["members"]:
                    st_code = m.get("current_status", "settled")
                    rem = m.get("remaining_balance", 0.0)
                    if st_code == "settled":
                        badge = '<span class="m-chip positive">Settled</span>'
                    elif st_code == "refund":
                        badge = f'<span class="m-chip positive m-mono">+{html.escape(fmt(rem))}</span>'
                    else:
                        badge = f'<span class="m-chip negative m-mono">-{html.escape(fmt(-rem))}</span>'

                    w_txt = f" · {m['weight']}x" if m["weight"] != 1.0 else ""
                    st.markdown(
                        f'<div class="m-list-card">'
                        f'<div style="min-width:0;">'
                        f'<div class="m-list-title">{html.escape(m["name"])}{w_txt}</div>'
                        f'<div class="m-list-sub">Paid {html.escape(fmt(m["total_paid"]))} · Share {html.escape(fmt(m["final_share"]))}</div>'
                        f'</div>{badge}</div>',
                        unsafe_allow_html=True,
                    )

                m_section("Settle-up plan")
                if not summary["settlements"] or summary.get("is_all_settled"):
                    st.success("All accounts are fully settled!")
                else:
                    for idx, s in enumerate(summary["settlements"]):
                        is_pool = s["transfer_type"] == "pool_cash"
                        txt = f"Pool cash → {s['to_name']}" if is_pool else f"{s['from_name']} → {s['to_name']}"
                        c1, c2 = st.columns([0.72, 0.28], vertical_alignment="center")
                        with c1:
                            st.markdown(
                                f'<div class="m-list-card">'
                                f'<div style="min-width:0;"><div class="m-list-title">{html.escape(txt)}</div>'
                                f'<div class="m-list-sub">{"Cash in hand" if is_pool else "Direct transfer"}</div></div>'
                                f'<div class="m-list-amt">{html.escape(fmt(s["amount"]))}</div></div>',
                                unsafe_allow_html=True,
                            )
                        with c2:
                            if s["is_paid"]:
                                st.markdown('<span class="m-chip positive">✓ Paid</span>', unsafe_allow_html=True)
                            else:
                                if st.button("Paid", icon=":material/check:", key=f"m_alert_stl_{trip_id}_{idx}"):
                                    trip_service.record_settlement(trip_id, s["from_name"], s["to_name"], s["remaining_amount"])
                                    st.session_state["m_trip_toast"] = "Settlement recorded!"
                                    st.rerun(scope="fragment")

                # One-tap WhatsApp clipboard export
                wa_text = trip_service.generate_whatsapp_summary(trip_id, st.session_state.get("sym", "₹"), bundle=bundle)
                wa_json = json.dumps(wa_text)
                components.html(
                    f"""
                    <button id="mCopyWa" onclick="copyWa()" style="
                        width:100%; height:44px; border-radius:12px; border:0;
                        background:#059669; color:#FFF; font-family:-apple-system,sans-serif;
                        font-size:14px; font-weight:600; cursor:pointer;">
                        📋 Copy WhatsApp Summary
                    </button>
                    <script>
                    function copyWa() {{
                        navigator.clipboard.writeText({wa_json}).then(function() {{
                            const b = document.getElementById('mCopyWa');
                            b.textContent = '✅ Copied to Clipboard!';
                            setTimeout(function() {{ b.textContent = '📋 Copy WhatsApp Summary'; }}, 2200);
                        }});
                    }}
                    </script>
                    """,
                    height=52,
                )

        # 2. ADD EXPENSE / ADVANCE
        with t_add:
            if not summary["members"]:
                m_empty("Add friends first", "Add at least one friend in the Friends tab before logging expenses.")
            else:
                m_names = [m["name"] for m in summary["members"]]
                t_sub_exp, t_sub_adv = st.tabs(["Expense", "Advance"])

                with t_sub_exp:
                    ev = st.session_state.get("m_te_v", 0)
                    with st.form(f"m_te_form_{trip_id}_{ev}"):
                        e_amt = st.number_input("Amount *", min_value=0.01, step=1.0, value=None, placeholder="0.00", key=f"m_te_amt_{trip_id}_{ev}")
                        e_desc = st.text_input("Description *", value="", placeholder="e.g. Resort, Lunch, Fuel", key=f"m_te_desc_{trip_id}_{ev}")
                        e_payer = st.selectbox("Paid By", ["💼 Pool Fund"] + m_names, index=0, key=f"m_te_pay_{trip_id}_{ev}")
                        e_inc = st.multiselect("Split Among", m_names, default=m_names, key=f"m_te_inc_{trip_id}_{ev}")
                        e_dt = st.date_input("Date", value=datetime.now().date(), key=f"m_te_dt_{trip_id}_{ev}")
                        if st.form_submit_button("Record Expense", type="primary", use_container_width=True):
                            if not e_desc.strip():
                                st.error("Please enter a description.")
                            elif e_amt is None or e_amt <= 0:
                                st.error("Please enter an amount greater than 0.")
                            elif not e_inc:
                                st.error("Select at least one friend.")
                            else:
                                from_pool = e_payer == "💼 Pool Fund"
                                pid = None if from_pool else next(m["id"] for m in summary["members"] if m["name"] == e_payer)
                                weights = {m["id"]: m["weight"] for m in summary["members"] if m["name"] in e_inc}
                                s_type = "custom" if len(e_inc) < len(summary["members"]) else "equal"
                                trip_service.add_expense(trip_id, pid, from_pool, e_amt, e_desc.strip(), e_dt, split_type=s_type, member_weights=weights)
                                st.session_state["m_te_v"] = ev + 1
                                st.session_state["m_trip_toast"] = f"Expense recorded: {e_desc.strip()} ({fmt(e_amt)})"
                                st.rerun(scope="fragment")

                with t_sub_adv:
                    av = st.session_state.get("m_ta_v", 0)
                    with st.form(f"m_ta_form_{trip_id}_{av}"):
                        a_mem = st.selectbox("Friend *", m_names, index=0, key=f"m_ta_mem_{trip_id}_{av}")
                        a_amt = st.number_input("Advance Amount *", min_value=0.01, step=100.0, value=None, placeholder="0.00", key=f"m_ta_amt_{trip_id}_{av}")
                        a_note = st.text_input("Note", value="", placeholder="e.g. Initial pool advance", key=f"m_ta_note_{trip_id}_{av}")
                        a_dt = st.date_input("Date", value=datetime.now().date(), key=f"m_ta_dt_{trip_id}_{av}")
                        if st.form_submit_button("Record Advance", type="primary", use_container_width=True):
                            if a_amt is None or a_amt <= 0:
                                st.error("Please enter an advance amount greater than 0.")
                            else:
                                mid = next(m["id"] for m in summary["members"] if m["name"] == a_mem)
                                trip_service.add_advance(trip_id, mid, a_amt, a_note.strip() or "Pool Advance", a_dt)
                                st.session_state["m_ta_v"] = av + 1
                                st.session_state["m_trip_toast"] = f"Advance recorded: {a_mem} ({fmt(a_amt)})"
                                st.rerun(scope="fragment")

        # 3. TRIP LEDGER
        with t_led:
            df_exp = bundle["expenses_df"]
            df_adv = bundle["advances_df"]

            m_section("Itemized expenses")
            if df_exp.empty:
                m_empty("No expenses yet", "Switch to Add to record your first trip expense.")
            else:
                for _, row in df_exp.iterrows():
                    c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
                    with c1:
                        st.markdown(
                            f'<div class="m-list-card">'
                            f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(row["description"]))}</div>'
                            f'<div class="m-list-sub">Paid by {html.escape(str(row["payer_name"]))} · {html.escape(str(row["date"]))}</div></div>'
                            f'<div class="m-list-amt" style="color:#F87171;">{html.escape(fmt(row["amount"]))}</div></div>',
                            unsafe_allow_html=True,
                        )
                    with c2:
                        m_delete_popover(
                            row["id"], f"mexp_{row['id']}", trip_service.delete_expense,
                            item_name=str(row["description"]), fragment_scope=True, toast_msg="Expense removed.",
                        )

            if not df_adv.empty:
                m_section("Pool advances")
                for _, row in df_adv.iterrows():
                    c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
                    with c1:
                        st.markdown(
                            f'<div class="m-list-card">'
                            f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(row["member_name"]))}</div>'
                            f'<div class="m-list-sub">{html.escape(str(row["description"] or "Pool Advance"))} · {html.escape(str(row["date"]))}</div></div>'
                            f'<div class="m-list-amt" style="color:#34D399;">+{html.escape(fmt(row["amount"]))}</div></div>',
                            unsafe_allow_html=True,
                        )
                    with c2:
                        m_delete_popover(
                            row["id"], f"madv_{row['id']}", trip_service.delete_advance,
                            item_name="this advance", fragment_scope=True, toast_msg="Advance removed.",
                        )

        # 4. FRIENDS & LIMITS
        with t_fri:
            mv = st.session_state.get("m_tm_v", 0)
            with st.form(f"m_tm_form_{trip_id}_{mv}"):
                fn = st.text_input("Add Friend *", value="", placeholder="e.g. Rahul, Bharat", key=f"m_tm_name_{trip_id}_{mv}")
                fc1, fc2 = st.columns(2)
                with fc1:
                    fw = st.number_input("Weight", min_value=0.1, value=1.0, step=0.5, key=f"m_tm_w_{trip_id}_{mv}")
                with fc2:
                    fcap = st.number_input("Max Cap (0=None)", min_value=0.0, value=None, placeholder="0.00", step=500.0, key=f"m_tm_c_{trip_id}_{mv}")
                if st.form_submit_button("Add Friend", type="primary", use_container_width=True):
                    if not fn.strip():
                        st.error("Please enter a name.")
                    else:
                        trip_service.add_member(trip_id, fn.strip(), weight=fw, max_budget=fcap if (fcap and fcap > 0) else None)
                        st.session_state["m_tm_v"] = mv + 1
                        st.session_state["m_trip_toast"] = f"Added {fn.strip()}!"
                        st.rerun(scope="fragment")

            members_df = bundle["members_df"]
            if not members_df.empty:
                m_section("Trip members")
                for _, row in members_df.iterrows():
                    cap_txt = fmt(row["max_budget"]) if pd.notnull(row["max_budget"]) and row["max_budget"] else "No cap"
                    c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
                    with c1:
                        st.markdown(
                            f'<div class="m-list-card">'
                            f'<div style="min-width:0;"><div class="m-list-title">{html.escape(str(row["name"]))}</div>'
                            f'<div class="m-list-sub">Weight {row["weight"]}x · Cap: {html.escape(cap_txt)}</div></div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with c2:
                        m_delete_popover(
                            row["id"], f"mmem_{row['id']}",
                            lambda mid: trip_service.delete_member_with_reassignment(mid, reassign_to_pool=True),
                            item_name=str(row["name"]), fragment_scope=True, toast_msg=f"Removed {row['name']}.",
                        )

    _trip_workspace(active_tid)
