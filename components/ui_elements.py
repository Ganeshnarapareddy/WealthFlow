import html
import streamlit as st


# Clean inline SVG icons for empty states & UI elements (no emojis as icons)
_EMPTY_SVGS = {
    "default": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 10h18"/><path d="M8 15h4"/>'
        '</svg>'
    ),
    "chart": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3 3v18h18"/><path d="M7 14l4-4 4 3 5-6"/>'
        '</svg>'
    ),
    "wallet": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="2" y="5" width="20" height="14" rx="3"/><path d="M16 12h2"/>'
        '</svg>'
    ),
    "check": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="9"/><path d="m9 12 2 2 4-4"/>'
        '</svg>'
    ),
}


def card_metric(label, value, delta=None, delta_color="normal"):
    """
    Metric card with optional delta, styled via Hallmark token-based rules.
    """
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def stat_strip(items):
    """
    Hallmark hairline-divided KPI strip — no card-in-card, tabular figures, semantic deltas.

    items: list of dicts with keys:
      - label (str)
      - value (str)
      - delta (str | None): optional delta text
      - tone (str): 'neutral' | 'positive' | 'negative' | 'accent'
    """
    if not items:
        return

    cells = []
    for item in items:
        label = html.escape(str(item.get("label", "")))
        value = html.escape(str(item.get("value", "")))
        delta = item.get("delta")
        tone = item.get("tone", "neutral")
        delta_html = ""
        if delta:
            d_esc = html.escape(str(delta))
            delta_html = f'<span class="wf-stat-delta wf-stat-delta--{tone}">{d_esc}</span>'
        cells.append(
            f'<div class="wf-stat-cell">'
            f'  <span class="wf-stat-label">{label}</span>'
            f'  <span class="wf-stat-value">{value}</span>'
            f'  {delta_html}'
            f'</div>'
        )

    cols = len(items)
    st.markdown(
        f'<div class="wf-stat-strip" style="--wf-cols: {cols};">{"".join(cells)}</div>',
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=None):
    """
    Styled section header — sentence case, no tracked caps, no eyebrow.
    """
    t = html.escape(str(title))
    sub = (
        f'<p class="wf-section-sub">{html.escape(str(subtitle))}</p>'
        if subtitle
        else ""
    )
    st.markdown(
        f'<div class="wf-section-head"><h3>{t}</h3>{sub}</div>',
        unsafe_allow_html=True,
    )


def empty_state(title, message, icon="default"):
    """
    Displays a crisp empty state with an inline SVG vector icon (never an emoji).
    """
    svg = _EMPTY_SVGS.get(icon, _EMPTY_SVGS["default"])
    t = html.escape(str(title))
    m = html.escape(str(message))
    st.markdown(
        f"""
        <div class="wf-empty">
            <div class="wf-empty-icon" aria-hidden="true">{svg}</div>
            <div class="wf-empty-title">{t}</div>
            <div class="wf-empty-body">{m}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def skeleton_block(rows=3):
    """
    Static structural skeleton placeholder for loading regions (Hallmark app-screen spec).
    """
    bars = "".join(
        f'<div class="wf-skeleton-line" style="width: {w}%;"></div>'
        for w in ([62, 100, 84, 72, 90][: max(1, rows)])
    )
    st.markdown(f'<div class="wf-skeleton">{bars}</div>', unsafe_allow_html=True)


def chip(text, variant="default"):
    """
    Renders an inline chip/tag. variant: default | accent | success | danger | warning
    """
    cls = "wf-chip"
    if variant in ("accent", "success", "danger", "warning"):
        cls += f" wf-chip--{variant}"
    return f'<span class="{cls}">{html.escape(str(text))}</span>'


def style_plotly(fig, show_legend=False, height=None):
    """
    Applies consistent WealthFlow Hallmark chart styling (Geist, subtle hairlines, clean hover).
    """
    layout_kwargs = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Geist, system-ui, sans-serif", color="#B3BBC9", size=12),
        showlegend=show_legend,
        hoverlabel=dict(
            bgcolor="#1A2130",
            bordercolor="rgba(255,255,255,0.12)",
            font=dict(family="Geist, system-ui, sans-serif", color="#EAECEF", size=12),
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            linecolor="rgba(255,255,255,0.08)",
            zerolinecolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#8A94A6"),
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.07)",
            linecolor="rgba(255,255,255,0.08)",
            zerolinecolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#8A94A6"),
        ),
    )
    if height is not None:
        layout_kwargs["height"] = height
    fig.update_layout(**layout_kwargs)
    return fig
