import html
from datetime import datetime
import streamlit as st

from components.mobile_ui import fmt, m_section
from components.upi_bridge import (
    UPI_APPS,
    PAY_ACTIVE_APP_OPTIONS,
    parse_upi_qr,
    render_qr_scanner_widget,
    render_pay_handoff_banner,
)


def render_scan_pay_view(uid: str, finance_service):
    """
    Dedicated floating-FAB Scan & Pay workflow:
    Step 1: Press / Scan Merchant UPI QR (or enter UPI ID)
    Step 2: Enter Amount, Category, Description, Paid by CC, and UPI App -> Proceed
    Step 3: Logs expense in WealthFlow immediately & hands off to CRED / Paytm / GPay / PhonePe / BHIM
    """
    @st.fragment
    def _scan_pay_frag():
        if "m_sp_v" not in st.session_state:
            st.session_state["m_sp_v"] = 0

        v = st.session_state["m_sp_v"]
        auto_open = bool(st.session_state.pop("m_scan_auto_open", False))

        handoff = st.session_state.pop("m_sp_handoff", None)
        if handoff:
            st.success(f"Expense logged: {fmt(handoff['amount'])}")
            render_pay_handoff_banner(
                app_name=handoff["app"],
                amount=handoff["amount"],
                parsed_qr=handoff.get("parsed_qr"),
                note=handoff.get("note", ""),
                paid_by_cc=handoff.get("paid_by_cc", False),
            )
            ac1, ac2 = st.columns(2)
            with ac1:
                if st.button("Scan Another QR", type="primary", use_container_width=True, key="m_sp_again"):
                    st.session_state["m_scan_auto_open"] = True
                    st.rerun(scope="fragment")
            with ac2:
                if st.button("Back to Home", type="secondary", use_container_width=True, key="m_sp_home"):
                    st.session_state["m_page"] = st.session_state.get("m_scan_return_page", "Home")
                    st.rerun()
            return

        # Read any already-scanned QR value BEFORE instantiating widgets
        raw_qr = st.session_state.get(f"m_sp_upi_{v}", "")
        parsed_qr = parse_upi_qr(raw_qr)

        # Step 1: Ask for QR first
        if not parsed_qr:
            m_section("Scan & Pay", "Step 1 · Scan merchant UPI QR to begin")
            with st.container(key="m_sp_card"):
                render_qr_scanner_widget(
                    f"m_sp_upi_{v}",
                    button_label="Press to Scan QR",
                    auto_open=auto_open,
                )
                upi_manual = st.text_input(
                    "Or enter UPI ID manually",
                    value="",
                    placeholder="e.g. merchant@okaxis or paste upi://pay?...",
                    key=f"m_sp_upi_{v}",
                )
                if upi_manual.strip() and not parse_upi_qr(upi_manual):
                    st.warning("Could not read a valid UPI ID from that input. Expected a UPI QR or name@bank.")
            return

        # Step 2: QR Captured -> Ask for Amount, Category, Description, Paid by CC, UPI App -> Proceed
        pn_txt = parsed_qr.get("pn") or "Merchant"
        pa_txt = parsed_qr["pa"]

        # Pre-fill Amount & Description from QR once if empty
        if parsed_qr.get("am") and st.session_state.get(f"m_sp_amt_{v}") is None:
            try:
                st.session_state[f"m_sp_amt_{v}"] = float(parsed_qr["am"])
            except (TypeError, ValueError):
                pass
        if not st.session_state.get(f"m_sp_desc_{v}") and parsed_qr.get("pn"):
            st.session_state[f"m_sp_desc_{v}"] = parsed_qr["pn"]

        m_section("Payment Details", "Step 2 · Enter amount & details, then tap Proceed")

        c_chip, c_chg = st.columns([0.74, 0.26], vertical_alignment="center")
        with c_chip:
            st.markdown(
                f'<div class="m-qr-chip">'
                f'  <div style="min-width:0;">'
                f'    <div class="m-qr-chip-name">✓ {html.escape(pn_txt)}</div>'
                f'    <div class="m-qr-chip-vpa">{html.escape(pa_txt)}</div>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c_chg:
            if st.button("Change QR", key=f"m_sp_reset_qr_{v}", use_container_width=True):
                st.session_state["m_sp_v"] = v + 1
                st.session_state["m_scan_auto_open"] = True
                st.rerun(scope="fragment")

        all_cats = finance_service.get_categories(uid)
        filtered = all_cats[all_cats["type"] == "Expense"] if not all_cats.empty else all_cats
        cat_opts = {f"{r['icon']} {r['name']}": r["id"] for _, r in filtered.iterrows()} if not filtered.empty else {}

        saved_app = finance_service.get_setting("preferred_upi_app", "CRED", uid)
        if saved_app not in PAY_ACTIVE_APP_OPTIONS:
            saved_app = "CRED"
        default_cc = finance_service.get_setting("preferred_upi_default_cc", "False", uid) == "True"

        with st.form(f"m_sp_details_form_{v}"):
            amt = st.number_input(
                f"Amount ({st.session_state.get('sym', '₹')}) *",
                min_value=0.01,
                step=1.0,
                value=None,
                placeholder="0.00",
                key=f"m_sp_amt_{v}",
            )
            cat_sel = st.selectbox(
                "Category *",
                list(cat_opts.keys()) if cat_opts else ["-"],
                index=0,
                key=f"m_sp_cat_{v}",
            )
            desc = st.text_input(
                "Description",
                placeholder="What was this for?",
                key=f"m_sp_desc_{v}",
            )
            paid_by_cc = st.checkbox("Paid by CC", value=default_cc, key=f"m_sp_cc_{v}")
            pay_app = st.selectbox(
                "Open in UPI App",
                PAY_ACTIVE_APP_OPTIONS,
                index=PAY_ACTIVE_APP_OPTIONS.index(saved_app),
                format_func=lambda k: UPI_APPS[k]["label"],
                key=f"m_sp_app_{v}",
            )

            if st.form_submit_button("Proceed", type="primary", use_container_width=True):
                if amt is None or amt <= 0:
                    st.error("Please enter an amount greater than 0.")
                elif cat_sel == "-":
                    st.error("Please select a category.")
                else:
                    desc_final = desc.strip() or pn_txt or pa_txt
                    finance_service.add_transaction(
                        float(amt),
                        cat_opts[cat_sel],
                        desc_final,
                        datetime.now(),
                        "Expense",
                        uid,
                        paid_by_cc=paid_by_cc,
                    )
                    st.session_state["m_sp_v"] = v + 1
                    st.session_state["m_sp_handoff"] = {
                        "app": pay_app,
                        "amount": float(amt),
                        "parsed_qr": parsed_qr,
                        "note": desc_final,
                        "paid_by_cc": paid_by_cc,
                    }
                    st.rerun(scope="fragment")

    _scan_pay_frag()
