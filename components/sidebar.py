import html
import json
import streamlit as st
import streamlit.components.v1 as components


# Navigation catalog — (page_id, label, material_icon)
NAV_ITEMS = [
    ("Dashboard", "Dashboard", ":material/space_dashboard:"),
    ("Transactions", "Transactions", ":material/receipt_long:"),
    ("Budgets", "Budgets", ":material/pie_chart:"),
    ("Subscriptions", "Subscriptions", ":material/autorenew:"),
    ("Loans", "Loans & EMI", ":material/account_balance:"),
    ("Credit Cards", "Credit Cards", ":material/credit_card:"),
    ("Goals", "Goals", ":material/flag:"),
    ("Assets", "Assets", ":material/show_chart:"),
    ("TripFlow", "TripFlow", ":material/flight_takeoff:"),
    ("Settings", "Settings", ":material/tune:"),
]

# Pin SVG — hollow outline (unpinned) & solid filled (pinned)
_SVG_PIN_OUTLINE = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 17v5"/><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/>'
    '</svg>'
)

_SVG_PIN_FILLED = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" '
    'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 17v5"/><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/>'
    '</svg>'
)

_SVG_SEARCH = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>'
    '</svg>'
)


def _user_initials(username: str) -> str:
    parts = [p for p in str(username or "U").strip().split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return (parts[0][:2] if parts else "U").upper()


def render_topbar(user_data, current_page_label: str, finance_service, auth_service, cookies):
    """
    Renders the 56px sticky top bar with:
      - Left: WealthFlow / Current Page breadcrumb
      - Right: Jump to… (Ctrl K) trigger, currency pill, and interactive RO profile menu
        (Edit profile, Currency, Settings, Log out — no User Management)
    """
    username = html.escape(str(user_data.get("username", "User")))
    initials = _user_initials(user_data.get("username", "U"))
    sid_display = html.escape(str(user_data.get("short_id", "N/A")))
    sym = html.escape(str(st.session_state.get("sym", "₹")))
    sym_raw = st.session_state.get("sym", "₹")
    curr_codes = {"₹": "INR", "$": "USD", "€": "EUR", "£": "GBP"}
    curr_code = curr_codes.get(sym_raw, "INR")
    page_esc = html.escape(current_page_label)

    col_left, col_tools, col_curr, col_profile = st.columns([5.4, 2.3, 1.1, 1.2], vertical_alignment="center")

    with col_left:
        st.markdown(
            f"""
            <div class="wf-topbar-left wf-topbar-marker" role="banner">
                <button type="button" id="wf-crumb-home" class="wf-topbar-crumb wf-topbar-crumb-btn" title="Go to Dashboard" aria-label="Go to WealthFlow Dashboard">WealthFlow</button>
                <span class="wf-topbar-sep" aria-hidden="true">/</span>
                <span class="wf-topbar-page">{page_esc}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_tools:
        st.markdown(
            f"""
            <div class="wf-topbar-tools">
                <button type="button" class="wf-cmd-trigger" id="wf-cmd-open" aria-label="Quick jump to page">
                    {_SVG_SEARCH}
                    <span>Jump to…</span>
                    <span class="wf-kbd">Ctrl K</span>
                </button>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_curr:
        with st.popover(f"{sym_raw} {curr_code}", icon=":material/payments:", key="tb_curr_pop", help="Switch display currency"):
            sym_map = {"INR (₹)": "₹", "USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
            current_sym = st.session_state.get("sym", "₹")
            try:
                curr_idx = list(sym_map.values()).index(current_sym)
            except ValueError:
                curr_idx = 0

            selected_label = st.selectbox(
                "Display Currency",
                options=list(sym_map.keys()),
                index=curr_idx,
                key="tb_currency_sel",
            )
            if sym_map[selected_label] != current_sym:
                new_s = sym_map[selected_label]
                st.session_state["sym"] = new_s
                finance_service.set_setting("currency_symbol", new_s, user_data["id"])
                finance_service.set_setting("currency", curr_codes.get(new_s, "INR"), user_data["id"])
                st.rerun()

    with col_profile:
        with st.popover(f"{username}", icon=":material/person:", key="tb_profile_pop", help=f"{user_data.get('username', 'User')} — Profile & account"):
            st.markdown(
                f"""
                <div class="wf-profile-head">
                    <div class="wf-profile-name">{username}</div>
                    <div class="wf-profile-meta">ID {sid_display}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 1. Edit Profile (inline expander)
            with st.expander("Edit profile", icon=":material/edit:"):
                new_name = st.text_input(
                    "Username", value=user_data["username"], key="tb_change_user"
                )
                if st.button(
                    "Update name",
                    key="tb_btn_update_name",
                    type="primary",
                    use_container_width=True,
                ):
                    if auth_service.update_username(user_data["id"], new_name):
                        st.session_state.user["username"] = new_name
                        st.success("Username updated.")
                        st.rerun()
                    else:
                        st.error("Username already taken.")

            # 3. Settings
            if st.button(
                "Settings",
                key="tb_nav_settings",
                icon=":material/tune:",
                use_container_width=True,
            ):
                st.session_state["page"] = "Settings"
                st.rerun()

            # 4. Log out
            if st.button(
                "Log out",
                key="tb_logout",
                icon=":material/logout:",
                use_container_width=True,
            ):
                from components.auth_cookie import get_persisted_token, inject_clear_token_script
                token = get_persisted_token(cookies)
                if token:
                    auth_service.clear_session(token)
                try:
                    del cookies["wealthflow_remember_token"]
                    cookies.save()
                except Exception:
                    pass
                inject_clear_token_script()
                st.session_state.user = None
                st.session_state.pop("_auth_save_token", None)
                st.rerun()


def _mount_shell_controller(nav_entries, current_page_label: str):
    """
    Mounts a self-healing controller directly onto window.parent so handlers never
    go stale when Streamlit recreates the components.html iframe across reruns:
      - Pin / unpin desktop hover-expand rail (turns red + filled icon when pinned)
      - Ctrl+K / Cmd+K Quick Jump Command Palette (real navigation on click & Enter)
      - Mobile bottom tab bar wired directly to real Streamlit sidebar buttons
    """
    items_json = json.dumps(
        [{"id": pid, "label": label} for pid, label, _ in nav_entries]
    )
    active_json = json.dumps(current_page_label)
    pin_outline_json = json.dumps(_SVG_PIN_OUTLINE)
    pin_filled_json = json.dumps(_SVG_PIN_FILLED)

    components.html(
        f"""
        <script>
        (function() {{
            const doc = window.parent.document;
            const win = window.parent;

            const PIN_OUTLINE = {pin_outline_json};
            const PIN_FILLED = {pin_filled_json};

            /* Store live state on window.parent so callbacks never capture dead iframe closures */
            win.__wf = win.__wf || {{}};
            win.__wf.items = {items_json};
            win.__wf.active = {active_json};
            win.__wf.filtered = win.__wf.items.slice();
            win.__wf.selectedIdx = 0;

            function clickSidebarPage(targetLabel) {{
                const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) return false;
                const wanted = String(targetLabel || '').trim().toLowerCase();
                const btns = sidebar.querySelectorAll('button');
                for (const b of btns) {{
                    const mdP = b.querySelector('[data-testid="stMarkdownContainer"] p') || b.querySelector('p');
                    const rawText = (mdP ? mdP.textContent : b.textContent || '').trim().toLowerCase();
                    if (rawText === wanted) {{
                        b.focus();
                        b.click();
                        return true;
                    }}
                }}
                return false;
            }}
            win.__wf.clickPage = clickSidebarPage;

            /* 1. Pin / Unpin rail with clear red active state + filled pin icon */
            function applyPinState() {{
                const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) return;
                const pinned = win.localStorage.getItem('wf_rail_pinned') === '1';
                sidebar.classList.toggle('wf-pinned', pinned);
                doc.body.classList.toggle('wf-rail-pinned', pinned);

                const pinBtn = doc.getElementById('wf-pin-rail');
                if (pinBtn) {{
                    pinBtn.classList.toggle('is-pinned', pinned);
                    pinBtn.setAttribute('aria-pressed', pinned ? 'true' : 'false');
                    pinBtn.title = pinned ? 'Pinned — click to unpin' : 'Pin rail open';
                    pinBtn.innerHTML = pinned ? PIN_FILLED : PIN_OUTLINE;
                    pinBtn.onclick = function(e) {{
                        e.preventDefault();
                        e.stopPropagation();
                        const next = !(win.localStorage.getItem('wf_rail_pinned') === '1');
                        win.localStorage.setItem('wf_rail_pinned', next ? '1' : '0');
                        applyPinState();
                    }};
                }}
            }}
            win.__wf.applyPinState = applyPinState;

            /* 2. Command Palette (Ctrl+K / Cmd+K) */
            function renderCmdList() {{
                const list = doc.getElementById('wf-cmd-list');
                if (!list) return;
                const st = win.__wf;
                list.innerHTML = '';
                if (!st.filtered.length) {{
                    const empty = doc.createElement('div');
                    empty.className = 'wf-cmd-hint';
                    empty.style.padding = '12px';
                    empty.textContent = 'No matching section';
                    list.appendChild(empty);
                    return;
                }}
                st.filtered.forEach(function(item, idx) {{
                    const btn = doc.createElement('button');
                    btn.type = 'button';
                    btn.className = 'wf-cmd-item' + (idx === st.selectedIdx ? ' is-selected' : '');
                    btn.setAttribute('role', 'option');
                    const isCurrent = item.label === st.active;
                    btn.innerHTML =
                        '<span>' + item.label + '</span>' +
                        '<span class="wf-cmd-hint">' + (isCurrent ? 'Current' : 'Enter ↵') + '</span>';
                    btn.onmousedown = function(e) {{
                        e.preventDefault();
                        closePalette();
                        win.__wf.clickPage(item.label);
                    }};
                    btn.onmouseenter = function() {{
                        st.selectedIdx = idx;
                        const all = list.querySelectorAll('.wf-cmd-item');
                        all.forEach(function(el, i) {{ el.classList.toggle('is-selected', i === idx); }});
                    }};
                    list.appendChild(btn);
                }});
            }}

            function openPalette() {{
                const overlay = doc.getElementById('wf-cmd-overlay');
                if (!overlay) return;
                const st = win.__wf;
                st.filtered = st.items.slice();
                st.selectedIdx = 0;
                overlay.classList.add('is-open');
                const input = doc.getElementById('wf-cmd-input');
                if (input) {{
                    input.value = '';
                    renderCmdList();
                    setTimeout(function() {{ input.focus(); }}, 15);
                }}
            }}

            function closePalette() {{
                const overlay = doc.getElementById('wf-cmd-overlay');
                if (overlay) overlay.classList.remove('is-open');
            }}

            win.__wf.openPalette = openPalette;
            win.__wf.closePalette = closePalette;

            function ensureCommandPalette() {{
                let overlay = doc.getElementById('wf-cmd-overlay');
                if (!overlay) {{
                    overlay = doc.createElement('div');
                    overlay.id = 'wf-cmd-overlay';
                    overlay.className = 'wf-cmd-overlay';
                    overlay.setAttribute('role', 'dialog');
                    overlay.setAttribute('aria-modal', 'true');
                    overlay.setAttribute('aria-label', 'Jump to section');
                    overlay.innerHTML =
                        '<div class="wf-cmd-dialog">' +
                        '  <div class="wf-cmd-input-wrap">' +
                        '    <input id="wf-cmd-input" class="wf-cmd-input" type="text" placeholder="Type a section name (e.g. Budgets, Goals)…" autocomplete="off" />' +
                        '    <span class="wf-kbd">Esc</span>' +
                        '  </div>' +
                        '  <div id="wf-cmd-list" class="wf-cmd-list" role="listbox"></div>' +
                        '</div>';
                    doc.body.appendChild(overlay);
                }}

                overlay.onclick = function(e) {{
                    if (e.target === overlay) win.__wf.closePalette();
                }};

                const input = doc.getElementById('wf-cmd-input');
                if (input) {{
                    input.oninput = function() {{
                        const st = win.__wf;
                        const q = input.value.trim().toLowerCase();
                        st.filtered = st.items.filter(function(i) {{
                            return i.label.toLowerCase().includes(q) || i.id.toLowerCase().includes(q);
                        }});
                        st.selectedIdx = 0;
                        renderCmdList();
                    }};
                    input.onkeydown = function(e) {{
                        const st = win.__wf;
                        if (e.key === 'Escape') {{
                            e.preventDefault();
                            win.__wf.closePalette();
                        }} else if (e.key === 'ArrowDown') {{
                            e.preventDefault();
                            if (st.filtered.length) {{
                                st.selectedIdx = (st.selectedIdx + 1) % st.filtered.length;
                                renderCmdList();
                            }}
                        }} else if (e.key === 'ArrowUp') {{
                            e.preventDefault();
                            if (st.filtered.length) {{
                                st.selectedIdx = (st.selectedIdx - 1 + st.filtered.length) % st.filtered.length;
                                renderCmdList();
                            }}
                        }} else if (e.key === 'Enter') {{
                            e.preventDefault();
                            const target = st.filtered[st.selectedIdx];
                            if (target) {{
                                win.__wf.closePalette();
                                win.__wf.clickPage(target.label);
                            }}
                        }}
                    }};
                }}

                const trigger = doc.getElementById('wf-cmd-open');
                if (trigger) {{
                    trigger.onclick = function(e) {{
                        e.preventDefault();
                        win.__wf.openPalette();
                    }};
                }}

                if (!win.__wfKeyHandler) {{
                    win.__wfKeyHandler = function(e) {{
                        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {{
                            e.preventDefault();
                            if (win.__wf && win.__wf.openPalette) win.__wf.openPalette();
                        }} else if (e.key === 'Escape') {{
                            if (win.__wf && win.__wf.closePalette) win.__wf.closePalette();
                        }}
                    }};
                    doc.addEventListener('keydown', win.__wfKeyHandler, true);
                }}
            }}

            /* 3. Mobile Bottom Navigation Bar */
            function ensureMobileBottomNav() {{
                const MOBILE_TABS = [
                    {{ label: 'Dashboard', short: 'Home', svg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>' }},
                    {{ label: 'Transactions', short: 'Ledger', svg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h10"/></svg>' }},
                    {{ label: 'Budgets', short: 'Budgets', svg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12A9 9 0 1 1 12 3"/><path d="M21 12h-9V3a9 9 0 0 1 9 9Z"/></svg>' }},
                    {{ label: 'Goals', short: 'Goals', svg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/></svg>' }},
                    {{ label: 'Assets', short: 'Assets', svg: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><path d="M17 7h4v4"/></svg>' }}
                ];

                let nav = doc.getElementById('wf-bottom-nav');
                if (!nav) {{
                    nav = doc.createElement('nav');
                    nav.id = 'wf-bottom-nav';
                    nav.className = 'wf-bottom-nav';
                    nav.setAttribute('aria-label', 'Primary navigation');
                    doc.body.appendChild(nav);
                }}

                nav.innerHTML = '';
                MOBILE_TABS.forEach(function(tab) {{
                    const btn = doc.createElement('button');
                    btn.type = 'button';
                    btn.className = 'wf-bottom-item' + (tab.label === win.__wf.active ? ' is-active' : '');
                    btn.setAttribute('aria-label', tab.label);
                    btn.innerHTML = tab.svg + '<span>' + tab.short + '</span>';
                    btn.onclick = function() {{
                        win.__wf.clickPage(tab.label);
                    }};
                    nav.appendChild(btn);
                }});
            }}

            /* 4. Strip any chevron arrow inside the profile avatar button & keep menu inside viewport */
            function fixProfilePopover() {{
                const popWrap = doc.querySelector('.st-key-tb_profile_pop');
                if (popWrap) {{
                    const btn = popWrap.querySelector('button');
                    if (btn) {{
                        const icons = btn.querySelectorAll('[data-testid="stIconMaterial"]');
                        icons.forEach(function(ic) {{
                            const txt = (ic.textContent || '').trim().toLowerCase();
                            if (txt !== 'person') {{
                                ic.style.display = 'none';
                                if (ic.parentElement && ic.parentElement !== btn && ic.parentElement.children.length === 1) {{
                                    ic.parentElement.style.display = 'none';
                                }}
                            }}
                        }});
                    }}
                }}
                const popHead = doc.querySelector('.wf-profile-head');
                if (popHead) {{
                    const layer = popHead.closest('[data-baseweb="popover"]');
                    if (layer) {{
                        layer.style.position = 'fixed';
                        layer.style.top = '52px';
                        layer.style.right = '20px';
                        layer.style.left = 'auto';
                        layer.style.transform = 'none';
                    }}
                }}
                /* Clamp any right-edge popover (e.g. delete confirmation) inside viewport */
                const vw = win.innerWidth || doc.documentElement.clientWidth || 1280;
                doc.querySelectorAll('[data-baseweb="popover"]').forEach(function(layer) {{
                    if (layer.querySelector('.wf-profile-head')) return;
                    if (!layer.querySelector('[data-testid="stPopoverBody"]')) return;
                    const rect = layer.getBoundingClientRect();
                    if (rect.width > 0 && rect.right > vw - 16) {{
                        const shift = Math.ceil(rect.right - (vw - 16));
                        if (shift > 1) {{
                            const curMargin = parseFloat(layer.style.marginLeft || '0') || 0;
                            layer.style.marginLeft = (curMargin - shift) + 'px';
                        }}
                    }}
                }});
            }}

            /* 5. Wire WealthFlow breadcrumb & sidebar brand to route directly to Dashboard */
            function bindHomeLinks() {{
                const crumb = doc.getElementById('wf-crumb-home');
                if (crumb) {{
                    crumb.onclick = function(e) {{
                        e.preventDefault();
                        win.__wf.clickPage('Dashboard');
                    }};
                }}
                const railHome = doc.getElementById('wf-rail-home');
                if (railHome) {{
                    railHome.onclick = function(e) {{
                        e.preventDefault();
                        win.__wf.clickPage('Dashboard');
                    }};
                }}
            }}

            if (!win.__wfPopObserver) {{
                win.__wfPopObserver = new MutationObserver(function() {{
                    fixProfilePopover();
                }});
                win.__wfPopObserver.observe(doc.body, {{ childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['aria-expanded', 'style'] }});
            }}

            applyPinState();
            ensureCommandPalette();
            ensureMobileBottomNav();
            fixProfilePopover();
            bindHomeLinks();
            setTimeout(function() {{
                applyPinState();
                ensureCommandPalette();
                fixProfilePopover();
                bindHomeLinks();
            }}, 200);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_sidebar(user_data, logo_b64, finance_service, auth_service, cookies):
    """
    Renders the Hallmark hover-expand navigation rail + sticky top bar (with interactive
    profile menu) + Ctrl+K palette.
    """
    nav_entries = list(NAV_ITEMS)
    if user_data.get("role") == "admin":
        nav_entries.append(("Admin", "User Management", ":material/group:"))

    current_page = st.session_state.get("page", "Dashboard")
    page_label_map = {pid: label for pid, label, _ in nav_entries}
    current_label = page_label_map.get(current_page, current_page)

    # 1. Sticky Top Bar inside main workspace (includes interactive RO Profile menu)
    render_topbar(user_data, current_label, finance_service, auth_service, cookies)

    # 2. Clean Hover-Expand Navigation Rail (destinations only — fits cleanly without scroll)
    with st.sidebar:
        logo_html = (
            f'<img class="wf-rail-logo" src="{logo_b64}" alt="WealthFlow">'
            if logo_b64
            else '<span class="wf-rail-logo-fallback">W</span>'
        )
        username = html.escape(str(user_data.get("username", "User")))
        role = html.escape(str(user_data.get("role", "member")).lower())

        st.markdown(
            f"""
            <div class="wf-rail-brand">
                <button type="button" id="wf-rail-home" class="wf-rail-brand-home" title="Go to Dashboard" aria-label="Go to WealthFlow Dashboard">
                    {logo_html}
                    <div class="wf-rail-text">
                        <div class="wf-rail-title">WealthFlow</div>
                        <div class="wf-rail-sub">{username} ({role})</div>
                    </div>
                </button>
                <button type="button" id="wf-pin-rail" class="wf-pin-btn wf-rail-text"
                        title="Pin rail open" aria-label="Pin navigation rail">
                    {_SVG_PIN_OUTLINE}
                </button>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Navigation items (crisp Material vector icons, dead-center in 72px rail)
        for p_id, p_label, p_icon in nav_entries:
            is_active = current_page == p_id
            if st.button(
                p_label,
                key=f"sb_nav_{p_id}",
                icon=p_icon,
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state["page"] = p_id
                for k in ["hist_year", "hist_month", "hist_day", "hist_type"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

    # 3. Interactive controller (pin rail, Ctrl+K palette, mobile bottom bar)
    _mount_shell_controller(nav_entries, current_label)
