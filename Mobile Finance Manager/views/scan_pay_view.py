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


def restore_scan_pay_to_step2(uid: str, finance_service):
    """Revert the unconfirmed Step 3 handoff back to Step 2 without leaving a duplicate ledger row."""
    handoff = st.session_state.pop("m_sp_handoff", None)
    if not handoff:
        return False
    txn_id = handoff.get("txn_id")
    if txn_id:
        try:
            finance_service.delete_transaction(txn_id, uid)
        except Exception:
            pass
    st.session_state["m_sp_parsed_qr"] = handoff.get("parsed_qr")
    st.session_state["m_sp_draft"] = {
        "amount": handoff.get("amount"),
        "cat_label": handoff.get("cat_label"),
        "raw_desc": handoff.get("raw_desc", ""),
        "paid_by_cc": handoff.get("paid_by_cc", False),
        "app": handoff.get("app", "CRED"),
    }
    st.session_state["m_sp_v"] = st.session_state.get("m_sp_v", 0) + 1
    return True


def render_scan_pay_view(uid: str, finance_service):
    """
    Dedicated floating-FAB Scan & Pay workflow:
    Step 1: Press / Scan Merchant UPI QR (or enter UPI ID)
    Step 2: Enter Amount, Category, Description, Paid by CC, and UPI App -> Proceed
    Step 3: Expense is already logged in Ledger & hands off to Paytm / PhonePe / GPay / CRED / BHIM;
            Back button returns to Step 2 with all entered details intact (and reverts the temporary row).
    """
    @st.fragment
    def _scan_pay_frag():
        if "m_sp_v" not in st.session_state:
            st.session_state["m_sp_v"] = 0

        v = st.session_state["m_sp_v"]
        auto_open = bool(st.session_state.pop("m_scan_auto_open", False))

        # Step 3: Post-Proceed Payment Handoff (expense is ALREADY logged in Ledger!)
        handoff = st.session_state.get("m_sp_handoff")
        if handoff:
            st.success(f"Logged to Ledger: {fmt(handoff['amount'])} · Ready to open {UPI_APPS.get(handoff['app'], {}).get('label', handoff['app'])}")
            render_pay_handoff_banner(
                app_name=handoff["app"],
                amount=handoff["amount"],
                parsed_qr=handoff.get("parsed_qr"),
                note=handoff.get("note", ""),
                paid_by_cc=handoff.get("paid_by_cc", False),
            )

            ac1, ac2 = st.columns(2)
            with ac1:
                if st.button("← Back", type="secondary", use_container_width=True, key="m_sp_back_edit"):
                    restore_scan_pay_to_step2(uid, finance_service)
                    st.rerun()
            with ac2:
                if st.button("Scan Another", type="primary", use_container_width=True, key="m_sp_again"):
                    st.session_state.pop("m_sp_handoff", None)
                    st.session_state.pop("m_sp_parsed_qr", None)
                    st.session_state.pop("m_sp_draft", None)
                    st.session_state["m_scan_auto_open"] = True
                    st.rerun(scope="fragment")
            return

        # Step 1: Capture QR and persist into non-widget session_state['m_sp_parsed_qr']
        parsed_qr = st.session_state.get("m_sp_parsed_qr")
        if not parsed_qr:
            raw_qr = st.session_state.get(f"m_sp_upi_{v}", "")
            candidate_qr = parse_upi_qr(raw_qr)
            if candidate_qr:
                st.session_state["m_sp_parsed_qr"] = candidate_qr
                parsed_qr = candidate_qr

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
                if upi_manual.strip():
                    cand2 = parse_upi_qr(upi_manual)
                    if cand2:
                        st.session_state["m_sp_parsed_qr"] = cand2
                        st.rerun(scope="fragment")
                    else:
                        st.warning("Could not read a valid UPI ID from that input. Expected a UPI QR or name@bank.")
            return

        # Step 2: QR Captured -> Ask for Amount, Category, Description, Paid by CC, UPI App -> Proceed
        pn_txt = parsed_qr.get("pn") or "Merchant"
        pa_txt = parsed_qr["pa"]

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
                st.session_state.pop("m_sp_parsed_qr", None)
                st.session_state.pop("m_sp_draft", None)
                st.session_state["m_sp_v"] = v + 1
                st.session_state["m_scan_auto_open"] = True
                st.rerun(scope="fragment")

        all_cats = finance_service.get_categories(uid)
        filtered = all_cats[all_cats["type"] == "Expense"] if not all_cats.empty else all_cats
        cat_opts = {f"{r['icon']} {r['name']}": r["id"] for _, r in filtered.iterrows()} if not filtered.empty else {}
        cat_keys = list(cat_opts.keys()) if cat_opts else ["-"]

        saved_app = finance_service.get_setting("preferred_upi_app", "Paytm", uid)
        if saved_app not in PAY_ACTIVE_APP_OPTIONS:
            saved_app = "Paytm"
        default_cc = finance_service.get_setting("preferred_upi_default_cc", "False", uid) == "True"

        draft = st.session_state.get("m_sp_draft") or {}
        amt_default = draft.get("amount")
        if amt_default is None and parsed_qr.get("am"):
            try:
                amt_default = float(parsed_qr["am"])
            except (TypeError, ValueError):
                amt_default = None
        cat_idx = cat_keys.index(draft["cat_label"]) if draft.get("cat_label") in cat_keys else 0
        desc_default = draft.get("raw_desc", "")
        cc_default = bool(draft.get("paid_by_cc", default_cc))
        app_default = draft.get("app") if draft.get("app") in PAY_ACTIVE_APP_OPTIONS else saved_app

        with st.form(f"m_sp_details_form_{v}"):
            amt = st.number_input(
                f"Amount ({st.session_state.get('sym', '₹')}) *",
                min_value=0.01,
                step=1.0,
                value=float(amt_default) if amt_default else None,
                placeholder="0.00",
                key=f"m_sp_amt_{v}",
            )
            cat_sel = st.selectbox(
                "Category *",
                cat_keys,
                index=cat_idx,
                key=f"m_sp_cat_{v}",
            )
            desc = st.text_input(
                "Description",
                value=desc_default,
                placeholder=f"Optional (default: {pn_txt})",
                key=f"m_sp_desc_{v}",
            )
            paid_by_cc = st.checkbox("Paid by CC", value=cc_default, key=f"m_sp_cc_{v}")
            pay_app = st.selectbox(
                "Open in UPI App",
                PAY_ACTIVE_APP_OPTIONS,
                index=PAY_ACTIVE_APP_OPTIONS.index(app_default),
                format_func=lambda k: UPI_APPS[k]["label"],
                key=f"m_sp_app_{v}",
            )

            if st.form_submit_button("Proceed", type="primary", use_container_width=True):
                if amt is None or amt <= 0:
                    st.error("Please enter an amount greater than 0.")
                elif cat_sel == "-":
                    st.error("Please select a category.")
                else:
                    raw_desc = desc.strip()
                    desc_final = raw_desc or pn_txt or pa_txt
                    txn_id = finance_service.add_transaction(
                        float(amt),
                        cat_opts[cat_sel],
                        desc_final,
                        datetime.now(),
                        "Expense",
                        uid,
                        paid_by_cc=paid_by_cc,
                    )
                    st.session_state.pop("m_sp_parsed_qr", None)
                    st.session_state.pop("m_sp_draft", None)
                    st.session_state["m_sp_v"] = v + 1
                    st.session_state["m_sp_handoff"] = {
                        "txn_id": txn_id,
                        "app": pay_app,
                        "amount": float(amt),
                        "parsed_qr": parsed_qr,
                        "note": desc_final,
                        "raw_desc": raw_desc,
                        "cat_label": cat_sel,
                        "paid_by_cc": paid_by_cc,
                    }
                    st.rerun(scope="fragment")

    _scan_pay_frag()
