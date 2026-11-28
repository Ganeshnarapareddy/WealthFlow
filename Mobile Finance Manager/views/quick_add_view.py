from datetime import datetime
import streamlit as st

from components.mobile_ui import fmt


def render_quick_add_view(uid: str, finance_service, trip_service):
    """Artboard 3: Instant <4s Mobile Quick Add (+ FAB destination) with empty 0.00 placeholder."""
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

        if active_mode in ("Expense", "Income"):
            all_cats = finance_service.get_categories(uid)
            filtered = all_cats[all_cats["type"] == active_mode] if not all_cats.empty else all_cats
            cat_opts = {f"{r['icon']} {r['name']}": r["id"] for _, r in filtered.iterrows()} if not filtered.empty else {}

            with st.form(f"m_qa_txn_form_{active_mode}_{v}"):
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
                paid_by_cc = (
                    st.checkbox("Paid by CC", value=False, key=f"m_qa_cc_{v}")
                    if active_mode == "Expense"
                    else False
                )

                if st.form_submit_button(f"Record {active_mode}", type="primary", use_container_width=True):
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
                            active_mode,
                            uid,
                            paid_by_cc=paid_by_cc,
                        )
                        st.session_state["m_qa_v"] = v + 1
                        cc_note = " · CC" if paid_by_cc else ""
                        st.session_state["m_qa_toast"] = f"{active_mode} logged: {fmt(amt)} ({cat_sel}{cc_note})"
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
