import html
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.mobile_ui import fmt, m_section, m_empty, m_kpi_strip, style_mobile_plotly, m_css_breakdown


def render_dashboard_view(uid: str, finance_service, credit_card_service, loan_service, budget_service):
    """Artboard 2: Mobile Home Dashboard — Hero Cash Flow, 2x2 KPIs, Compact Alerts, Touch Charts."""
    # Period controls in compact 3-column mobile strip
    years = finance_service.get_available_years(uid)
    year_options = [str(y) for y in years] + ["All"]
    if "m_year" not in st.session_state:
        st.session_state["m_year"] = str(datetime.now().year)
    if "m_month" not in st.session_state:
        st.session_state["m_month"] = "All"
    if "m_mode" not in st.session_state:
        st.session_state["m_mode"] = "Calendar"

    fiscal_day_raw = finance_service.get_setting("fiscal_month_start_day", "1", uid)
    fiscal_day = int(fiscal_day_raw) if str(fiscal_day_raw).isdigit() else 1

    f1, f2, f3 = st.columns([0.33, 0.33, 0.34], vertical_alignment="center")
    with f1:
        try:
            y_idx = year_options.index(str(st.session_state["m_year"]))
        except ValueError:
            y_idx = 0
        sel_y_str = st.selectbox("Year", year_options, index=y_idx, label_visibility="collapsed", key="m_dash_year")
        sel_year = "All" if sel_y_str == "All" else int(sel_y_str)
        st.session_state["m_year"] = sel_year

    with f2:
        month_names = ["All", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        if st.session_state["m_mode"] == "Fiscal" and sel_year != "All":
            m_labels = ["All"] + [finance_service.get_fiscal_month_label(sel_year, m, fiscal_day) for m in range(1, 13)]
        else:
            m_labels = month_names
        try:
            m_idx = 0 if st.session_state["m_month"] == "All" else int(st.session_state["m_month"])
        except (ValueError, TypeError):
            m_idx = 0
        m_idx = max(0, min(m_idx, len(m_labels) - 1))
        sel_m_lbl = st.selectbox("Month", m_labels, index=m_idx, label_visibility="collapsed", key="m_dash_month")
        sel_month = "All" if sel_m_lbl == "All" else m_labels.index(sel_m_lbl)
        st.session_state["m_month"] = sel_month

    with f3:
        mode_opts = ["Calendar", "Fiscal"]
        m_mode = st.selectbox(
            "Mode",
            mode_opts,
            index=0 if st.session_state["m_mode"] == "Calendar" else 1,
            label_visibility="collapsed",
            key="m_dash_mode",
        )
        st.session_state["m_mode"] = m_mode

    fiscal_start_day = fiscal_day if (m_mode == "Fiscal" and sel_year != "All" and sel_month != "All") else 1

    # Single batched Turso HTTP roundtrip for ALL Dashboard KPIs, Credit Cards, Alerts, Wealth
    dash = finance_service.get_dashboard_bundle(uid, sel_year, sel_month, m_mode, fiscal_day)

    net = dash["net_worth"]
    inc = dash["inc"]
    exp = dash["exp"]
    burn = dash["burn"]
    today_spent = dash["today_spent"]
    yesterday_spent = dash["yesterday_spent"]
    prev_inc = dash["prev_inc"]
    prev_exp = dash["prev_exp"]
    total_emi_amt = dash["total_emi_amt"]
    active_emi_count = dash["active_emi_count"]
    active_subs_count = dash["active_subs_count"]

    inc_delta, inc_up = finance_service.get_comparison_delta(inc, prev_inc)
    exp_delta, exp_up = finance_service.get_comparison_delta(exp, prev_exp)
    savings_rate = ((inc - exp) / inc * 100) if inc > 0 else 0.0
    day_pct = ((today_spent - yesterday_spent) / yesterday_spent * 100) if yesterday_spent > 0 else 0.0

    # Hero Cash-Flow Card + 2x2 KPI Grid
    period_badge = f"{sel_y_str}" if sel_month == "All" else f"{month_names[sel_month]} {sel_y_str}"
    m_kpi_strip(
        hero_label="Net worth",
        hero_value=fmt(net),
        hero_badge=period_badge,
        flow_in=inc,
        flow_out=exp,
        items=[
            {
                "label": "Income",
                "value": fmt(inc),
                "delta": inc_delta,
                "tone": "positive" if inc_up else "neutral",
            },
            {
                "label": "Spend",
                "value": fmt(exp),
                "delta": exp_delta,
                "tone": "negative" if exp_up else ("positive" if exp_delta else "neutral"),
            },
            {
                "label": "Today's spend",
                "value": fmt(today_spent),
                "delta": f"{day_pct:+.0f}% vs yest." if yesterday_spent > 0 else None,
                "tone": "negative" if day_pct > 0 else ("positive" if day_pct < 0 else "neutral"),
            },
            {
                "label": "Savings rate",
                "value": f"{savings_rate:.1f}%",
                "delta": f"{active_subs_count} subs · {fmt(burn)}/m",
                "tone": "positive" if savings_rate >= 20 else ("warning" if savings_rate > 0 else "negative"),
            },
        ],
    )

    # Compact Credit Card Utilization & EMI Bar (only if user has cards or EMIs)
    cards_df = dash["cards_df"]
    if not cards_df.empty or active_emi_count > 0:
        total_limit = float(cards_df["card_limit"].sum()) if not cards_df.empty else 0.0
        total_used = float(cards_df["current_balance"].apply(lambda x: -x if x < 0 else 0).sum()) if not cards_df.empty else 0.0
        util = (total_used / total_limit * 100) if total_limit > 0 else 0.0
        m_kpi_strip(
            items=[
                {
                    "label": "Card used",
                    "value": fmt(total_used),
                    "delta": f"{util:.0f}% of {fmt(total_limit)}" if total_limit > 0 else "No limit",
                    "tone": "negative" if util >= 75 else ("warning" if util >= 40 else "positive"),
                },
                {
                    "label": "Monthly EMIs",
                    "value": fmt(total_emi_amt),
                    "delta": f"{active_emi_count} active",
                    "tone": "accent" if active_emi_count > 0 else "neutral",
                },
            ]
        )

    # Compact Upcoming Dues & Alerts
    m_section("Upcoming dues & alerts", "Due within 30 days")
    all_alerts = dash["all_alerts"]
    if not all_alerts:
        st.markdown(
            '<div class="m-list-card"><div class="m-list-left"><div class="m-list-icon">✓</div>'
            '<div><div class="m-list-title">All clear</div>'
            '<div class="m-list-sub">No dues in the next 30 days</div></div></div></div>',
            unsafe_allow_html=True,
        )
    else:
        max_show = 5 if not st.session_state.get("m_alerts_expand") else len(all_alerts)
        for a in all_alerts[:max_show]:
            days = int(a["days"])
            cat = a["category"]
            # Color code alerts: <= 2d: Red (danger), <= 10d: Orange (warning), > 10d: Green (positive)
            tone = "danger" if days <= 2 else ("warning" if days <= 10 else "positive")
            due_txt = "Due today" if days <= 0 else f"In {days}d"

            c1, c2 = st.columns([0.76, 0.24], vertical_alignment="center")
            with c1:
                st.markdown(
                    f"""
                    <div class="m-alert-row tone-{tone}">
                        <div style="min-width:0;">
                            <div class="m-alert-name">{html.escape(str(a['name']))}</div>
                            <div class="m-alert-meta">
                                <span class="m-chip {tone}">{due_txt}</span>
                                <span>{html.escape(str(a['date']))}</span>
                                <span>{html.escape(str(cat))}</span>
                            </div>
                        </div>
                        <div class="m-alert-amt">{html.escape(fmt(a['amount']))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                if cat == "Subscription":
                    if st.button("Paid", key=f"m_alert_sub_{a['id']}", use_container_width=True):
                        finance_service.mark_alert_actioned(a["id"], uid)
                        finance_service.add_transaction(
                            amount=a["amount"], category_id="8", description=f"Auto: {a['name']}",
                            date_obj=datetime.now(), txn_type="Expense", user_id=uid,
                        )
                        st.session_state["m_toast"] = f"Marked {a['name']} paid!"
                        st.rerun()
                elif cat == "EMI":
                    if st.button("Paid", key=f"m_alert_emi_{a['id']}", use_container_width=True):
                        credit_card_service.mark_emi_paid(a["id"])
                        st.session_state["m_toast"] = "EMI payment recorded!"
                        st.rerun()
                elif cat == "Loan":
                    is_given = "Given" in a["name"]
                    if is_given:
                        # For received: no check icon, only text, green hover, same pill size
                        if st.button("Received", key=f"m_alert_receive_{a['id']}", use_container_width=True):
                            if a.get("is_emi"):
                                loan_service.toggle_payment_status(a["id"], "pending")
                            else:
                                loan_service.update_loan_status(a["id"], "paid")
                            st.session_state["m_toast"] = "Loan marked received!"
                            st.rerun()
                    else:
                        if st.button("Paid", key=f"m_alert_paid_{a['id']}", use_container_width=True):
                            if a.get("is_emi"):
                                loan_service.toggle_payment_status(a["id"], "pending")
                            else:
                                loan_service.update_loan_status(a["id"], "paid")
                            st.session_state["m_toast"] = "Loan payment recorded!"
                            st.rerun()
                elif cat == "Bill":
                    if st.button("Paid", key=f"m_alert_bill_{a['id']}", use_container_width=True):
                        credit_card_service.add_transaction(
                            uid, a["id"], a["amount"], f"Bill Payment: {a['name']}", "payment", sync_bank=True,
                        )
                        st.session_state["m_toast"] = "Card bill payment logged!"
                        st.rerun()

        if len(all_alerts) > 5:
            expanded = st.session_state.get("m_alerts_expand", False)
            if st.button(
                "View less" if expanded else "View more",
                key="m_toggle_alerts",
                use_container_width=True,
            ):
                st.session_state["m_alerts_expand"] = not expanded
                st.rerun()

    # Mobile Touch-Friendly Analytics with Lazy Loading (<100ms sub-tab switches)
    m_section("Analytics")

    @st.fragment
    def _render_analytics_fragment():
        if "m_dash_tab" not in st.session_state:
            st.session_state["m_dash_tab"] = "Category"

        active_tab = st.segmented_control(
            "Analytics View",
            ["Category", "Daily", "In/Out", "Trend", "Wealth", "Budgets"],
            default=st.session_state["m_dash_tab"],
            label_visibility="collapsed",
            key="m_dash_analytics_seg",
        )
        if active_tab is not None:
            st.session_state["m_dash_tab"] = active_tab
        cur_tab = st.session_state["m_dash_tab"]

        if cur_tab == "Category":
            df_sp = finance_service.get_spending_by_category(uid, sel_year, sel_month, start_day=fiscal_start_day)
            if not df_sp.empty:
                tot_spend = float(df_sp["Amount"].sum()) or 1.0
                top_df = df_sp.head(10)
                items = [
                    {
                        "label": r["Category"],
                        "amount_str": fmt(r["Amount"]),
                        "pct": (float(r["Amount"]) / tot_spend) * 100,
                        "color": "linear-gradient(90deg, #4F86F7, #60A5FA)",
                    }
                    for _, r in top_df.iterrows()
                ]
                m_css_breakdown(items, empty_title="No spending data", empty_sub="Log an expense via the + button to see category breakdown.")
            else:
                m_empty("No spending data", "Log an expense via the + button to see category breakdown.")

        elif cur_tab == "Daily":
            df_dy = finance_service.get_daily_spending_by_category(uid, sel_year, sel_month, start_day=fiscal_start_day)
            if not df_dy.empty:
                daily_tot = df_dy.groupby("Date", as_index=False)["Amount"].sum()
                daily_tot["_dt"] = pd.to_datetime(daily_tot["Date"], errors="coerce")
                # Show newest/today's date first on the left, up to 14 active days
                daily_tot = daily_tot.dropna(subset=["_dt"]).sort_values("_dt", ascending=False).head(14)
                yrs_present = sorted(daily_tot["_dt"].dt.year.unique().tolist())
                yr_lbl = str(yrs_present[0]) if len(yrs_present) == 1 else f"{yrs_present[0]}–{yrs_present[-1]}"
                st.markdown(f'<span class="m-chip accent" style="margin-bottom:4px;">{yr_lbl} · Latest {len(daily_tot)} active days (Newest first)</span>', unsafe_allow_html=True)
                daily_tot["DayLabel"] = daily_tot["_dt"].dt.strftime("%d %b")
                day_order = daily_tot["DayLabel"].tolist()
                fig_d = px.bar(daily_tot, x="DayLabel", y="Amount", text_auto=".2s", color_discrete_sequence=["#60A5FA"])
                style_mobile_plotly(fig_d, height=255)
                fig_d.update_traces(textposition="outside", cliponaxis=False, marker_cornerradius=5)
                fig_d.update_layout(
                    xaxis=dict(
                        type="category",
                        title="",
                        tickangle=-35,
                        fixedrange=True,
                        categoryorder="array",
                        categoryarray=day_order,
                    ),
                    yaxis=dict(title="", fixedrange=True),
                    margin=dict(l=8, r=12, t=24, b=46),
                )
                st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})
            else:
                m_empty("No daily expenses", "Daily totals appear here once you log expenses.")

        elif cur_tab == "In/Out":
            df_ie = finance_service.get_income_expense_by_month(uid, sel_year, sel_month)
            if not df_ie.empty:
                df_ie = df_ie.tail(6)
                fig_ie = go.Figure()
                fig_ie.add_trace(go.Bar(name="Income", x=df_ie["Month"], y=df_ie["Income"], marker_color="#34D399"))
                fig_ie.add_trace(go.Bar(name="Expense", x=df_ie["Month"], y=df_ie["Expense"], marker_color="#F87171"))
                style_mobile_plotly(fig_ie, height=255, show_legend=True)
                fig_ie.update_layout(barmode="group", xaxis=dict(title="", tickangle=-25), yaxis=dict(title=""))
                st.plotly_chart(fig_ie, use_container_width=True, config={"displayModeBar": False})
            else:
                m_empty("No cash flow data", "Log income and expenses to compare months.")

        elif cur_tab == "Trend":
            df_tr = finance_service.get_spending_trend(uid, sel_year, sel_month, months=8)
            if not df_tr.empty:
                fig_tr = px.area(df_tr, x="Month", y="Amount", markers=True, color_discrete_sequence=["#4F86F7"])
                style_mobile_plotly(fig_tr, height=250)
                fig_tr.update_layout(xaxis=dict(title="", tickangle=-25), yaxis=dict(title=""))
                st.plotly_chart(fig_tr, use_container_width=True, config={"displayModeBar": False})
            else:
                m_empty("No trend data", "Spending trend updates automatically each month.")

        elif cur_tab == "Wealth":
            asset_data = dash["asset_data"]
            if asset_data:
                wdf = pd.DataFrame(asset_data).sort_values("Amount", ascending=False)
                tot_wealth = float(wdf["Amount"].sum()) or 1.0
                w_items = [
                    {
                        "label": r["Category"],
                        "amount_str": fmt(r["Amount"]),
                        "pct": (float(r["Amount"]) / tot_wealth) * 100,
                        "color": "linear-gradient(90deg, #10B981, #34D399)",
                    }
                    for _, r in wdf.iterrows()
                ]
                m_css_breakdown(w_items, empty_title="No assets tracked", empty_sub="Add assets under More → Assets to view wealth allocation.")
            else:
                m_empty("No assets tracked", "Add assets under More → Assets to view wealth allocation.")

        elif cur_tab == "Budgets":
            now = datetime.now()
            bm = sel_month if sel_month != "All" else now.month
            by = sel_year if sel_year != "All" else now.year
            df_b = budget_service.get_monthly_budgets(uid, bm, by)
            if not df_b.empty:
                for _, row in df_b.iterrows():
                    pct = min(1.0, max(0.0, float(row["Progress"]) / 100.0))
                    tone = "negative" if row["Progress"] >= 100 else ("warning" if row["Progress"] >= 80 else "positive")
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;align-items:center;font-size:13px;margin-top:4px;">'
                        f'<strong style="color:#F3F5F8;">{html.escape(str(row["Category"]))}</strong>'
                        f'<span class="m-chip {tone} m-mono">{fmt(row["Spent"])} / {fmt(row["Limit"])}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.progress(pct)
            else:
                m_empty("No budgets set", "Create monthly category limits under More → Budgets.")

    _render_analytics_fragment()
