import html
from datetime import datetime
import streamlit as st

from components.mobile_ui import fmt, m_section
from components.upi_bridge import (
    UPI_APPS,
    parse_upi_qr,
    render_qr_scanner_widget,
    render_pay_handoff_banner,
)


def render_quick_add_view(uid: str, finance_service, trip_service):
    """Artboard 3: Instant <4s Mobile Quick Add (+ FAB destination) + QR Quick Pay."""
    @st.fragment
    def _quick_add_frag():
        if "m_qa_v" not in st.session_state:
            st.session_state["m_qa_v"] = 0
        if "m_qa_mode" not in st.session_state:
            st.session_state["m_qa_mode"] = "Expense"

        toast_msg = st.session_state.pop("m_qa_toast", None)
        if toast_msg:
            st.toast(toast_msg, icon=":material/check_circle:")
            st.success(toast_msg)

        handoff = st.session_state.pop("m_qa_pay_handoff", None)
        if handoff:
            render_pay_handoff_banner(
                app_name=handoff["app"],
                amount=handoff["amount"],
                parsed_qr=handoff.get("parsed_qr"),
                note=handoff.get("note", ""),
                paid_by_cc=handoff.get("paid_by_cc", False),
            )

        # Deterministic 3-pill mode switcher (immune to Streamlit version DOM diffs)
        active_mode = st.session_state["m_qa_mode"]
        if active_mode not in ("Expense", "Income", "Trip Expense"):
            active_mode = "Expense"
            st.session_state["m_qa_mode"] = active_mode

        sc1, sc2, sc3 = st.columns([1.0, 0.9, 1.25])
        for col, opt, btn_key in (
            (sc1, "Expense", "m_qa_tab_exp"),
            (sc2, "Income", "m_qa_tab_inc"),
            (sc3, "Trip Expense", "m_qa_tab_trip"),
        ):
            with col:
                if st.button(
                    opt,
                    key=btn_key,
                    type="primary" if active_mode == opt else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["m_qa_mode"] = opt
                    st.rerun(scope="fragment")

        v = st.session_state["m_qa_v"]

        if active_mode == "Expense":
            all_cats = finance_service.get_categories(uid)
            filtered = all_cats[all_cats["type"] == "Expense"] if not all_cats.empty else all_cats
            cat_opts = {f"{r['icon']} {r['name']}": r["id"] for _, r in filtered.iterrows()} if not filtered.empty else {}

            preferred_app = finance_service.get_setting("preferred_upi_app", "None", uid)
            if preferred_app not in UPI_APPS:
                preferred_app = "None"
            default_cc = finance_service.get_setting("preferred_upi_default_cc", "False", uid) == "True"

            raw_qr = st.session_state.get(f"m_qa_upi_{v}", "")
            parsed_qr = parse_upi_qr(raw_qr)

            # Auto-fill amount from dynamic merchant QR if amount field is currently empty
            if parsed_qr and parsed_qr.get("am") and st.session_state.get(f"m_qa_amt_{v}") is None:
                try:
                    st.session_state[f"m_qa_amt_{v}"] = float(parsed_qr["am"])
                except (TypeError, ValueError):
                    pass

            with st.container(key="m_qa_exp_card"):
                amt = st.number_input(
                    f"Amount ({st.session_state.get('sym', '₹')})",
                    min_value=0.01,
                    step=1.0,
                    value=None,
                    placeholder="0.00",
                    key=f"m_qa_amt_{v}",
                )
                cat_sel = st.selectbox(
                    "Category",
                    list(cat_opts.keys()) if cat_opts else ["-"],
                    index=0,
                    key=f"m_qa_cat_{v}",
                )
                dt = st.date_input("Date", value=datetime.now().date(), key=f"m_qa_dt_{v}")
                desc = st.text_input("Description", value="", placeholder="What was this for?", key=f"m_qa_desc_{v}")

                # QR Scanner + Merchant UPI ID (syncs directly into m_qa_upi_{v} via JS)
                render_qr_scanner_widget(f"m_qa_upi_{v}", button_label="Scan Merchant QR")
                upi_input = st.text_input(
                    "Merchant UPI ID / QR",
                    value="",
                    placeholder="Scan QR above or enter name@upi",
                    label_visibility="collapsed",
                    key=f"m_qa_upi_{v}",
                )
                parsed_qr = parse_upi_qr(upi_input)
                if parsed_qr:
                    pn_esc = html.escape(parsed_qr["pn"] or "Merchant")
                    pa_esc = html.escape(parsed_qr["pa"])
                    st.markdown(
                        f'<div class="m-qr-chip">'
                        f'<span class="m-qr-chip-name">✓ {pn_esc}</span>'
                        f'<span class="m-qr-chip-vpa">{pa_esc}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                elif upi_input.strip():
                    st.caption("Could not detect a valid UPI ID (expected upi://pay?pa=... or name@bank).")

                # Paid by CC checkbox directly below the scanner
                paid_by_cc = st.checkbox("Paid by CC", value=default_cc, key=f"m_qa_cc_{v}")

                def _commit_expense(launch_upi: bool, target_app: str | None = None):
                    if amt is None or amt <= 0:
                        st.error("Please enter an amount greater than 0.")
                        return
                    if cat_sel == "-":
                        st.error("Please select a category.")
                        return
                    full_dt = datetime.combine(dt, datetime.now().time())
                    desc_final = desc.strip()
                    if not desc_final and parsed_qr:
                        desc_final = parsed_qr.get("pn") or parsed_qr.get("pa") or ""
                    finance_service.add_transaction(
                        amt,
                        cat_opts[cat_sel],
                        desc_final,
                        full_dt,
                        "Expense",
                        uid,
                        paid_by_cc=paid_by_cc,
                    )
                    st.session_state["m_qa_v"] = v + 1
                    cc_note = " · CC" if paid_by_cc else ""
                    if launch_upi:
                        app_to_use = target_app or preferred_app
                        st.session_state["m_qa_pay_handoff"] = {
                            "app": app_to_use,
                            "amount": float(amt),
                            "parsed_qr": parsed_qr,
                            "note": desc_final,
                            "paid_by_cc": paid_by_cc,
                        }
                        st.session_state["m_qa_toast"] = f"Logged {fmt(amt)} ({cat_sel}{cc_note}) · Opening {app_to_use}"
                    else:
                        st.session_state["m_qa_toast"] = f"Expense logged: {fmt(amt)} ({cat_sel}{cc_note})"
                    st.rerun(scope="fragment")

                if preferred_app != "None":
                    pay_lbl = f"Pay via {UPI_APPS[preferred_app]['label']}"
                    bc1, bc2 = st.columns([1.2, 0.8])
                    with bc1:
                        if st.button(pay_lbl, type="primary", use_container_width=True, key=f"m_qa_pay_{v}"):
                            _commit_expense(launch_upi=True, target_app=preferred_app)
                    with bc2:
                        if st.button("Record Only", type="secondary", use_container_width=True, key=f"m_qa_save_{v}"):
                            _commit_expense(launch_upi=False)
                elif parsed_qr:
                    bc1, bc2 = st.columns([1.2, 0.8])
                    with bc1:
                        if st.button("Pay via UPI", type="primary", use_container_width=True, key=f"m_qa_pay_{v}"):
                            _commit_expense(launch_upi=True, target_app="System UPI")
                    with bc2:
                        if st.button("Record Only", type="secondary", use_container_width=True, key=f"m_qa_save_{v}"):
                            _commit_expense(launch_upi=False)
                else:
                    if st.button("Record Expense", type="primary", use_container_width=True, key=f"m_qa_save_{v}"):
                        _commit_expense(launch_upi=False)
                    st.caption("Tip: Choose CRED, Paytm, GPay, or PhonePe in More → Settings → Quick Pay & UPI.")

        elif active_mode == "Income":
            all_cats = finance_service.get_categories(uid)
            filtered = all_cats[all_cats["type"] == "Income"] if not all_cats.empty else all_cats
            cat_opts = {f"{r['icon']} {r['name']}": r["id"] for _, r in filtered.iterrows()} if not filtered.empty else {}

            with st.form(f"m_qa_txn_form_Income_{v}"):
                amt = st.number_input(
                    f"Amount ({st.session_state.get('sym', '₹')})",
                    min_value=0.01,
                    step=1.0,
                    value=None,
                    placeholder="0.00",
                    key=f"m_qa_amt_{v}",
                )
                cat_sel = st.selectbox(
                    "Category",
                    list(cat_opts.keys()) if cat_opts else ["-"],
                    index=0,
                    key=f"m_qa_cat_{v}",
                )
                dt = st.date_input("Date", value=datetime.now().date(), key=f"m_qa_dt_{v}")
                desc = st.text_input("Description", value="", placeholder="What was this for?", key=f"m_qa_desc_{v}")

                if st.form_submit_button("Record Income", type="primary", use_container_width=True):
                    if amt is None or amt <= 0:
                        st.error("Please enter an amount greater than 0.")
                    elif cat_sel == "-":
                        st.error("Please select a category.")
                    else:
                        full_dt = datetime.combine(dt, datetime.now().time())
                        finance_service.add_transaction(
                            amt,
                            cat_opts[cat_sel],
                            desc.strip(),
                            full_dt,
                            "Income",
                            uid,
                            paid_by_cc=False,
                        )
                        st.session_state["m_qa_v"] = v + 1
                        st.session_state["m_qa_toast"] = f"Income logged: {fmt(amt)} ({cat_sel})"
                        st.rerun(scope="fragment")
        else:
            trips_df = trip_service.get_trips(uid)
            active_trips = trips_df[trips_df["status"] == "active"] if not trips_df.empty else trips_df
            if active_trips.empty:
                st.info("No active trips yet. Open Trips to create your first trip.")
                if st.button("Open TripFlow", type="primary", use_container_width=True, key="m_qa_goto_trips"):
                    st.session_state["m_page"] = "Trips"
                    st.rerun()
                return

            trip_map = {r["name"]: r["id"] for _, r in active_trips.iterrows()}
            sel_trip_name = st.selectbox("Trip", list(trip_map.keys()), key="m_qa_trip_sel")
            tid = trip_map[sel_trip_name]
            bundle = trip_service.get_trip_bundle(tid)
            members = bundle["summary"]["members"] if bundle else []
            if not members:
                st.info("Add friends to this trip first in Trips → Friends.")
                return

            m_names = [m["name"] for m in members]
            with st.form(f"m_qa_trip_exp_{tid}_{v}"):
                t_amt = st.number_input(
                    f"Amount ({st.session_state.get('sym', '₹')})",
                    min_value=0.01,
                    step=1.0,
                    value=None,
                    placeholder="0.00",
                    key=f"m_qa_tamt_{v}",
                )
                t_desc = st.text_input("Description *", value="", placeholder="e.g. Lunch, Cab, Tickets", key=f"m_qa_tdesc_{v}")
                payer_opts = ["💼 Pool Fund"] + m_names
                payer = st.selectbox("Paid By", payer_opts, index=0, key=f"m_qa_tpayer_{v}")
                inc_friends = st.multiselect("Split Among", m_names, default=m_names, key=f"m_qa_tinc_{v}")
                t_dt = st.date_input("Date", value=datetime.now().date(), key=f"m_qa_tdt_{v}")

                if st.form_submit_button("Record Trip Expense", type="primary", use_container_width=True):
                    if not t_desc.strip():
                        st.error("Please enter a description.")
                    elif t_amt is None or t_amt <= 0:
                        st.error("Please enter an amount greater than 0.")
                    elif not inc_friends:
                        st.error("Select at least one friend.")
                    else:
                        from_pool = payer == "💼 Pool Fund"
                        payer_id = None if from_pool else next(m["id"] for m in members if m["name"] == payer)
                        weights = {m["id"]: m["weight"] for m in members if m["name"] in inc_friends}
                        s_type = "custom" if len(inc_friends) < len(members) else "equal"
                        trip_service.add_expense(tid, payer_id, from_pool, t_amt, t_desc.strip(), t_dt, split_type=s_type, member_weights=weights)
                        st.session_state["m_qa_v"] = v + 1
                        st.session_state["m_qa_toast"] = f"Trip expense recorded: {t_desc.strip()} ({fmt(t_amt)})"
                        st.rerun(scope="fragment")

    _quick_add_frag()
