import streamlit as st

def card_metric(label, value, delta=None, delta_color="normal"):
    """
    Custom metric card with optional delta.
    """
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)

def section_header(title, subtitle=None):
    """
    Styled section header.
    """
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f"<p style='color: #94a3b8; margin-top: -10px;'>{subtitle}</p>", unsafe_allow_html=True)

def empty_state(title, message, icon="🔍"):
    """
    Displays a friendly empty state when no data is available.
    """
    st.markdown(f"""
        <div style="text-align: center; padding: 50px; background: rgba(30, 41, 59, 0.2); border-radius: 16px;">
            <div style="font-size: 50px; margin-bottom: 20px;">{icon}</div>
            <h4 style="margin-bottom: 10px;">{title}</h4>
            <p style="color: #94a3b8;">{message}</p>
        </div>
    """, unsafe_allow_html=True)
