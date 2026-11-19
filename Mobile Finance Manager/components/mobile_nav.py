import html
import streamlit as st
from streamlit_javascript import st_javascript


MORE_SUBPAGES = {
    "Budgets": "Budgets",
    "Subscriptions": "Subscriptions",
    "Loans": "Loans & EMI",
    "Credit Cards": "Credit Cards",
    "Goals": "Goals",
    "Assets": "Assets",
    "Settings": "Settings",
    "Admin": "User Management",
}

PAGE_TITLES = {
    "Home": "WealthFlow",
    "Ledger": "Ledger",
    "QuickAdd": "Quick Add",
    "Trips": "TripFlow",
    "More": "More",
    **MORE_SUBPAGES,
}

SYM_MAP = {"INR (₹)": "₹", "USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
COMPACT_SYM_MAP = {"₹ INR": "₹", "$ USD": "$", "€ EUR": "€", "£ GBP": "£"}
CODE_BY_SYM = {"₹": "INR", "$": "USD", "€": "EUR", "£": "GBP"}


def render_mobile_topbar(user_data: dict, logo_b64: str | None, finance_service, auth_service, cookies):
    """Flush top-left sticky mobile header: WealthFlow | interactive Currency dropdown | square Profile menu."""
    cur_page = st.session_state.get("m_page", "Home")
    is_subpage = cur_page in MORE_SUBPAGES
    title_txt = html.escape(PAGE_TITLES.get(cur_page, cur_page))
    username = html.escape(str(user_data.get("username", "User")))
    sid = html.escape(str(user_data.get("short_id") or "—"))

    if is_subpage:
        c_back, c_title, c_cur, c_prof = st.columns([0.13, 0.45, 0.27, 0.15], vertical_alignment="center")
        with c_back:
            if st.button("", icon=":material/arrow_back:", key="m_top_back", help="Back to More"):
                st.session_state["m_page"] = "More"
                st.rerun()
        with c_title:
            st.markdown(f'<div class="wf-m-top-brand"><div class="wf-m-top-title">{title_txt}</div></div>', unsafe_allow_html=True)
    else:
        c_title, c_cur, c_prof = st.columns([0.58, 0.27, 0.15], vertical_alignment="center")
        with c_title:
            logo_el = f'<img class="wf-m-top-logo" src="{logo_b64}" alt="WF">' if logo_b64 else ""
            st.markdown(
                f'<div class="wf-m-top-brand">{logo_el}<div class="wf-m-top-title">{title_txt}</div></div>',
                unsafe_allow_html=True,
            )

    with c_cur:
        c_labels = list(COMPACT_SYM_MAP.keys())
        cur_sym = st.session_state.get("sym", "₹")
        try:
            c_idx = list(COMPACT_SYM_MAP.values()).index(cur_sym)
        except ValueError:
            c_idx = 0
        picked_curr = st.selectbox(
            "Currency",
            c_labels,
            index=c_idx,
            label_visibility="collapsed",
            key="m_top_curr_sel",
        )
        if COMPACT_SYM_MAP[picked_curr] != cur_sym:
            new_sym = COMPACT_SYM_MAP[picked_curr]
            st.session_state["sym"] = new_sym
            finance_service.set_setting("currency_symbol", new_sym, user_data["id"])
            finance_service.set_setting("currency", CODE_BY_SYM.get(new_sym, "INR"), user_data["id"])
            st.rerun()

    with c_prof:
        with st.popover("", icon=":material/person:", key="m_profile_pop", help="Account & settings"):
            st.markdown(
                f'<div class="wf-m-profile-head">'
                f'<div class="wf-m-profile-name">{username}</div>'
                f'<div class="wf-m-profile-id">ID {sid}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Settings & Profile", icon=":material/tune:", key="m_prof_settings", use_container_width=True):
                st.session_state["m_page"] = "Settings"
                st.rerun()

            if st.button("Log out", icon=":material/logout:", key="m_prof_logout", use_container_width=True):
                from components.auth_cookie import get_persisted_token, inject_clear_token_script
                token = get_persisted_token(cookies)
                if token:
                    auth_service.clear_session(token)
                try:
                    cookies["wealthflow_remember_token"] = ""
                    cookies.save()
                except Exception:
                    pass
                inject_clear_token_script()
                st.session_state.user = None
                st.session_state.pop("_auth_save_token", None)
                st.session_state.pop("_auth_token_active", None)
                st.rerun()


def render_mobile_dock():
    """Fixed 5-slot iOS thumb-zone bottom navigation dock."""
    cur_page = st.session_state.get("m_page", "Home")
    active_dock = "More" if cur_page in MORE_SUBPAGES else cur_page

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("Home", icon=":material/home:", key="m_dock_home", type="primary" if active_dock == "Home" else "secondary", use_container_width=True):
            st.session_state["m_page"] = "Home"
            st.rerun()
    with c2:
        if st.button("Ledger", icon=":material/receipt_long:", key="m_dock_ledger", type="primary" if active_dock == "Ledger" else "secondary", use_container_width=True):
            st.session_state["m_page"] = "Ledger"
            st.rerun()
    with c3:
        if st.button("", icon=":material/add:", key="m_dock_add"):
            st.session_state["m_page"] = "QuickAdd"
            st.rerun()
    with c4:
        if st.button("Trips", icon=":material/flight_takeoff:", key="m_dock_trips", type="primary" if active_dock == "Trips" else "secondary", use_container_width=True):
            st.session_state["m_page"] = "Trips"
            st.rerun()
    with c5:
        if st.button("More", icon=":material/grid_view:", key="m_dock_more", type="primary" if active_dock == "More" else "secondary", use_container_width=True):
            st.session_state["m_page"] = "More"
            st.rerun()
