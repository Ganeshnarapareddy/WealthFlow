import html
import streamlit as st

from components.mobile_ui import fmt, m_empty, m_delete_popover


def render_ledger_view(uid: str, finance_service, credit_card_service):
    """Artboard 4: Mobile Transaction Ledger — Search bar, collapsible filter drawer, compact rows."""
    sel_desc = st.text_input(
        "Search",
        placeholder="Search notes or description...",
        label_visibility="collapsed",
        key="m_hist_search",
    )

    all_cats_df = finance_service.get_categories(uid)
    cat_opts = ["All"] + list(all_cats_df["name"].unique()) if not all_cats_df.empty else ["All"]
    years = finance_service.get_available_years(uid)

    with st.expander("Filters", icon=":material/tune:"):
        fc1, fc2 = st.columns(2)
        with fc1:
            sel_y = st.selectbox("Year", ["All"] + [str(y) for y in years], key="m_hist_y")
        with fc2:
            m_names = ["All", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            sel_m_lbl = st.selectbox("Month", m_names, key="m_hist_m")
            sel_m = "All" if sel_m_lbl == "All" else m_names.index(sel_m_lbl)

        fc3, fc4 = st.columns(2)
        with fc3:
            sel_t = st.selectbox("Type", ["All", "Expense", "Income"], key="m_hist_t")
        with fc4:
            sel_cat = st.selectbox("Category", cat_opts, key="m_hist_cat")

        cc_only = st.checkbox("Paid with CC only", value=False, key="m_hist_cc_only")

    df = finance_service.get_filtered_transactions(
        uid,
        year=sel_y,
        month=sel_m,
        day="All",
        txn_type=sel_t,
        description_search=sel_desc,
        category_name=sel_cat,
        limit=100,
        cc_filter="Paid with CC only" if cc_only else "All",
    )

    if df.empty:
        m_empty("No transactions found", "Tap the + button in the dock to log your first entry.")
        return

    st.caption(f"Showing {len(df)} transactions")

    for _, row in df.iterrows():
        is_exp = row["Type"] == "Expense"
        is_cc = bool(row.get("PaidByCC"))
        color = "#F87171" if is_exp else "#34D399"
        sign = "-" if is_exp else "+"
        desc_txt = html.escape(str(row["Description"] or row["Category"]))
        cat_txt = html.escape(str(row["Category"]))
        dt_txt = html.escape(str(row["Date"])[:10])
        icon_txt = html.escape(str(row["Icon"] or "•"))
        cc_badge = '<span class="m-cc-badge">CC</span>' if is_cc else ""

        c1, c2 = st.columns([0.84, 0.16], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<div class="m-list-card">'
                f'<div class="m-list-left">'
                f'<div class="m-list-icon">{icon_txt}</div>'
                f'<div style="min-width:0;flex:1;">'
                f'<div class="m-list-title">{desc_txt}</div>'
                f'<div class="m-list-sub">{cat_txt} · {dt_txt}</div>'
                f'</div>'
                f'</div>'
                f'<div class="m-list-right">'
                f'{cc_badge}'
                f'<div class="m-list-amt" style="color:{color};">{sign}{html.escape(fmt(row["Amount"]))}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c2:
            del_fn = finance_service.delete_transaction if row["Source"] == "main" else credit_card_service.delete_transaction
            m_delete_popover(
                row["ID"],
                f"txn_{row['ID']}_{row['Source']}",
                del_fn,
                item_name=str(row["Description"] or row["Category"]),
                pass_user_id=uid,
                toast_msg="Transaction deleted & balance updated.",
            )
