import html
import streamlit as st


def fmt(val) -> str:
    sym = st.session_state.get("sym", "₹")
    if val is None:
        return f"{sym}0.00"
    return f"{sym}{float(val):,.2f}"


def m_section(title: str, subtitle: str | None = None):
    sub_html = f'<div class="m-sec-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="m-sec-head">{html.escape(title)}</div>{sub_html}', unsafe_allow_html=True)


def m_empty(title: str, subtitle: str):
    st.markdown(
        f'<div class="m-empty">'
        f'<div class="m-empty-title">{html.escape(title)}</div>'
        f'<div class="m-empty-sub">{html.escape(subtitle)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def m_kpi_strip(items: list[dict], hero_label: str | None = None, hero_value: str | None = None,
                hero_badge: str | None = None, flow_in: float = 0.0, flow_out: float = 0.0):
    """Renders a sleek obsidian mobile hero + 2x2 hairline KPI grid."""
    top_html = ""
    if hero_label is not None and hero_value is not None:
        badge_html = f'<span class="m-chip accent">{html.escape(hero_badge)}</span>' if hero_badge else ""
        top_html = (
            f'<div class="m-hero-top">'
            f'<div><div class="m-hero-label">{html.escape(hero_label)}</div>'
            f'<div class="m-hero-val">{html.escape(hero_value)}</div></div>'
            f'{badge_html}'
            f'</div>'
        )

    bar_html = ""
    total_flow = max(0.0, float(flow_in or 0)) + max(0.0, float(flow_out or 0))
    if total_flow > 0:
        in_pct = max(2, min(98, round(float(flow_in) / total_flow * 100)))
        out_pct = 100 - in_pct
        bar_html = f'<div class="m-flow-bar"><div class="m-flow-in" style="width:{in_pct}%"></div><div class="m-flow-out" style="width:{out_pct}%"></div></div>'

    cells = []
    for it in items:
        lbl = html.escape(str(it.get("label", "")))
        val = html.escape(str(it.get("value", "")))
        delta = it.get("delta")
        tone = it.get("tone", "neutral")
        delta_html = f'<span class="m-chip {tone}">{html.escape(str(delta))}</span>' if delta else ""
        cells.append(f'<div class="m-kpi-cell"><div class="m-kpi-label">{lbl}</div><div class="m-kpi-val">{val}</div>{delta_html}</div>')

    grid_style = ' style="border-top:0;padding-top:0;"' if not top_html else ""
    grid_html = f'<div class="m-kpi-grid"{grid_style}>{"".join(cells)}</div>' if cells else ""

    st.markdown(f'<div class="m-hero-card">{top_html}{bar_html}{grid_html}</div>', unsafe_allow_html=True)


def m_delete_popover(item_id, button_key: str, delete_fn, item_name: str = "this item",
                     pass_user_id: str | None = None, fragment_scope: bool = False, toast_msg: str | None = None):
    """Viewport-safe mobile delete confirmation popover (instant open, Yes/No never wrap)."""
    with st.popover("", icon=":material/delete_outline:", help=f"Delete {item_name}"):
        st.markdown(
            f'<div class="wf-m-del-msg">Delete <strong>{html.escape(str(item_name))}</strong>?</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes", icon=":material/check:", type="primary", use_container_width=True, key=f"m_yes_{button_key}"):
                if pass_user_id is not None:
                    delete_fn(item_id, pass_user_id)
                else:
                    delete_fn(item_id)
                if toast_msg:
                    st.session_state["m_toast"] = toast_msg
                st.rerun(scope="fragment" if fragment_scope else "app")
        with c2:
            if st.button("No", icon=":material/close:", use_container_width=True, key=f"m_no_{button_key}"):
                st.rerun(scope="fragment" if fragment_scope else "app")


def style_mobile_plotly(fig, height: int = 260, show_legend: bool = False):
    """Configures Plotly charts cleanly for 375–430px portrait touch viewports."""
    fig.update_layout(
        paper_bgcolor="rgba(17,23,36,0)",
        plot_bgcolor="rgba(17,23,36,0)",
        font=dict(family="Geist, -apple-system, sans-serif", color="#9CA6B8", size=11),
        height=height,
        margin=dict(l=8, r=12, t=20, b=32),
        showlegend=show_legend,
        dragmode=False,
        hoverlabel=dict(bgcolor="#182132", bordercolor="rgba(255,255,255,0.16)", font=dict(color="#F3F5F8", size=12)),
        xaxis=dict(showgrid=False, zeroline=False, fixedrange=True, tickfont=dict(size=10, color="#9CA6B8")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False, fixedrange=True, tickfont=dict(size=10, color="#9CA6B8")),
    )
    if show_legend:
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10))
        )
    return fig
