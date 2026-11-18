import html
import streamlit as st
from streamlit_javascript import st_javascript


def render_auth_view(logo_b64: str | None, auth_service, cookies, db):
    """Artboard 1: Clean iPhone-centered Sign in / Create account / Reset password screen."""
    logo_html = (
        f'<img src="{logo_b64}" alt="WealthFlow" style="width:54px;height:54px;border-radius:14px;'
        f'object-fit:contain;background:#111724;border:1px solid rgba(255,255,255,0.16);padding:4px;">'
        if logo_b64
        else '<div style="width:54px;height:54px;border-radius:14px;background:rgba(79,134,247,0.16);'
             'border:1px solid rgba(79,134,247,0.35);color:#4F86F7;display:grid;place-items:center;'
             'font-weight:700;font-size:20px;margin:0 auto;">WF</div>'
    )
    st.markdown(
        f"""
        <div style="text-align:center; padding: 24px 0 14px 0;">
            {logo_html}
            <div style="font-size:23px; font-weight:700; color:#F3F5F8; margin-top:10px; letter-spacing:-0.02em;">WealthFlow</div>
            <div style="font-size:13px; color:#9CA6B8; margin-top:2px;">Mobile Finance Manager</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_signup, tab_reset = st.tabs(["Sign in", "Create account", "Reset"])

    with tab_login:
        with st.form("m_login_form"):
            l_user = st.text_input("Username", placeholder="Enter your username")
            l_pass = st.text_input("Password", type="password", placeholder="Enter your password")
            remember = st.checkbox("Keep me signed in (30 days)", value=True)
            if st.form_submit_button("Sign in", type="primary", use_container_width=True):
                if not l_user or not l_pass:
                    st.error("Please enter both username and password.")
                else:
                    user = auth_service.login(l_user, l_pass)
                    if user:
                        if remember:
                            token = auth_service.create_session(user["id"])
                            cookies["wealthflow_remember_token"] = token
                            cookies.save()
                            st_javascript(f"localStorage.setItem('wealthflow_remember_token', '{token}');")
                        st.session_state.user = user
                        st.session_state["m_page"] = "Home"
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

    with tab_signup:
        with st.form("m_signup_form"):
            s_user = st.text_input("Username *", placeholder="Choose a username")
            s_email = st.text_input("Email *", placeholder="you@example.com")
            s_phone = st.text_input("Phone", placeholder="Optional")
            s_pass = st.text_input("Password *", type="password", placeholder="At least 6 characters")
            if st.form_submit_button("Create account", type="primary", use_container_width=True):
                if not s_user or not s_pass or not s_email:
                    st.error("Username, email, and password are required.")
                elif len(s_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    ok, msg = auth_service.signup(s_user.strip(), s_pass, s_email.strip(), s_phone.strip())
                    if ok:
                        st.success("Account created! Switch to Sign in to continue.")
                    else:
                        st.error(msg)

    with tab_reset:
        with st.form("m_reset_form"):
            r_user = st.text_input("Username *", placeholder="Your username")
            r_email = st.text_input("Registered Email *", placeholder="you@example.com")
            r_new = st.text_input("New Password *", type="password", placeholder="At least 6 characters")
            if st.form_submit_button("Verify & Reset Password", type="primary", use_container_width=True):
                if not r_user or not r_email or not r_new:
                    st.error("All fields are required.")
                elif len(r_new) < 6:
                    st.error("New password must be at least 6 characters.")
                else:
                    res = db.execute(
                        "SELECT id FROM wf_users WHERE LOWER(TRIM(username)) = LOWER(TRIM(?)) AND LOWER(TRIM(email)) = LOWER(TRIM(?))",
                        (r_user, r_email),
                    )
                    if res and res.rows:
                        auth_service.update_password(res.rows[0][0], r_new)
                        st.success("Password updated! You can now sign in.")
                    else:
                        st.error("No matching account found for that username and email.")
