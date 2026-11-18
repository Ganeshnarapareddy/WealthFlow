import streamlit as st

def card_metric(label, value, delta=None, delta_color="normal"):
    """
    Custom metric card with optional delta.
    Uses Hallmark token-based metric-container styles.
    """
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def section_header(title, subtitle=None):
    """
    Styled section header — left-accent stripe, sentence case, no tracked caps.
    """
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(
            f"<p style='color: var(--color-ink-3, #64748b); margin-top: -0.5rem; "
            f"font-size: 0.8125rem;'>{subtitle}</p>",
            unsafe_allow_html=True
        )


def empty_state(title, message, icon=""):
    """
    Displays a friendly empty state when no data is available.
    Uses .wf-empty token-based card styles.
    """
    st.markdown(f"""
        <div class="wf-empty">
            <span class="wf-empty-icon" aria-hidden="true">{icon}</span>
            <div class="wf-empty-title">{title}</div>
            <div class="wf-empty-body">{message}</div>
        </div>
    """, unsafe_allow_html=True)


def chip(text, variant="default"):
    """
    Renders an inline chip/tag. variant: default | accent | success | danger
    """
    cls = "wf-chip"
    if variant == "accent":
        cls += " wf-chip--accent"
    elif variant == "success":
        cls += " wf-chip--success"
    elif variant == "danger":
        cls += " wf-chip--danger"
    return f'<span class="{cls}">{text}</span>'
