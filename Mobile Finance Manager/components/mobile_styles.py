import streamlit as st


def apply_mobile_styles():
    """
    Hallmark v2.0.0 + ECC Mobile Design System for WealthFlow Mobile (iPhone Safari PWA).
    100% isolated from desktop styles.py.
    """
    st.markdown(
        """
        <style>
        /* hallmark: v2.0.0 | theme: obsidian-fintech-mobile | genre: modern-minimal | viewport: 375-430px */
        /* critique: mobile-first thumb dock, 16px non-zoom inputs, unified BaseWeb + React Aria pills */

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

        :root {
            --m-bg: #090D16;
            --m-surface-1: #111724;
            --m-surface-2: #182132;
            --m-surface-3: #212D42;
            --m-border: rgba(255, 255, 255, 0.08);
            --m-border-strong: rgba(255, 255, 255, 0.16);
            --m-ink-1: #F3F5F8;
            --m-ink-2: #9CA6B8;
            --m-ink-3: #69758B;
            --m-accent: #4F86F7;
            --m-accent-hover: #3B74EB;
            --m-accent-ink: #FFFFFF;
            --m-accent-low: rgba(79, 134, 247, 0.16);
            --m-accent-glow: rgba(79, 134, 247, 0.32);
            --m-success: #34D399;
            --m-success-low: rgba(52, 211, 153, 0.14);
            --m-success-mid: rgba(52, 211, 153, 0.34);
            --m-danger: #F87171;
            --m-danger-low: rgba(248, 113, 113, 0.14);
            --m-warning: #FBBF24;
            --m-warning-low: rgba(251, 191, 36, 0.14);
            --m-font-ui: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            --m-font-mono: 'JetBrains Mono', ui-monospace, 'SF Mono', monospace;
            --m-rad-hero: 16px;
            --m-rad-card: 12px;
            --m-rad-pill: 10px;
            --m-rad-full: 999px;
            --m-dur: 140ms;
            --m-ease: cubic-bezier(0.22, 1, 0.36, 1);
        }

        /* ============================================================
           1. CANVAS, SAFE AREAS & DESKTOP CHROME REMOVAL
        ============================================================ */
        html, body {
            background-color: var(--m-bg) !important;
            color: var(--m-ink-1) !important;
            font-family: var(--m-font-ui) !important;
            overflow-x: clip !important;
            -webkit-tap-highlight-color: transparent;
            -webkit-font-smoothing: antialiased;
        }

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .stApp {
            background-color: var(--m-bg) !important;
            color: var(--m-ink-1) !important;
            font-family: var(--m-font-ui) !important;
            overflow-x: clip !important;
        }

        /* Hide desktop Streamlit sidebar, header, footer, anchor links */
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        header[data-testid="stHeader"],
        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stHeaderActionElements"] {
            display: none !important;
        }

        /* Centered mobile app shell — flush top-left with zero wasted top gap */
        .block-container,
        [data-testid="stMainBlockContainer"],
        [data-testid="stAppViewBlockContainer"] {
            max-width: 460px !important;
            width: 100% !important;
            margin: 0 auto !important;
            padding: calc(2px + env(safe-area-inset-top, 0px)) 12px calc(98px + env(safe-area-inset-bottom, 0px)) 12px !important;
        }

        /* Collapse hidden utility blocks (<style>, 0px PWA bridge, Cookie/JS iframes) so top bar starts flush at top */
        [data-testid="stElementContainer"]:has(style),
        [data-testid="stElementContainer"]:has(iframe[height="0"]),
        [data-testid="stElementContainer"]:has(iframe[title*="streamlit_cookies_manager"]),
        [data-testid="stElementContainer"]:has(iframe[title*="streamlit_javascript"]) {
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Tighten vertical gaps between Streamlit blocks for crisp mobile rhythm */
        [data-testid="stVerticalBlock"] {
            gap: 0.6rem !important;
        }

        /* ============================================================
           2. TYPOGRAPHY & NUMERIC DISCIPLINE (Unified Global System Font)
        ============================================================ */
        html, body, .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        [data-testid="stElementContainer"],
        [data-testid="stSelectbox"] div:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]),
        [data-testid="stSelectbox"] span:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]),
        [data-baseweb="select"] div:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]),
        [data-baseweb="select"] span:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]),
        [data-baseweb="popover"] div:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]),
        [data-baseweb="menu"] div:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]),
        [data-baseweb="input"] input,
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]),
        .stMarkdown,
        .stMarkdown p,
        button:not([data-testid="stIconMaterial"]),
        button p,
        .stButton > button,
        .stButton > button p,
        input, select, textarea,
        p, label,
        .m-hero-card,
        .m-kpi-cell,
        .m-alert-row,
        .m-list-card {
            font-family: var(--m-font-ui) !important;
        }

        /* ============================================================
           CRITICAL: PRESERVE MATERIAL SYMBOLS & ICONS (Never render ligature text)
        ============================================================ */
        [data-testid="stIconMaterial"],
        [data-testid="stIconMaterial"] *,
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-icons,
        span.material-symbols-rounded,
        button [data-testid="stIconMaterial"],
        .stButton [data-testid="stIconMaterial"],
        [data-testid="stPopoverButton"] [data-testid="stIconMaterial"],
        [class*="st-key-"] [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
            font-weight: normal !important;
            font-style: normal !important;
            line-height: 1 !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            display: inline-block !important;
            white-space: nowrap !important;
            word-wrap: normal !important;
            direction: ltr !important;
            -webkit-font-feature-settings: 'liga' 1 !important;
            font-feature-settings: 'liga' 1 !important;
            -webkit-font-smoothing: antialiased !important;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: var(--m-font-ui) !important;
            color: var(--m-ink-1) !important;
            letter-spacing: -0.02em !important;
            overflow-wrap: break-word;
            min-width: 0;
        }

        p, li, .stMarkdown {
            color: var(--m-ink-2);
            font-family: var(--m-font-ui) !important;
            font-size: 14px;
            line-height: 1.45;
        }

        /* Monospace discipline for tabular numeric amounts */
        .m-mono, .m-mono *,
        .m-hero-val,
        .m-kpi-val,
        .m-alert-amt,
        .m-list-amt,
        code, pre {
            font-family: var(--m-font-mono) !important;
            font-variant-numeric: tabular-nums !important;
        }

        .m-sec-head {
            font-size: 15px;
            font-weight: 600;
            color: var(--m-ink-1);
            margin: 6px 0 2px 0;
            letter-spacing: -0.01em;
        }

        .m-sec-sub {
            font-size: 12px;
            color: var(--m-ink-3);
            margin-bottom: 4px;
        }

        label, [data-testid="stWidgetLabel"] p {
            font-family: var(--m-font-ui) !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            color: var(--m-ink-2) !important;
            letter-spacing: 0 !important;
            text-transform: none !important;
        }

        hr, [data-testid="stDivider"] {
            border-color: var(--m-border) !important;
            margin: 8px 0 !important;
        }

        /* ============================================================
           3. STICKY MOBILE TOP BAR (Flush Top-Left, Matching 40px Rounded Squares)
        ============================================================ */
        [data-testid="stHorizontalBlock"]:has(.wf-m-top-brand),
        [data-testid="stHorizontalBlock"]:has(.st-key-m_top_back) {
            position: sticky;
            top: 0;
            z-index: 60;
            background: rgba(9, 13, 22, 0.96);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border-bottom: 1px solid var(--m-border);
            padding: 6px 0 10px 0 !important;
            margin: 0 0 6px 0 !important;
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 8px !important;
        }

        [data-testid="stHorizontalBlock"]:has(.wf-m-top-brand) > [data-testid="stColumn"],
        [data-testid="stHorizontalBlock"]:has(.st-key-m_top_back) > [data-testid="stColumn"] {
            min-width: 0 !important;
            width: auto !important;
            display: flex !important;
            align-items: center !important;
            padding: 0 !important;
        }

        [data-testid="stHorizontalBlock"]:has(.wf-m-top-brand) > [data-testid="stColumn"]:first-child {
            flex: 1 1 0 !important;
            min-width: 0 !important;
            justify-content: flex-start !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_top_back) > [data-testid="stColumn"]:first-child {
            flex: 0 0 40px !important;
            width: 40px !important;
            max-width: 40px !important;
            min-width: 40px !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_top_back) > [data-testid="stColumn"]:nth-child(2) {
            flex: 1 1 0 !important;
            min-width: 0 !important;
            justify-content: flex-start !important;
        }
        [data-testid="stHorizontalBlock"]:has(.wf-m-top-brand) > [data-testid="stColumn"]:has(.st-key-m_top_curr_sel),
        [data-testid="stHorizontalBlock"]:has(.st-key-m_top_back) > [data-testid="stColumn"]:has(.st-key-m_top_curr_sel) {
            flex: 0 0 92px !important;
            width: 92px !important;
            max-width: 92px !important;
            min-width: 92px !important;
            justify-content: flex-end !important;
        }
        [data-testid="stHorizontalBlock"]:has(.wf-m-top-brand) > [data-testid="stColumn"]:has(.st-key-m_profile_pop),
        [data-testid="stHorizontalBlock"]:has(.st-key-m_top_back) > [data-testid="stColumn"]:has(.st-key-m_profile_pop) {
            flex: 0 0 40px !important;
            width: 40px !important;
            max-width: 40px !important;
            min-width: 40px !important;
            justify-content: flex-end !important;
        }

        [data-testid="stHorizontalBlock"]:has(.wf-m-top-brand) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"]:has(.st-key-m_top_back) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
            gap: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
        }

        [data-testid="stHorizontalBlock"]:has(.wf-m-top-brand) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
        [data-testid="stHorizontalBlock"]:has(.st-key-m_top_back) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
        }

        [data-testid="stHorizontalBlock"]:has(.wf-m-top-brand) [data-testid="stMarkdownContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }

        .wf-m-top-brand {
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;
            height: 40px;
        }

        .wf-m-top-logo {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            object-fit: contain;
            background: var(--m-surface-1);
            border: 1px solid var(--m-border-strong);
            padding: 3px;
            flex-shrink: 0;
        }

        .wf-m-top-title {
            font-size: 17px;
            font-weight: 700;
            color: var(--m-ink-1);
            letter-spacing: -0.02em;
            line-height: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Compact 92x40 rounded-square Currency dropdown matching 2026 / All / Calendar */
        .st-key-m_top_curr_sel,
        .st-key-m_top_curr_sel > div,
        .st-key-m_top_curr_sel [data-testid="stSelectbox"],
        .st-key-m_top_curr_sel [data-baseweb="select"] {
            width: 92px !important;
            max-width: 92px !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-m_top_curr_sel [data-baseweb="select"] > div {
            min-height: 40px !important;
            height: 40px !important;
            max-height: 40px !important;
            border-radius: var(--m-rad-card) !important;
            padding: 0 6px 0 8px !important;
            background-color: var(--m-surface-2) !important;
            border: 1px solid var(--m-border-strong) !important;
            align-items: center !important;
        }
        .st-key-m_top_curr_sel [data-baseweb="select"] > div > div:first-child {
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
        }
        .st-key-m_top_curr_sel [data-baseweb="select"] *,
        .st-key-m_top_curr_sel [data-baseweb="select"] div,
        .st-key-m_top_curr_sel [data-baseweb="select"] input {
            font-family: var(--m-font-ui) !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            line-height: 1.2 !important;
        }
        .st-key-m_top_curr_sel [data-baseweb="select"] svg {
            width: 16px !important;
            height: 16px !important;
            margin: 0 !important;
        }

        /* Period filter dropdowns: 2026 / All / Calendar (exact match to currency dropdown & profile button) */
        .st-key-m_dash_year,
        .st-key-m_dash_month,
        .st-key-m_dash_mode,
        .st-key-m_dash_year > div,
        .st-key-m_dash_month > div,
        .st-key-m_dash_mode > div,
        .st-key-m_dash_year [data-testid="stSelectbox"],
        .st-key-m_dash_month [data-testid="stSelectbox"],
        .st-key-m_dash_mode [data-testid="stSelectbox"],
        .st-key-m_dash_year [data-baseweb="select"],
        .st-key-m_dash_month [data-baseweb="select"],
        .st-key-m_dash_mode [data-baseweb="select"] {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
        }
        .st-key-m_dash_year [data-baseweb="select"] > div,
        .st-key-m_dash_month [data-baseweb="select"] > div,
        .st-key-m_dash_mode [data-baseweb="select"] > div {
            min-height: 40px !important;
            height: 40px !important;
            max-height: 40px !important;
            border-radius: var(--m-rad-card) !important;
            padding: 0 6px 0 10px !important;
            background-color: var(--m-surface-2) !important;
            border: 1px solid var(--m-border-strong) !important;
            align-items: center !important;
        }
        .st-key-m_dash_year [data-baseweb="select"] *,
        .st-key-m_dash_month [data-baseweb="select"] *,
        .st-key-m_dash_mode [data-baseweb="select"] * {
            font-family: var(--m-font-ui) !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            line-height: 1.2 !important;
            color: var(--m-ink-1) !important;
        }
        .st-key-m_dash_year [data-baseweb="select"] svg,
        .st-key-m_dash_month [data-baseweb="select"] svg,
        .st-key-m_dash_mode [data-baseweb="select"] svg {
            width: 16px !important;
            height: 16px !important;
            margin: 0 !important;
        }

        /* Top-right Profile Person Popover TRIGGER ONLY — exact 40x40 rounded square (never overrides closed popover hidden content) */
        .st-key-m_profile_pop {
            width: 40px !important;
            max-width: 40px !important;
            height: 40px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-m_profile_pop [data-testid="stPopoverButton"] {
            width: 40px !important;
            min-width: 40px !important;
            height: 40px !important;
            min-height: 40px !important;
            padding: 0 !important;
            margin: 0 !important;
            border-radius: var(--m-rad-card) !important;
            background-color: var(--m-surface-2) !important;
            border: 1px solid var(--m-border-strong) !important;
            color: var(--m-ink-1) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0 !important;
        }
        .st-key-m_profile_pop [data-testid="stPopoverButton"] > div {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .st-key-m_profile_pop [data-testid="stPopoverButton"] > div:nth-child(n+2),
        .st-key-m_profile_pop [data-testid="stPopoverButton"] > span,
        .st-key-m_profile_pop [data-testid="stPopoverButton"] svg,
        .st-key-m_profile_pop [data-testid="stPopoverButton"] [data-testid="stPopoverIcon"],
        .st-key-m_profile_pop [data-testid="stPopoverButton"] [data-testid="stMarkdownContainer"] {
            display: none !important;
        }
        .st-key-m_profile_pop [data-testid="stPopoverButton"] [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
            margin: 0 !important;
            font-size: 20px !important;
            line-height: 1 !important;
            display: inline-block !important;
        }
        .wf-m-profile-head {
            padding-bottom: 10px;
            margin-bottom: 10px;
            border-bottom: 1px solid var(--m-border);
        }
        .wf-m-profile-name { font-size: 15px; font-weight: 600; color: var(--m-ink-1); }
        .wf-m-profile-id { font-size: 12px; color: var(--m-ink-3); font-family: var(--m-font-mono); }

        /* ============================================================
           4. FIXED 5-TAB BOTTOM iOS DOCK (Mathematically Symmetrical 5-Col Grid)
        ============================================================ */
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) {
            position: fixed !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            bottom: 0 !important;
            width: 100% !important;
            max-width: 460px !important;
            z-index: 95 !important;
            background: rgba(17, 23, 36, 0.96) !important;
            backdrop-filter: blur(18px) !important;
            -webkit-backdrop-filter: blur(18px) !important;
            border-top: 1px solid var(--m-border-strong) !important;
            padding: 8px 10px calc(10px + env(safe-area-inset-bottom, 0px)) 10px !important;
            margin: 0 !important;
            display: grid !important;
            grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
            align-items: center !important;
            justify-items: center !important;
            gap: 6px !important;
        }

        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"],
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) .stButton {
            width: 100% !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            gap: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [data-testid="stColumn"]:not(:nth-child(3)) .stButton > button {
            height: 48px !important;
            min-height: 48px !important;
            width: 100% !important;
            max-width: 74px !important;
            padding: 4px 4px !important;
            margin: 0 auto !important;
            border-radius: 12px !important;
            background-color: transparent !important;
            border: 1px solid transparent !important;
            color: var(--m-ink-3) !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 2px !important;
            font-size: 11px !important;
            font-weight: 500 !important;
            box-shadow: none !important;
        }

        /* Stack Material icon cleanly ABOVE label text on outer 4 nav slots */
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [data-testid="stColumn"]:not(:nth-child(3)) .stButton > button > div,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [data-testid="stColumn"]:not(:nth-child(3)) .stButton > button > div > span {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 2px !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
        }

        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [data-testid="stColumn"]:not(:nth-child(3)) .stButton > button [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
            font-size: 20px !important;
            line-height: 1 !important;
            margin: 0 !important;
            display: inline-block !important;
        }

        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) .stButton > button [data-testid="stMarkdownContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }

        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) .stButton > button [data-testid="stMarkdownContainer"] p {
            font-size: 11px !important;
            line-height: 1.1 !important;
            margin: 0 !important;
            color: inherit !important;
            text-align: center !important;
        }

        /* Outer 4 nav slots styling */
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [data-testid="stColumn"]:not(:nth-child(3)) .stButton > button[kind="primary"] {
            background-color: var(--m-accent-low) !important;
            border-color: rgba(79, 134, 247, 0.34) !important;
            color: var(--m-accent) !important;
            font-weight: 600 !important;
        }

        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [data-testid="stColumn"]:not(:nth-child(3)) .stButton > button[kind="primary"] * {
            color: var(--m-accent) !important;
        }

        /* Center Column 3 (Slot 3) layout reset */
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3),
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3) > [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3) .stElementContainer,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3) .stButton {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Elevated Center + Quick-Add FAB — dead-center in slot 3 (50% axis) */
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [class*="st-key-m_dock_add"] button,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3) button {
            width: 50px !important;
            min-width: 50px !important;
            max-width: 50px !important;
            height: 50px !important;
            min-height: 50px !important;
            max-height: 50px !important;
            margin: -14px auto 0 auto !important;
            border-radius: 50% !important;
            background-color: var(--m-accent) !important;
            border: 2px solid var(--m-bg) !important;
            color: var(--m-accent-ink) !important;
            box-shadow: 0 6px 20px var(--m-accent-glow) !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            position: relative !important;
            overflow: hidden !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [class*="st-key-m_dock_add"] button > div,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [class*="st-key-m_dock_add"] button > div > span,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [class*="st-key-m_dock_add"] button span,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3) button > div,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3) button > div > span,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3) button span {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            height: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            text-align: center !important;
            line-height: 1 !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [class*="st-key-m_dock_add"] button [data-testid="stIconMaterial"],
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3) button [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
            color: var(--m-accent-ink) !important;
            font-size: 26px !important;
            width: 26px !important;
            height: 26px !important;
            line-height: 26px !important;
            margin: 0 auto !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) [class*="st-key-m_dock_add"] button *,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dock_home) > [data-testid="stColumn"]:nth-child(3) button * {
            color: var(--m-accent-ink) !important;
        }

        /* Hide zero-height marker divs from consuming vertical gap */
        [data-testid="stElementContainer"]:has(.wf-m-top-marker),
        [data-testid="stElementContainer"]:has(.wf-m-dock-marker) {
            margin: 0 !important;
            padding: 0 !important;
            height: 0 !important;
            min-height: 0 !important;
            overflow: hidden !important;
        }

        /* ============================================================
           5. MOBILE CARDS, HERO STRIP & COMPACT ALERT ROWS
        ============================================================ */
        .m-hero-card {
            background-color: var(--m-surface-1);
            border: 1px solid var(--m-border);
            border-radius: var(--m-rad-hero);
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .m-hero-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
        }

        .m-hero-label {
            font-size: 12px;
            font-weight: 500;
            color: var(--m-ink-2);
        }

        .m-hero-val {
            font-family: var(--m-font-mono);
            font-variant-numeric: tabular-nums;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.03em;
            line-height: 1.15;
            color: var(--m-ink-1);
            margin-top: 2px;
        }

        .m-flow-bar {
            height: 6px;
            border-radius: var(--m-rad-full);
            background-color: var(--m-surface-2);
            overflow: hidden;
            display: flex;
            gap: 2px;
        }
        .m-flow-in { background-color: var(--m-success); height: 100%; border-radius: var(--m-rad-full); }
        .m-flow-out { background-color: var(--m-danger); height: 100%; border-radius: var(--m-rad-full); }

        .m-kpi-grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
            gap: 12px 14px;
            border-top: 1px solid var(--m-border);
            padding-top: 12px;
        }

        .m-kpi-cell {
            display: flex;
            flex-direction: column;
            gap: 3px;
            min-width: 0;
        }

        .m-kpi-label {
            font-family: var(--m-font-ui) !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            color: var(--m-ink-2) !important;
            letter-spacing: -0.01em !important;
            line-height: 1.3 !important;
        }
        .m-kpi-val {
            font-family: var(--m-font-mono) !important;
            font-variant-numeric: tabular-nums !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            color: var(--m-ink-1) !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        .m-chip {
            display: inline-flex;
            align-items: center;
            width: fit-content;
            font-size: 11px;
            font-weight: 600;
            padding: 1px 7px;
            border-radius: var(--m-rad-full);
            line-height: 1.4;
        }
        .m-chip.positive { background: rgba(16, 185, 129, 0.16) !important; color: #10B981 !important; }
        .m-chip.danger, .m-chip.negative { background: rgba(239, 68, 68, 0.16) !important; color: #EF4444 !important; }
        .m-chip.warning { background: rgba(245, 158, 11, 0.16) !important; color: #F59E0B !important; }
        .m-chip.accent { background: var(--m-accent-low); color: #8AB4FF; }
        .m-chip.neutral { background: var(--m-surface-2); color: var(--m-ink-2); }

        /* Compact Alert Row */
        .m-alert-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            background-color: var(--m-surface-1);
            border: 1px solid var(--m-border);
            border-left: 3px solid var(--m-ink-3);
            border-radius: var(--m-rad-card);
            padding: 10px 12px;
            min-height: 50px;
        }
        .m-alert-row.tone-danger { border-left-color: #EF4444 !important; }
        .m-alert-row.tone-warning { border-left-color: #F59E0B !important; }
        .m-alert-row.tone-positive { border-left-color: #10B981 !important; }
        .m-alert-row.tone-accent { border-left-color: var(--m-accent); }

        /* Ensure all alert rows have identical left card and right button column widths */
        [data-testid="stHorizontalBlock"]:has([class*="st-key-m_alert_"]) {
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            width: 100% !important;
        }
        [data-testid="stHorizontalBlock"]:has([class*="st-key-m_alert_"]) > [data-testid="column"]:first-child {
            flex: 1 1 0px !important;
            min-width: 0 !important;
            width: auto !important;
        }
        [data-testid="stHorizontalBlock"]:has([class*="st-key-m_alert_"]) > [data-testid="column"]:last-child {
            flex: 0 0 84px !important;
            width: 84px !important;
            min-width: 84px !important;
            max-width: 84px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }

        /* Alert Action Pill Buttons (Uniform pill size, Centered, Green hover on Received, Red hover on Paid) */
        [class*="st-key-m_alert_"] {
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        [class*="st-key-m_alert_"] button,
        [class*="st-key-m_alert_"] .stButton > button,
        [class*="st-key-m_alert_"] [data-testid="stBaseButton-secondary"] {
            width: 80px !important;
            min-width: 80px !important;
            max-width: 80px !important;
            height: 32px !important;
            min-height: 32px !important;
            max-height: 32px !important;
            padding: 0 8px !important;
            border-radius: var(--m-rad-full) !important;
            background-color: var(--m-surface-2) !important;
            border: 1px solid var(--m-border-strong) !important;
            color: var(--m-ink-1) !important;
            font-family: var(--m-font-ui) !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            line-height: 1 !important;
            white-space: nowrap !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            margin: 0 auto !important;
            transition: all 0.15s ease !important;
        }
        [class*="st-key-m_alert_"] button [data-testid="stMarkdownContainer"] p,
        [class*="st-key-m_alert_"] button [data-testid="stMarkdownContainer"] span {
            font-family: var(--m-font-ui) !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            line-height: 1 !important;
            color: inherit !important;
            margin: 0 !important;
            padding: 0 !important;
            text-align: center !important;
        }
        /* Hover Green for Received */
        [class*="st-key-m_alert_receive_"] button:hover {
            background-color: rgba(16, 185, 129, 0.2) !important;
            border-color: #10B981 !important;
            color: #10B981 !important;
        }
        [class*="st-key-m_alert_receive_"] button:hover * {
            color: #10B981 !important;
        }
        /* Hover Red for Paid */
        [class*="st-key-m_alert_sub_"] button:hover,
        [class*="st-key-m_alert_emi_"] button:hover,
        [class*="st-key-m_alert_bill_"] button:hover,
        [class*="st-key-m_alert_paid_"] button:hover {
            background-color: rgba(239, 68, 68, 0.2) !important;
            border-color: #EF4444 !important;
            color: #EF4444 !important;
        }
        [class*="st-key-m_alert_sub_"] button:hover *,
        [class*="st-key-m_alert_emi_"] button:hover *,
        [class*="st-key-m_alert_bill_"] button:hover *,
        [class*="st-key-m_alert_paid_"] button:hover * {
            color: #EF4444 !important;
        }

        .m-alert-name {
            font-family: var(--m-font-ui) !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            color: var(--m-ink-1) !important;
            line-height: 1.3 !important;
        }
        .m-alert-meta {
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
            margin-top: 3px !important;
            font-family: var(--m-font-ui) !important;
            font-size: 11px !important;
            color: var(--m-ink-3) !important;
        }
        .m-alert-amt {
            font-family: var(--m-font-mono) !important;
            font-variant-numeric: tabular-nums !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            color: var(--m-ink-1) !important;
            white-space: nowrap !important;
        }



        /* Compact Ledger / List Card */
        .m-list-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            width: 100%;
            box-sizing: border-box;
            background-color: var(--m-surface-1);
            border: 1px solid var(--m-border);
            border-radius: var(--m-rad-card);
            padding: 11px 12px;
        }
        .m-list-left {
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1 1 0;
            min-width: 0;
            overflow: hidden;
        }
        .m-list-icon {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: var(--m-surface-2);
            display: grid;
            place-items: center;
            font-size: 16px;
            flex-shrink: 0;
        }
        .m-list-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--m-ink-1);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .m-list-sub {
            font-size: 12px;
            color: var(--m-ink-3);
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .m-list-right {
            display: flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
        }
        .m-cc-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(245, 158, 11, 0.18);
            border: 1px solid rgba(245, 158, 11, 0.45);
            color: #FBBF24;
            font-family: var(--m-font-ui) !important;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.04em;
            line-height: 1;
            padding: 3px 7px;
            border-radius: var(--m-rad-full);
            white-space: nowrap;
        }
        .m-list-amt {
            font-family: var(--m-font-mono);
            font-variant-numeric: tabular-nums;
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
            flex-shrink: 0;
        }

        .m-empty {
            background-color: var(--m-surface-1);
            border: 1px dashed var(--m-border-strong);
            border-radius: var(--m-rad-hero);
            padding: 24px 16px;
            text-align: center;
        }
        .m-empty-title { font-size: 15px; font-weight: 600; color: var(--m-ink-1); }
        .m-empty-sub { font-size: 13px; color: var(--m-ink-2); margin-top: 4px; }

        /* Pure CSS Breakdown Bars (Monzo / iOS Wallet style) */
        .m-breakdown-card {
            background-color: var(--m-surface-1);
            border: 1px solid var(--m-border);
            border-radius: var(--m-rad-hero);
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .m-breakdown-row {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .m-breakdown-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .m-breakdown-label {
            font-size: 13px;
            font-weight: 500;
            color: var(--m-ink-1);
        }
        .m-breakdown-meta {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .m-breakdown-amt {
            font-size: 13px;
            font-weight: 600;
            color: var(--m-ink-1);
            font-family: var(--m-font-mono);
        }
        .m-breakdown-track {
            width: 100%;
            height: 6px;
            background-color: var(--m-surface-2);
            border-radius: 999px;
            overflow: hidden;
        }
        .m-breakdown-fill {
            height: 100%;
            border-radius: 999px;
            transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        /* ============================================================
           6. UNIFIED TABS & SEGMENTED CONTROLS (BaseWeb + React Aria)
        ============================================================ */
        [data-testid="stTabs"] [role="tablist"],
        .stTabs [role="tablist"],
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            background-color: var(--m-surface-1) !important;
            border: 1px solid var(--m-border) !important;
            border-radius: var(--m-rad-card) !important;
            padding: 5px !important;
            gap: 6px !important;
            margin-bottom: 10px !important;
            overflow-x: auto !important;
            scrollbar-width: none !important;
            display: flex !important;
            align-items: center !important;
        }
        [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar { display: none; }

        [data-testid="stTabs"] [role="tab"],
        [data-testid="stTabs"] [data-testid="stTab"],
        [data-testid="stTabs"] button[role="tab"],
        .stTabs [role="tab"] {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 8px !important;
            padding: 0 12px !important;
            height: 36px !important;
            min-height: 36px !important;
            color: var(--m-ink-2) !important;
            font-family: var(--m-font-ui) !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            border: 1px solid var(--m-border-strong) !important;
            background-color: var(--m-surface-2) !important;
            white-space: nowrap !important;
            flex-shrink: 0 !important;
            cursor: pointer !important;
            transition: background-color var(--m-dur) var(--m-ease), border-color var(--m-dur) var(--m-ease), color var(--m-dur) var(--m-ease) !important;
        }

        [data-testid="stTabs"] [role="tab"] p,
        [data-testid="stTabs"] [data-testid="stTab"] p {
            color: inherit !important;
            font-size: 13px !important;
            margin: 0 !important;
            white-space: nowrap !important;
        }

        [data-testid="stTabs"] [role="tab"][aria-selected="true"],
        [data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"],
        [data-testid="stTabs"] [role="tab"][data-selected="true"] {
            background-color: var(--m-accent) !important;
            border-color: var(--m-accent) !important;
            color: var(--m-accent-ink) !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 10px var(--m-accent-glow) !important;
        }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
        [data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] * {
            color: var(--m-accent-ink) !important;
        }

        [data-testid="stTabs"] [data-baseweb="tab-highlight"],
        [data-testid="stTabs"] [data-baseweb="tab-border"],
        [data-testid="stTabs"] .react-aria-SelectionIndicator,
        [data-testid="stTabs"] [role="tablist"]::after {
            display: none !important;
        }

        /* Segmented controls & button groups */
        [data-testid="stSegmentedControl"] [role="radiogroup"],
        [data-testid="stButtonGroup"] > div,
        [data-baseweb="button-group"],
        .stButtonGroup > div {
            background-color: var(--m-surface-1) !important;
            border: 1px solid var(--m-border) !important;
            border-radius: var(--m-rad-card) !important;
            padding: 5px !important;
            gap: 6px !important;
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            scrollbar-width: none !important;
        }
        [data-testid="stSegmentedControl"] button,
        [data-testid="stButtonGroup"] button,
        [data-baseweb="button-group"] button,
        .stButtonGroup button {
            border-radius: 8px !important;
            border: 1px solid var(--m-border-strong) !important;
            background-color: var(--m-surface-2) !important;
            color: var(--m-ink-2) !important;
            height: 36px !important;
            padding: 0 12px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
            flex-shrink: 0 !important;
            transition: all 0.15s ease !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="true"],
        [data-testid="stSegmentedControl"] button[aria-selected="true"],
        [data-testid="stSegmentedControl"] button[data-selected="true"],
        [data-testid="stButtonGroup"] button[aria-checked="true"],
        [data-testid="stButtonGroup"] button[aria-pressed="true"],
        [data-testid="stButtonGroup"] button[aria-selected="true"],
        [data-testid="stButtonGroup"] button[data-selected="true"],
        [data-testid="stButtonGroup"] button[data-active="true"],
        [data-testid="stButtonGroup"] button[data-testid*="Active"],
        [data-testid="stButtonGroup"] button[kind*="Active"],
        [data-baseweb="button-group"] button[aria-checked="true"],
        [data-baseweb="button-group"] button[aria-pressed="true"],
        [data-baseweb="button-group"] button[aria-selected="true"],
        [data-baseweb="button-group"] button[data-selected="true"],
        [data-baseweb="button-group"] button[kind*="Active"],
        [data-baseweb="button-group"] button[data-testid*="Active"],
        .stButtonGroup button[aria-checked="true"],
        .stButtonGroup button[aria-selected="true"],
        .stButtonGroup button[data-selected="true"],
        .stButtonGroup button[data-testid*="Active"] {
            background-color: var(--m-accent) !important;
            border-color: var(--m-accent) !important;
            color: var(--m-accent-ink) !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 10px var(--m-accent-glow) !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="true"] *,
        [data-testid="stSegmentedControl"] button[aria-selected="true"] *,
        [data-testid="stSegmentedControl"] button[data-selected="true"] *,
        [data-testid="stButtonGroup"] button[aria-checked="true"] *,
        [data-testid="stButtonGroup"] button[aria-pressed="true"] *,
        [data-testid="stButtonGroup"] button[aria-selected="true"] *,
        [data-testid="stButtonGroup"] button[data-selected="true"] *,
        [data-testid="stButtonGroup"] button[data-active="true"] *,
        [data-testid="stButtonGroup"] button[data-testid*="Active"] *,
        [data-testid="stButtonGroup"] button[kind*="Active"] *,
        [data-baseweb="button-group"] button[aria-checked="true"] *,
        [data-baseweb="button-group"] button[aria-pressed="true"] *,
        [data-baseweb="button-group"] button[aria-selected="true"] *,
        [data-baseweb="button-group"] button[data-selected="true"] *,
        [data-baseweb="button-group"] button[kind*="Active"] *,
        [data-baseweb="button-group"] button[data-testid*="Active"] *,
        .stButtonGroup button[aria-checked="true"] *,
        .stButtonGroup button[aria-selected="true"] *,
        .stButtonGroup button[data-selected="true"] *,
        .stButtonGroup button[data-testid*="Active"] * {
            color: var(--m-accent-ink) !important;
        }

        /* Quick Add 3-pill mode switcher (Expense / Income / Trip Expense) — deterministic primary highlight */
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            background-color: var(--m-surface-1) !important;
            border: 1px solid var(--m-border) !important;
            border-radius: var(--m-rad-card) !important;
            padding: 5px !important;
            gap: 6px !important;
            margin: 0 0 6px 0 !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) > [data-testid="stColumn"] {
            flex: 1 1 auto !important;
            min-width: 0 !important;
            width: auto !important;
            padding: 0 !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) > [data-testid="stColumn"]:nth-child(1) { flex: 1 1 0 !important; }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) > [data-testid="stColumn"]:nth-child(2) { flex: 0.9 1 0 !important; }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) > [data-testid="stColumn"]:nth-child(3) { flex: 1.3 1 0 !important; }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) .stElementContainer,
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) .stButton {
            margin: 0 !important;
            padding: 0 !important;
            gap: 0 !important;
            width: 100% !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) .stButton > button {
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
            padding: 0 10px !important;
            border-radius: 8px !important;
            background-color: var(--m-surface-2) !important;
            border: 1px solid var(--m-border-strong) !important;
            color: var(--m-ink-2) !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
            box-shadow: none !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) .stButton > button[kind="primary"] {
            background-color: var(--m-accent) !important;
            border-color: var(--m-accent) !important;
            color: var(--m-accent-ink) !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 10px var(--m-accent-glow) !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_qa_tab_exp) .stButton > button[kind="primary"] * {
            color: var(--m-accent-ink) !important;
        }

        /* ============================================================
           7. FORMS, 16px NON-ZOOM INPUTS & 44px TOUCH BUTTONS
        ============================================================ */
        [data-testid="stForm"],
        .st-key-m_qa_exp_card,
        .st-key-m_sp_card {
            background-color: var(--m-surface-1) !important;
            border: 1px solid var(--m-border) !important;
            border-radius: var(--m-rad-hero) !important;
            padding: 14px !important;
        }

        /* Floating Round QR Scanner FAB (Right-Side Overlay above Dock) */
        [data-testid="stElementContainer"]:has(.st-key-m_qr_fab_btn) {
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
        }
        .st-key-m_qr_fab_btn {
            position: fixed !important;
            right: max(16px, calc(50vw - 214px)) !important;
            bottom: calc(82px + env(safe-area-inset-bottom, 0px)) !important;
            z-index: 98 !important;
            width: 52px !important;
            height: 52px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-m_qr_fab_btn button {
            width: 52px !important;
            min-width: 52px !important;
            max-width: 52px !important;
            height: 52px !important;
            min-height: 52px !important;
            max-height: 52px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #4F86F7 0%, #3B74EB 100%) !important;
            border: 2px solid var(--m-bg) !important;
            color: var(--m-accent-ink) !important;
            box-shadow: 0 8px 24px rgba(79, 134, 247, 0.45), 0 2px 8px rgba(0, 0, 0, 0.4) !important;
            padding: 0 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .st-key-m_qr_fab_btn button > div,
        .st-key-m_qr_fab_btn button > div > span,
        .st-key-m_qr_fab_btn button span {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            height: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-m_qr_fab_btn button [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
            color: var(--m-accent-ink) !important;
            font-size: 24px !important;
            width: 24px !important;
            height: 24px !important;
            line-height: 24px !important;
            margin: 0 !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .st-key-m_qr_fab_btn button * {
            color: var(--m-accent-ink) !important;
        }

        input, select, textarea,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="select"] > div {
            font-size: 16px !important; /* Prevents iOS Safari focus auto-zoom */
            font-family: var(--m-font-ui) !important;
            color: var(--m-ink-1) !important;
        }

        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div,
        [data-baseweb="textarea"] > div {
            background-color: var(--m-surface-2) !important;
            border: 1px solid var(--m-border-strong) !important;
            border-radius: var(--m-rad-card) !important;
            min-height: 44px !important;
        }

        input::placeholder, textarea::placeholder {
            color: var(--m-ink-3) !important;
        }

        .stButton > button,
        [data-testid="stFormSubmitButton"] > button {
            min-height: 44px !important;
            height: 44px !important;
            border-radius: var(--m-rad-card) !important;
            background-color: var(--m-surface-2) !important;
            border: 1px solid var(--m-border-strong) !important;
            color: var(--m-ink-1) !important;
            font-family: var(--m-font-ui) !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
            transition: background-color var(--m-dur) var(--m-ease), transform 90ms var(--m-ease) !important;
        }
        .stButton > button [data-testid="stMarkdownContainer"] p,
        [data-testid="stFormSubmitButton"] > button [data-testid="stMarkdownContainer"] p {
            white-space: nowrap !important;
            margin: 0 !important;
        }

        .stButton > button[kind="primary"],
        [data-testid="stFormSubmitButton"] > button {
            background-color: var(--m-accent) !important;
            border-color: var(--m-accent) !important;
            color: var(--m-accent-ink) !important;
            font-weight: 600 !important;
        }
        .stButton > button[kind="primary"] *,
        [data-testid="stFormSubmitButton"] > button * {
            color: var(--m-accent-ink) !important;
        }

        .stButton > button:focus-visible,
        [data-testid="stFormSubmitButton"] > button:focus-visible {
            outline: 2px solid var(--m-accent) !important;
            outline-offset: 2px !important;
        }

        /* More Hub Tile Buttons */
        [class*="st-key-m_hub_"] button {
            height: 76px !important;
            min-height: 76px !important;
            border-radius: 14px !important;
            background-color: var(--m-surface-1) !important;
            border: 1px solid var(--m-border) !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            justify-content: flex-start !important;
            padding: 0 14px !important;
            transition: all var(--m-dur) var(--m-ease) !important;
        }
        [class*="st-key-m_hub_"] button:hover,
        [class*="st-key-m_hub_"] button:active,
        [class*="st-key-m_hub_"] button:focus {
            background-color: var(--m-surface-2) !important;
            border-color: var(--m-accent) !important;
            color: var(--m-accent) !important;
            box-shadow: 0 0 0 1px var(--m-accent), 0 2px 10px var(--m-accent-glow) !important;
        }
        [class*="st-key-m_hub_"] button:hover *,
        [class*="st-key-m_hub_"] button:active *,
        [class*="st-key-m_hub_"] button:focus * {
            color: var(--m-accent) !important;
        }

        /* Popovers & Delete Confirmation */
        [data-testid="stPopover"] > div > button {
            min-height: 40px !important;
            height: 40px !important;
            border-radius: 10px !important;
            background-color: var(--m-surface-2) !important;
            border: 1px solid var(--m-border-strong) !important;
            color: var(--m-ink-1) !important;
        }
        [data-testid="stPopoverBody"] {
            background-color: var(--m-surface-1) !important;
            border: 1px solid var(--m-border-strong) !important;
            border-radius: 14px !important;
            width: 260px !important;
            min-width: 240px !important;
            max-width: calc(100vw - 24px) !important;
        }
        .wf-m-del-msg {
            background: var(--m-warning-low);
            border: 1px solid rgba(251, 191, 36, 0.3);
            border-radius: 10px;
            padding: 9px 11px;
            margin-bottom: 10px;
            font-size: 13px;
            color: var(--m-ink-1);
            word-break: break-word;
        }

        /* Keep inline mobile action & filter rows strictly horizontal even on 375px phones */
        [data-testid="stHorizontalBlock"]:has(.m-alert-row),
        [data-testid="stHorizontalBlock"]:has(.m-list-card),
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dash_year),
        [data-testid="stHorizontalBlock"]:has(.st-key-m_trip_picker),
        [data-testid="stHorizontalBlock"]:has([class*="st-key-m_tsync_"]),
        [data-testid="stHorizontalBlock"]:has([class*="st-key-m_gadd_"]) {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 8px !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_dash_year) > [data-testid="stColumn"],
        [data-testid="stHorizontalBlock"]:has([class*="st-key-m_tsync_"]) > [data-testid="stColumn"] {
            flex: 1 1 0 !important;
            min-width: 0 !important;
            width: auto !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_trip_picker) > [data-testid="stColumn"]:first-child,
        [data-testid="stHorizontalBlock"]:has([class*="st-key-m_gadd_"]) > [data-testid="stColumn"]:first-child {
            flex: 1 1 auto !important;
            min-width: 0 !important;
            width: auto !important;
        }
        [data-testid="stHorizontalBlock"]:has(.st-key-m_trip_picker) > [data-testid="stColumn"]:last-child,
        [data-testid="stHorizontalBlock"]:has([class*="st-key-m_gadd_"]) > [data-testid="stColumn"]:last-child {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }
        [data-testid="stHorizontalBlock"]:has(.m-alert-row) > [data-testid="stColumn"]:first-child,
        [data-testid="stHorizontalBlock"]:has(.m-list-card) > [data-testid="stColumn"]:first-child {
            flex: 1 1 0px !important;
            min-width: 0 !important;
            width: auto !important;
        }
        [data-testid="stHorizontalBlock"]:has(.m-alert-row) > [data-testid="stColumn"]:not(:first-child),
        [data-testid="stHorizontalBlock"]:has(.m-list-card) > [data-testid="stColumn"]:not(:first-child) {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }
        .m-qr-chip {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            background: rgba(52, 211, 153, 0.10);
            border: 1px solid rgba(52, 211, 153, 0.34);
            border-radius: var(--m-rad-card);
            padding: 9px 12px;
        }
        .m-qr-chip-name {
            font-size: 13px;
            font-weight: 600;
            color: var(--m-success);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .m-qr-chip-vpa {
            font-size: 11px;
            color: var(--m-ink-2);
            font-family: var(--m-font-mono);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Floating Mobile Toast (clears top bar & Dynamic Island) */
        [data-testid="stToastContainer"] {
            top: calc(58px + env(safe-area-inset-top, 0px)) !important;
            right: 12px !important;
            left: 12px !important;
            bottom: auto !important;
            z-index: 120 !important;
        }
        [data-testid="stToast"] {
            background-color: var(--m-surface-1) !important;
            border: 1px solid var(--m-success-mid) !important;
            border-left: 3px solid var(--m-success) !important;
            border-radius: 12px !important;
            color: var(--m-ink-1) !important;
        }

        /* Progress bars & Expanders */
        [data-testid="stExpander"] {
            background-color: var(--m-surface-1) !important;
            border: 1px solid var(--m-border) !important;
            border-radius: var(--m-rad-card) !important;
        }
        .stProgress > div > div > div {
            background-color: var(--m-surface-2) !important;
            border-radius: var(--m-rad-full) !important;
            height: 7px !important;
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                transition-duration: 0.01ms !important;
                animation-duration: 0.01ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
