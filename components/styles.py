import streamlit as st

def apply_styles():
    """
    Hallmark · app · genre: modern-minimal · theme: slate-steel · v2.0.0
    critique: clean token system, one blue accent, density-first app shell
    waive: 44b (app screen, no hero fold rule applies per flow.md § App screens)
    waive: 58 (app screen, no word budget per flow.md § App screens)
    """
    st.markdown("""
        <style>
        /* Hallmark · app · genre: modern-minimal · theme: slate-steel · v2.0.0 */
        /* critique: density-first financial tool, one accent, full token system */

        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

        /* ============================================================
           TOKEN BLOCK — all colour, type, radius, space, motion here
           No literal value may appear past this block.
        ============================================================ */
        :root {
            /* Palette — OKLCH */
            --color-paper:        oklch(13% 0.012 240);   /* deep slate */
            --color-paper-2:      oklch(17% 0.012 240);   /* raised panel */
            --color-paper-3:      oklch(21% 0.011 240);   /* well / input bg */
            --color-paper-4:      oklch(25% 0.010 240);   /* hover surface */
            --color-ink:          oklch(94% 0.005 240);   /* primary text */
            --color-ink-2:        oklch(72% 0.008 240);   /* secondary text */
            --color-ink-3:        oklch(52% 0.008 240);   /* muted / disabled */
            --color-rule:         oklch(100% 0 0 / 0.07); /* hairline */
            --color-accent:       oklch(63% 0.18 258);    /* blue signal */
            --color-accent-ink:   oklch(94% 0.005 240);   /* text on accent */
            --color-accent-low:   oklch(63% 0.18 258 / 0.12); /* tinted accent bg */
            --color-accent-mid:   oklch(63% 0.18 258 / 0.25);
            --color-focus:        oklch(70% 0.20 258);    /* focus ring */
            --color-success:      oklch(65% 0.14 150);
            --color-warning:      oklch(78% 0.14  85);
            --color-danger:       oklch(63% 0.18  25);
            --color-shadow:       oklch(5% 0.01 240 / 0.4);

            /* Typography */
            --font-body:   'Outfit', system-ui, sans-serif;
            --text-xs:     0.75rem;   /* 12px */
            --text-sm:     0.8125rem; /* 13px */
            --text-base:   1rem;      /* 16px */
            --text-md:     1.125rem;  /* 18px */
            --text-lg:     1.25rem;   /* 20px */
            --text-xl:     1.5rem;    /* 24px */
            --text-2xl:    1.875rem;  /* 30px */
            --text-3xl:    2.25rem;   /* 36px */

            /* Spacing scale */
            --space-3xs:  0.125rem;  /* 2px  */
            --space-2xs:  0.25rem;   /* 4px  */
            --space-xs:   0.5rem;    /* 8px  */
            --space-sm:   0.75rem;   /* 12px */
            --space-md:   1rem;      /* 16px */
            --space-lg:   1.5rem;    /* 24px */
            --space-xl:   2.5rem;    /* 40px */
            --space-2xl:  4rem;      /* 64px */

            /* Radii — one per nesting level */
            --radius-sm:    6px;
            --radius-md:    10px;
            --radius-lg:    14px;
            --radius-xl:    20px;
            --radius-full:  9999px;

            /* Motion */
            --dur-micro:  120ms;
            --dur-short:  220ms;
            --dur-long:   420ms;
            --ease-out:   cubic-bezier(0.16, 1, 0.3, 1);
            --ease-in:    cubic-bezier(0.4, 0, 1, 1);
            --ease-io:    cubic-bezier(0.4, 0, 0.2, 1);

            /* Surfaces */
            --shadow-raised: 0 1px 3px var(--color-shadow);
            --shadow-card:   0 0 0 1px var(--color-rule);
        }

        /* ============================================================
           RESET & BASE
        ============================================================ */
        html, body {
            overflow-x: clip;
        }

        html, body, [data-testid="stAppViewContainer"],
        [data-testid="stMain"], .main {
            font-family: var(--font-body) !important;
            background-color: var(--color-paper) !important;
            color: var(--color-ink) !important;
            font-size: var(--text-base);
            line-height: 1.55;
        }

        /* Smooth scroll — passive, no script needed */
        * { scroll-behavior: smooth; }

        /* ============================================================
           MAIN CONTAINER
        ============================================================ */
        .main .block-container {
            padding: var(--space-lg) var(--space-md) !important;
            max-width: 100% !important;
            overflow-x: clip;
        }

        /* ============================================================
           TYPOGRAPHY
        ============================================================ */
        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-body) !important;
            font-weight: 700 !important;
            color: var(--color-ink) !important;
            overflow-wrap: break-word;
            min-width: 0;
            text-wrap: balance;
            line-height: 1.2;
            letter-spacing: -0.02em;
        }

        h1 { font-size: var(--text-2xl) !important; }
        h2 { font-size: var(--text-xl) !important; }
        h3 { font-size: var(--text-lg) !important; font-weight: 600 !important; color: var(--color-ink-2) !important; }
        h4 { font-size: var(--text-md) !important; font-weight: 600 !important; }

        p, li, label, .stMarkdown {
            color: var(--color-ink-2);
            font-size: var(--text-base);
            line-height: 1.6;
        }

        /* Labels — sentence case, body face, one step smaller, untracked */
        label, .stSelectbox label, .stTextInput label,
        .stNumberInput label, .stDateInput label,
        .stTextArea label, .stMultiSelect label {
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            color: var(--color-ink-2) !important;
            letter-spacing: 0 !important;
            text-transform: none !important;
        }

        /* Section headers — left-accented, clean */
        .main-header {
            font-size: var(--text-2xl) !important;
            font-weight: 700 !important;
            color: var(--color-ink) !important;
            letter-spacing: -0.025em;
            margin-bottom: var(--space-lg) !important;
            line-height: 1.1;
        }

        h3, .section-header {
            font-weight: 600 !important;
            color: var(--color-ink-2) !important;
            border-left: 3px solid var(--color-accent);
            padding-left: var(--space-xs);
            margin-top: var(--space-lg) !important;
            letter-spacing: 0;
            text-transform: none;
        }

        /* ============================================================
           METRIC CARDS
        ============================================================ */
        div[data-testid="metric-container"] {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            border-radius: var(--radius-lg) !important;
            padding: var(--space-md) var(--space-lg) !important;
            box-shadow: var(--shadow-raised) !important;
            transition:
                border-color var(--dur-short) var(--ease-out),
                transform var(--dur-short) var(--ease-out) !important;
        }

        div[data-testid="metric-container"]:hover {
            border-color: var(--color-accent-mid) !important;
            transform: translateY(-2px);
        }

        [data-testid="stMetricValue"] {
            font-size: var(--text-xl) !important;
            font-weight: 700 !important;
            color: var(--color-ink) !important;
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.02em;
        }

        [data-testid="stMetricLabel"] {
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            color: var(--color-ink-2) !important;
            letter-spacing: 0 !important;
        }

        [data-testid="stMetricDelta"] {
            font-size: var(--text-xs) !important;
            font-weight: 600 !important;
            font-variant-numeric: tabular-nums;
        }

        /* ============================================================
           EXPANDERS
        ============================================================ */
        [data-testid="stExpander"] {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            border-radius: var(--radius-lg) !important;
            overflow: hidden;
            box-shadow: var(--shadow-raised) !important;
        }

        [data-testid="stExpander"] > details > summary {
            font-size: var(--text-md) !important;
            font-weight: 600 !important;
            color: var(--color-ink) !important;
            padding: var(--space-md) var(--space-lg) !important;
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
            transition: background-color var(--dur-micro) var(--ease-out);
        }

        [data-testid="stExpander"] > details > summary:hover {
            background-color: var(--color-paper-3);
        }

        [data-testid="stExpander"] > details > summary:focus-visible {
            outline: 2px solid var(--color-focus);
            outline-offset: -2px;
        }

        [data-testid="stExpander"] > details[open] > summary {
            border-bottom: 1px solid var(--color-rule);
        }

        /* ============================================================
           FORM CONTROLS
        ============================================================ */
        input, select, textarea,
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div,
        [data-baseweb="textarea"] > div {
            background-color: var(--color-paper-3) !important;
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--color-rule) !important;
            color: var(--color-ink) !important;
            font-family: var(--font-body) !important;
            font-size: var(--text-base) !important;
            transition:
                border-color var(--dur-micro) var(--ease-out),
                box-shadow var(--dur-micro) var(--ease-out) !important;
        }

        input:focus, select:focus, textarea:focus,
        [data-baseweb="select"]:focus-within > div,
        [data-baseweb="input"]:focus-within > div {
            border-color: var(--color-accent) !important;
            box-shadow: 0 0 0 3px var(--color-accent-low) !important;
            outline: none !important;
        }

        input:focus-visible, select:focus-visible, textarea:focus-visible,
        [data-baseweb="select"] *:focus-visible,
        [data-baseweb="input"] *:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: 2px !important;
        }

        /* Date input */
        [data-testid="stDateInput"] input {
            background-color: var(--color-paper-3) !important;
        }

        /* Select dropdown menu */
        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="menu"] {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            border-radius: var(--radius-md) !important;
            box-shadow: 0 8px 24px var(--color-shadow) !important;
        }

        [data-baseweb="option"]:hover,
        [data-baseweb="option"][aria-selected="true"] {
            background-color: var(--color-accent-low) !important;
            color: var(--color-ink) !important;
        }

        /* Number input arrows */
        [data-testid="stNumberInput"] button {
            background-color: var(--color-paper-3) !important;
            border-color: var(--color-rule) !important;
            color: var(--color-ink-2) !important;
            border-radius: var(--radius-sm) !important;
        }

        [data-testid="stNumberInput"] button:hover {
            background-color: var(--color-paper-4) !important;
        }

        [data-testid="stNumberInput"] button:focus-visible {
            outline: 2px solid var(--color-focus) !important;
        }

        /* ============================================================
           BUTTONS
        ============================================================ */
        .stButton > button {
            background-color: var(--color-accent) !important;
            color: var(--color-accent-ink) !important;
            border: none !important;
            border-radius: var(--radius-md) !important;
            padding: var(--space-xs) var(--space-md) !important;
            font-family: var(--font-body) !important;
            font-size: var(--text-sm) !important;
            font-weight: 600 !important;
            letter-spacing: 0 !important;
            height: 36px;
            min-height: 36px;
            box-shadow: none !important;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                transform var(--dur-micro) var(--ease-out),
                box-shadow var(--dur-micro) var(--ease-out) !important;
            width: 100% !important;
        }

        .stButton > button:hover {
            background-color: oklch(68% 0.18 258) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px oklch(63% 0.18 258 / 0.3) !important;
        }

        .stButton > button:active {
            transform: translateY(0) !important;
            background-color: oklch(58% 0.18 258) !important;
        }

        .stButton > button:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: 2px !important;
        }

        .stButton > button:disabled {
            background-color: var(--color-paper-3) !important;
            color: var(--color-ink-3) !important;
            cursor: not-allowed;
            transform: none !important;
        }

        /* Secondary / ghost buttons — delete, cancel, etc. */
        .stButton > button[kind="secondary"],
        [data-testid="stFormSubmitButton"] > button[kind="secondary"] {
            background-color: transparent !important;
            border: 1px solid var(--color-rule) !important;
            color: var(--color-ink-2) !important;
        }

        .stButton > button[kind="secondary"]:hover {
            background-color: var(--color-paper-3) !important;
            border-color: var(--color-accent-mid) !important;
            color: var(--color-ink) !important;
            box-shadow: none !important;
        }

        /* Form submit buttons */
        [data-testid="stFormSubmitButton"] > button {
            background-color: var(--color-accent) !important;
            color: var(--color-accent-ink) !important;
            border-radius: var(--radius-md) !important;
            font-weight: 600 !important;
            font-size: var(--text-sm) !important;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                transform var(--dur-micro) var(--ease-out) !important;
        }

        [data-testid="stFormSubmitButton"] > button:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: 2px !important;
        }

        /* ============================================================
           POPOVER
        ============================================================ */
        [data-testid="stPopover"] > div > button {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            color: var(--color-ink) !important;
            border-radius: var(--radius-md) !important;
            font-size: var(--text-sm) !important;
            padding: var(--space-xs) var(--space-md) !important;
            transition: background-color var(--dur-micro) var(--ease-out) !important;
        }

        [data-testid="stPopover"] > div > button:hover {
            background-color: var(--color-paper-3) !important;
        }

        [data-testid="stPopover"] > div > button:focus-visible {
            outline: 2px solid var(--color-focus) !important;
        }

        /* ============================================================
           PROGRESS BAR
        ============================================================ */
        .stProgress > div > div > div > div {
            background-color: var(--color-accent) !important;
            border-radius: var(--radius-full) !important;
        }

        .stProgress > div > div > div {
            background-color: var(--color-paper-3) !important;
            border-radius: var(--radius-full) !important;
        }

        /* ============================================================
           DATAFRAMES / TABLES
        ============================================================ */
        [data-testid="stDataFrame"],
        [data-testid="stDataFrameGlideDataEditor"] {
            border-radius: var(--radius-lg) !important;
            overflow: hidden;
            border: 1px solid var(--color-rule) !important;
        }

        /* ============================================================
           ALERTS & NOTIFICATIONS
        ============================================================ */
        [data-testid="stAlert"] {
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--color-rule) !important;
            font-size: var(--text-sm) !important;
        }

        .stSuccess { border-left: 3px solid var(--color-success) !important; }
        .stWarning { border-left: 3px solid var(--color-warning) !important; }
        .stError   { border-left: 3px solid var(--color-danger) !important; }
        .stInfo    { border-left: 3px solid var(--color-accent) !important; }

        /* ============================================================
           PLOTLY CHARTS
        ============================================================ */
        .js-plotly-plot .plotly .main-svg {
            border-radius: var(--radius-md);
        }

        /* ============================================================
           SCROLLABLE CHART WRAPPER
        ============================================================ */
        .scrollable-chart {
            overflow-x: auto;
            overflow-y: hidden;
            width: 100%;
            padding-bottom: var(--space-xs);
            border-radius: var(--radius-md);
        }

        .scrollable-chart [data-testid="elementContainer"],
        .scrollable-chart [data-testid="stPlotlyChart"] {
            width: fit-content !important;
            min-width: fit-content !important;
        }

        /* Scrollbar — global sleek style */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--color-paper-2); border-radius: var(--radius-full); }
        ::-webkit-scrollbar-thumb { background: oklch(40% 0.01 240); border-radius: var(--radius-full); }
        ::-webkit-scrollbar-thumb:hover { background: oklch(52% 0.01 240); }

        /* ============================================================
           SIDEBAR
        ============================================================ */
        [data-testid="stSidebar"] {
            background-color: var(--color-paper-2) !important;
            border-right: 1px solid var(--color-rule) !important;
            width: 280px !important;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding-top: var(--space-md) !important;
            padding-left: var(--space-xs) !important;
            padding-right: var(--space-xs) !important;
        }

        /* Sidebar branding */
        .sidebar-branding {
            text-align: center;
            padding: var(--space-md) 0;
            margin-bottom: var(--space-xs);
        }

        .sidebar-branding img {
            width: 56px !important;
            height: auto !important;
            margin-bottom: var(--space-xs);
            border-radius: var(--radius-md);
            filter: drop-shadow(0 2px 8px oklch(63% 0.18 258 / 0.25));
        }

        .sidebar-title {
            font-size: var(--text-xl) !important;
            font-weight: 700 !important;
            color: var(--color-ink) !important;
            letter-spacing: -0.025em;
            margin-bottom: 0 !important;
        }

        .sidebar-subtitle {
            font-size: var(--text-xs);
            color: var(--color-ink-3);
            margin-top: var(--space-3xs);
        }

        /* Sidebar user box */
        .sidebar-user-box {
            background-color: var(--color-paper-3);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-md);
            padding: var(--space-xs) var(--space-sm);
            margin-bottom: var(--space-md);
            text-align: center;
        }

        .sidebar-welcome {
            font-size: var(--text-xs);
            color: var(--color-ink-3);
        }

        .sidebar-username {
            font-weight: 600;
            color: var(--color-accent);
            display: block;
            font-size: var(--text-sm);
        }

        /* Sidebar nav buttons */
        [data-testid="stSidebar"] .stButton > button {
            background-color: transparent !important;
            border: 1px solid transparent !important;
            text-align: left !important;
            padding: var(--space-xs) var(--space-sm) !important;
            margin-bottom: var(--space-3xs) !important;
            box-shadow: none !important;
            color: var(--color-ink-2) !important;
            justify-content: flex-start !important;
            font-weight: 500 !important;
            font-size: var(--text-sm) !important;
            border-radius: var(--radius-md) !important;
            height: 38px;
            letter-spacing: 0 !important;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                color var(--dur-micro) var(--ease-out) !important;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: var(--color-accent-low) !important;
            color: var(--color-ink) !important;
            border-color: transparent !important;
            transform: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] .stButton > button:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: -2px !important;
        }

        /* Active nav item — accent left-border */
        [data-testid="stSidebar"] .nav-active button {
            background-color: var(--color-accent-low) !important;
            color: var(--color-ink) !important;
            border-left: 3px solid var(--color-accent) !important;
            border-radius: 0 var(--radius-md) var(--radius-md) 0 !important;
            font-weight: 600 !important;
        }

        /* Sidebar footer */
        .sidebar-footer {
            margin-top: auto;
            padding-top: var(--space-lg);
            border-top: 1px solid var(--color-rule);
        }

        [data-testid="stSidebarNav"] { display: none !important; }

        /* ============================================================
           AUTH CONTAINER
        ============================================================ */
        .auth-container {
            max-width: 400px;
            margin: 5vh auto;
            padding: var(--space-xl) var(--space-lg);
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-xl);
            box-shadow: 0 20px 48px var(--color-shadow);
        }

        .auth-logo {
            font-size: var(--text-2xl);
            text-align: center;
            margin-bottom: var(--space-xs);
        }

        .auth-logo img {
            width: 72px;
            margin-bottom: var(--space-xs);
            border-radius: var(--radius-md);
        }

        /* ============================================================
           CENTER POPUP
        ============================================================ */
        .center-popup {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100vh !important;
            pointer-events: none !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            z-index: 99999 !important;
        }

        .center-popup > div {
            pointer-events: auto !important;
            width: 90% !important;
            max-width: 420px !important;
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-accent-mid) !important;
            box-shadow: 0 20px 48px var(--color-shadow) !important;
            text-align: center !important;
            border-radius: var(--radius-xl) !important;
            padding: var(--space-xs) !important;
        }

        .center-popup [data-testid="stNotification"] {
            position: relative !important;
            top: 0 !important;
            left: 0 !important;
            transform: none !important;
            width: 100% !important;
            margin: 0 !important;
        }

        /* ============================================================
           DASHBOARD CUSTOM CARDS
        ============================================================ */
        .wf-card {
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-lg);
            padding: var(--space-md) var(--space-lg);
            transition:
                border-color var(--dur-short) var(--ease-out),
                transform var(--dur-short) var(--ease-out);
        }

        .wf-card:hover {
            border-color: var(--color-accent-mid);
            transform: translateY(-2px);
        }

        /* Stat row dividers — hairline between siblings, no leading/trailing padding */
        .wf-stat-row {
            display: flex;
            align-items: center;
            gap: var(--space-md);
            padding: var(--space-xs) 0;
            border-top: 1px solid var(--color-rule);
        }
        .wf-stat-row:first-child { border-top: none; }

        /* Chip / Tag */
        .wf-chip {
            display: inline-flex;
            align-items: center;
            padding: var(--space-3xs) var(--space-xs);
            background-color: var(--color-paper-3);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-full);
            font-size: var(--text-xs);
            font-weight: 500;
            color: var(--color-ink-2);
            letter-spacing: 0;
            text-transform: none;
        }

        .wf-chip--accent {
            background-color: var(--color-accent-low);
            border-color: var(--color-accent-mid);
            color: var(--color-accent);
        }

        .wf-chip--success {
            background-color: oklch(65% 0.14 150 / 0.12);
            border-color: oklch(65% 0.14 150 / 0.3);
            color: var(--color-success);
        }

        .wf-chip--danger {
            background-color: oklch(63% 0.18 25 / 0.12);
            border-color: oklch(63% 0.18 25 / 0.3);
            color: var(--color-danger);
        }

        /* Empty state */
        .wf-empty {
            text-align: center;
            padding: var(--space-2xl) var(--space-lg);
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-lg);
        }

        .wf-empty-icon {
            font-size: 2rem;
            margin-bottom: var(--space-sm);
            display: block;
        }

        .wf-empty-title {
            font-size: var(--text-md);
            font-weight: 600;
            color: var(--color-ink);
            margin-bottom: var(--space-xs);
        }

        .wf-empty-body {
            font-size: var(--text-sm);
            color: var(--color-ink-3);
        }

        /* ============================================================
           MOBILE RESPONSIVE
        ============================================================ */
        @media (max-width: 48rem) {
            [data-testid="stSidebar"] {
                width: 85vw !important;
            }

            [data-testid="stMetricValue"] {
                font-size: var(--text-lg) !important;
            }

            .main .block-container {
                padding: var(--space-md) var(--space-xs) !important;
            }

            .auth-container {
                margin: var(--space-lg) var(--space-sm);
            }
        }

        /* ============================================================
           REDUCED MOTION
        ============================================================ */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)
