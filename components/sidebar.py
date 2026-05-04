import streamlit as st
from datetime import datetime

def render_sidebar(user_data, logo_b64, finance_service, auth_service, cookies):
    """
    Renders the premium NexGen-style sidebar.
    """
    with st.sidebar:
        # 1. Branding Section
        logo_html = f'<img src="{logo_b64}">' if logo_b64 else "💎"
        st.markdown(f"""
            <div class="sidebar-branding">
                {logo_html}
                <div class="sidebar-title">WealthFlow</div>
                <div class="sidebar-subtitle">Made by Ganesh Narapareddy</div>
            </div>
        """, unsafe_allow_html=True)

        # 2. User Info Box
        username = user_data.get('username', 'User')
        role = user_data.get('role', 'User').upper()
        st.markdown(f"""
            <div class="sidebar-user-box">
                <div class="sidebar-welcome">Welcome, <span class="sidebar-username">{username} ({role})</span></div>
            </div>
        """, unsafe_allow_html=True)

        # 3. Currency Selector (Replacing Language Toggle)
        st.markdown("<p style='color: #94a3b8; font-size: 0.8rem; margin-bottom: 5px; padding-left: 10px;'>Currency</p>", unsafe_allow_html=True)
        sym_map = {"INR (₹)": "₹", "USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
        
        # Get current index
        current_sym = st.session_state.get('sym', '₹')
        try:
            curr_idx = list(sym_map.values()).index(current_sym)
        except:
            curr_idx = 0
            
        selected_label = st.selectbox(
            "Currency", 
            options=list(sym_map.keys()), 
            index=curr_idx, 
            key="sb_currency_sel", 
            label_visibility="collapsed"
        )
        
        if sym_map[selected_label] != current_sym:
            st.session_state['sym'] = sym_map[selected_label]
            # Save to database
            finance_service.update_setting('currency_symbol', sym_map[selected_label], user_data['id'])
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # 4. Navigation Menu
        pages = {
            "Dashboard": "📊 Dashboard",
            "Transactions": "💸 Transactions",
            "Budgets": "📋 Budgets",
            "Subscriptions": "💳 Subscriptions",
            "Loans": "💰 Loans and EMI",
            "Credit Cards": "💳 Credit Cards",
            "Goals": "🎯 Goals",
            "Assets": "📈 Assets",
            "Settings": "⚙️ Settings"
        }

        # Admin only page
        if user_data.get('role') == 'admin':
            pages["Admin"] = "👥 User Management"

        current_page = st.session_state.get('page', 'Dashboard')

        for p_id, p_label in pages.items():
            is_active = (current_page == p_id)
            
            # Use a container to apply active styling
            if is_active:
                st.markdown(f'<div class="nav-active">', unsafe_allow_html=True)
            
            if st.button(p_label, key=f"sb_nav_{p_id}", use_container_width=True):
                st.session_state['page'] = p_id
                # Reset transaction filters when moving between pages
                for k in ["hist_year", "hist_month", "hist_day", "hist_type"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
                
            if is_active:
                st.markdown('</div>', unsafe_allow_html=True)

        # 5. Bottom Section (Profile & Logout)
        st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
        
        # Profile Popover (using the one from Dashboard but in sidebar)
        with st.popover("👤 Edit Profile", use_container_width=True):
            st.markdown(f"**Username:** `{user_data['username']}`")
            sid_display = user_data.get('short_id', 'N/A')
            st.markdown(f"**System ID:** `{sid_display}`")
            st.markdown("---")
            new_name = st.text_input("Change Username", value=user_data['username'], key="sb_change_user")
            if st.button("Update Name", key="sb_btn_update_name", use_container_width=True):
                if auth_service.update_username(user_data['id'], new_name):
                    st.session_state.user['username'] = new_name
                    st.success("Name updated!")
                    st.rerun()
                else:
                    st.error("Name already taken")
        
        if st.button("🔓 Logout", key="sb_logout", use_container_width=True):
            token = cookies.get('wealthflow_remember_token')
            auth_service.clear_session(token)
            if token:
                del cookies['wealthflow_remember_token']
                cookies.save()
            # Clear localStorage backup
            st.session_state.user = None
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)
