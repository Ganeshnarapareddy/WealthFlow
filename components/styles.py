import streamlit as st


def apply_styles():
    """
    Hallmark v2.0.0 App Screen Design System for WealthFlow Pro.
    Genre: modern-minimal | Theme: slate-steel (OKLCH hue 245) | Typeface: Geist + Geist Mono
    """
    st.markdown(
        """
        <style>
        /* Hallmark · app · genre: modern-minimal · theme: slate-steel · v2.0.0 */
        /* critique: hairline KPI strip, hover-expand clip-path rail, zero backdrop-blur jank, Geist tabular UI */
        /* waive: 44b (app screen behind auth, no marketing fold per flow.md § App screens) */
        /* waive: 58 (app screen dashboard, no marketing word budget per flow.md § App screens) */

        @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

        /* ============================================================
           1. TOKEN BLOCK — single source of truth (OKLCH, hue 245)
              No literal colour or font-family may appear past :root.
        ============================================================ */
        :root {
            /* Surfaces — deep slate-steel */
            --color-paper:              oklch(12% 0.014 245);
            --color-paper-2:            oklch(16% 0.013 245);
            --color-paper-3:            oklch(20% 0.012 245);
            --color-paper-4:            oklch(24% 0.011 245);

            /* Ink — neutral cool-tinted */
            --color-ink:                oklch(94% 0.004 245);
            --color-ink-2:              oklch(72% 0.007 245);
            --color-ink-3:              oklch(52% 0.007 245);

            /* Rules & field edges */
            --color-rule:               oklch(100% 0 0 / 0.08);
            --color-rule-strong:        oklch(100% 0 0 / 0.14);
            --color-field-edge:         oklch(100% 0 0 / 0.16);
            --color-transparent:        oklch(0% 0 0 / 0);

            /* Accent — single cobalt signal */
            --color-accent:             oklch(64% 0.19 258);
            --color-accent-hover:       oklch(69% 0.19 258);
            --color-accent-active:      oklch(59% 0.19 258);
            --color-accent-low:         oklch(64% 0.19 258 / 0.12);
            --color-accent-mid:         oklch(64% 0.19 258 / 0.28);
            --color-accent-ink:         oklch(97% 0.004 245);
            --color-focus:              oklch(72% 0.21 258);

            /* Semantic status */
            --color-success:            oklch(72% 0.15 152);
            --color-success-low:        oklch(72% 0.15 152 / 0.12);
            --color-success-mid:        oklch(72% 0.15 152 / 0.28);
            --color-warning:            oklch(80% 0.14  82);
            --color-warning-low:        oklch(80% 0.14  82 / 0.12);
            --color-warning-mid:        oklch(80% 0.14  82 / 0.28);
            --color-danger:             oklch(66% 0.19  24);
            --color-danger-low:         oklch(66% 0.19  24 / 0.12);
            --color-danger-mid:         oklch(66% 0.19  24 / 0.28);

            /* Scrollbars & overlays */
            --color-scroll-thumb:       oklch(34% 0.012 245);
            --color-scroll-thumb-hover: oklch(46% 0.014 245);
            --color-backdrop:           oklch(6% 0.014 245 / 0.72);
            --color-shadow:             oklch(4% 0.012 245 / 0.45);
            --color-shadow-deep:        oklch(4% 0.012 245 / 0.65);

            /* Typography — Geist + Geist Mono */
            --font-body:  'Geist', system-ui, -apple-system, sans-serif;
            --font-mono:  'Geist Mono', ui-monospace, monospace;

            /* Fixed app-screen type scale (ratio ~1.15) */
            --text-xs:    0.75rem;    /* 12px */
            --text-sm:    0.8125rem;  /* 13px */
            --text-base:  0.9375rem;  /* 15px */
            --text-md:    1.0625rem;  /* 17px */
            --text-lg:    1.25rem;    /* 20px */
            --text-xl:    1.5rem;     /* 24px */
            --text-2xl:   1.75rem;    /* 28px */

            /* Spacing scale (4pt) */
            --space-3xs:  0.125rem;   /* 2px */
            --space-2xs:  0.25rem;    /* 4px */
            --space-xs:   0.5rem;     /* 8px */
            --space-sm:   0.75rem;    /* 12px */
            --space-md:   1rem;       /* 16px */
            --space-lg:   1.5rem;     /* 24px */
            --space-xl:   2.5rem;     /* 40px */
            --space-2xl:  4rem;       /* 64px */

            /* Concentric radii */
            --radius-sm:   6px;
            --radius-md:   10px;
            --radius-lg:   16px;
            --radius-xl:   22px;
            --radius-full: 9999px;

            /* Shell geometry */
            --rail-collapsed: 72px;
            --rail-expanded:  260px;
            --rail-clip:      188px;  /* 260px - 72px */
            --topbar-height:  56px;
            --container-max:  1360px;

            /* Motion */
            --dur-press:  80ms;
            --dur-micro:  140ms;
            --dur-short:  220ms;
            --dur-long:   380ms;
            --ease-out:   cubic-bezier(0.16, 1, 0.3, 1);
            --ease-in:    cubic-bezier(0.4, 0, 1, 1);
            --ease-io:    cubic-bezier(0.4, 0, 0.2, 1);

            /* Elevation & z-index ladder */
            --shadow-raised: 0 1px 2px var(--color-shadow);
            --shadow-float:  0 12px 32px var(--color-shadow);
            --shadow-rail:   16px 0 40px var(--color-shadow-deep);
            --shadow-modal:  0 24px 56px var(--color-shadow-deep);
            --z-base:       1;
            --z-raised:     10;
            --z-dropdown:   100;
            --z-sticky:     200;
            --z-sticky-nav: 300;
            --z-modal:      400;
            --z-toast:      500;
            --z-tooltip:    600;
        }

        /* ============================================================
           2. BASE, SCROLLING & CONTAINER DISCIPLINE
        ============================================================ */
        html, body {
            overflow-x: clip !important;
            background-color: var(--color-paper) !important;
            color: var(--color-ink) !important;
            font-family: var(--font-body) !important;
            font-synthesis: none;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        [data-testid="stApp"],
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .main {
            font-family: var(--font-body) !important;
            background-color: var(--color-paper) !important;
            color: var(--color-ink) !important;
            scroll-behavior: smooth;
        }

        /* Keep Streamlit's own top header minimal & unobtrusive */
        header[data-testid="stHeader"] {
            background-color: var(--color-transparent) !important;
            height: 0 !important;
            min-height: 0 !important;
            overflow: visible !important;
        }
        [data-testid="stToolbar"] {
            top: var(--space-sm) !important;
            right: var(--space-md) !important;
            z-index: var(--z-sticky-nav) !important;
        }
        [data-testid="stDecoration"] {
            display: none !important;
        }

        /* Smooth scroll & stable gutter on primary scrollable view */
        [data-testid="stMain"] {
            overflow-y: auto !important;
            overflow-x: clip !important;
            scroll-behavior: smooth;
            scrollbar-gutter: stable;
        }

        /* Full-width top-left app shell alignment (flush top-left, aligned with sidebar logo) */
        .main .block-container,
        [data-testid="stMainBlockContainer"] {
            max-width: 100% !important;
            margin-inline: 0 !important;
            padding: 8px var(--space-lg) var(--space-2xl) var(--space-lg) !important;
            overflow-x: clip;
        }

        /* Remove zero-UI helper containers (style, link, cookie sync, hidden JS iframes) from flex flow
           so they never add 1rem gaps above the top bar while continuing to run normally */
        [data-testid="stElementContainer"]:has(> .stMarkdown style),
        [data-testid="stElementContainer"]:has(> .stMarkdown link),
        [data-testid="stElementContainer"]:has(iframe[title*="streamlit_cookies_manager"]),
        [data-testid="stElementContainer"]:has(iframe[title*="streamlit_javascript"]),
        [data-testid="stElementContainer"]:has(iframe[height="0"]) {
            position: fixed !important;
            top: -10px !important;
            left: -10px !important;
            width: 1px !important;
            height: 1px !important;
            margin: 0 !important;
            padding: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
            overflow: hidden !important;
        }

        /* Subtle entrance on route change (opacity + 4px rise only) */
        [data-testid="stMainBlockContainer"] > div {
            animation: wf-enter var(--dur-short) var(--ease-out);
        }

        @keyframes wf-enter {
            from {
                opacity: 0;
                transform: translateY(4px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Sleek rounded scrollbars everywhere */
        * {
            scrollbar-width: thin;
            scrollbar-color: var(--color-scroll-thumb) var(--color-transparent);
        }
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: var(--color-transparent);
            border-radius: var(--radius-full);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--color-scroll-thumb);
            border-radius: var(--radius-full);
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--color-scroll-thumb-hover);
        }

        /* ============================================================
           3. TYPOGRAPHY (Geist, tabular figures, zero tracked caps)
        ============================================================ */
        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-body) !important;
            color: var(--color-ink) !important;
            overflow-wrap: break-word;
            min-width: 0;
            text-wrap: balance;
            letter-spacing: -0.025em;
            line-height: 1.2;
        }

        h1, .main-header {
            font-size: var(--text-2xl) !important;
            font-weight: 700 !important;
            color: var(--color-ink) !important;
            margin: var(--space-xs) 0 var(--space-md) 0 !important;
            line-height: 1.15 !important;
        }

        h2 {
            font-size: var(--text-xl) !important;
            font-weight: 600 !important;
        }

        h3, .section-header {
            font-size: var(--text-lg) !important;
            font-weight: 600 !important;
            color: var(--color-ink) !important;
            letter-spacing: -0.015em !important;
            margin-top: var(--space-lg) !important;
            margin-bottom: var(--space-sm) !important;
            border-left: none !important;
            padding-left: 0 !important;
            text-transform: none !important;
        }

        h4 {
            font-size: var(--text-md) !important;
            font-weight: 600 !important;
            color: var(--color-ink) !important;
            margin-top: var(--space-md) !important;
            margin-bottom: var(--space-xs) !important;
        }

        p, li, .stMarkdown {
            color: var(--color-ink-2);
            font-size: var(--text-base);
            line-height: 1.55;
            text-wrap: pretty;
        }

        code, pre, .wf-mono {
            font-family: var(--font-mono) !important;
            font-variant-numeric: tabular-nums;
        }

        /* Form labels — sentence case, body face, step smaller, untracked */
        label,
        [data-testid="stWidgetLabel"] p {
            font-family: var(--font-body) !important;
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            color: var(--color-ink-2) !important;
            letter-spacing: 0 !important;
            text-transform: none !important;
        }

        hr, [data-testid="stDivider"] {
            border-color: var(--color-rule) !important;
            margin: var(--space-lg) 0 !important;
        }

        /* ============================================================
           4. STICKY TOP BAR (52px, flush top-left aligned with sidebar logo)
        ============================================================ */
        [data-testid="stHorizontalBlock"]:has(.wf-topbar-marker) {
            position: sticky;
            top: 0;
            z-index: var(--z-sticky-nav);
            min-height: 48px;
            align-items: center !important;
            padding: 4px 0 var(--space-sm) 0;
            margin: 0 0 var(--space-md) 0 !important;
            background-color: var(--color-paper);
            border-bottom: 1px solid var(--color-rule);
        }

        .wf-topbar-left {
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            min-width: 0;
        }

        .wf-topbar-crumb {
            font-size: var(--text-sm);
            font-weight: 500;
            color: var(--color-ink-3);
            white-space: nowrap;
        }

        .wf-topbar-crumb-btn {
            appearance: none;
            background-color: var(--color-transparent);
            border: 1px solid var(--color-transparent);
            border-radius: var(--radius-sm);
            padding: 4px 8px;
            margin-left: -8px;
            font-family: var(--font-body);
            cursor: pointer;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                border-color var(--dur-micro) var(--ease-out),
                color var(--dur-micro) var(--ease-out);
        }

        @media (hover: hover) {
            .wf-topbar-crumb-btn:hover {
                background-color: var(--color-paper-2);
                border-color: var(--color-rule);
                color: var(--color-ink);
            }
        }

        .wf-topbar-crumb-btn:focus-visible {
            outline: 2px solid var(--color-focus);
            outline-offset: 2px;
        }

        .wf-topbar-sep {
            color: var(--color-ink-3);
            opacity: 0.45;
            user-select: none;
        }

        .wf-topbar-page {
            font-size: var(--text-base);
            font-weight: 600;
            color: var(--color-ink);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .wf-topbar-tools {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: var(--space-sm);
            width: 100%;
        }

        /* Top-bar Profile & Currency Popovers — rounded rectangles matching wf-cmd-trigger */
        .st-key-tb_profile_pop,
        .st-key-tb_curr_pop {
            display: flex !important;
            justify-content: flex-end !important;
        }

        .st-key-tb_profile_pop [data-testid="stPopover"] > div > button,
        .st-key-tb_profile_pop button,
        .st-key-tb_curr_pop [data-testid="stPopover"] > div > button,
        .st-key-tb_curr_pop button {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 6px !important;
            height: 34px !important;
            min-height: 34px !important;
            padding: 0 12px !important;
            border-radius: var(--radius-md) !important;
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            color: var(--color-ink) !important;
            font-family: var(--font-body) !important;
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            cursor: pointer !important;
            white-space: nowrap !important;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                border-color var(--dur-micro) var(--ease-out),
                color var(--dur-micro) var(--ease-out),
                box-shadow var(--dur-micro) var(--ease-out),
                transform var(--dur-press) var(--ease-out) !important;
        }

        .st-key-tb_profile_pop button [data-testid="stMarkdownContainer"] p,
        .st-key-tb_curr_pop button [data-testid="stMarkdownContainer"] p {
            color: inherit !important;
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            margin: 0 !important;
            line-height: 1 !important;
        }

        .st-key-tb_profile_pop button [data-testid="stIconMaterial"],
        .st-key-tb_curr_pop button [data-testid="stIconMaterial"] {
            font-size: 18px !important;
            line-height: 1 !important;
            margin: 0 !important;
            color: inherit !important;
        }

        @media (hover: hover) {
            .st-key-tb_profile_pop button:hover,
            .st-key-tb_curr_pop button:hover {
                background-color: var(--color-paper-3) !important;
                border-color: var(--color-rule-strong) !important;
                color: var(--color-ink) !important;
            }
        }

        /* Pin profile popover menu cleanly inside viewport right edge (overrides Popper translate3d overflow) */
        div[data-baseweb="popover"]:has(.wf-profile-head),
        div[data-baseweb="popover"]:has([data-testid="stPopoverBody"] .wf-profile-head) {
            position: fixed !important;
            top: 52px !important;
            right: 20px !important;
            left: auto !important;
            transform: none !important;
            z-index: var(--z-tooltip) !important;
        }

        @media (hover: hover) {
            .st-key-tb_profile_pop button:hover {
                background-color: var(--color-accent-low) !important;
                border-color: var(--color-accent-mid) !important;
                color: var(--color-accent) !important;
                transform: translateY(-1px);
            }
        }

        /* Highlighted state when profile menu is open */
        .st-key-tb_profile_pop button[aria-expanded="true"] {
            background-color: var(--color-accent) !important;
            border-color: var(--color-accent) !important;
            color: var(--color-accent-ink) !important;
            box-shadow: 0 0 0 3px var(--color-accent-low) !important;
        }

        .st-key-tb_profile_pop button:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: 2px !important;
        }

        .wf-profile-head {
            padding-bottom: var(--space-xs);
            margin-bottom: var(--space-xs);
            border-bottom: 1px solid var(--color-rule);
        }

        .wf-profile-name {
            font-size: var(--text-base);
            font-weight: 600;
            color: var(--color-ink);
            line-height: 1.3;
        }

        .wf-profile-meta {
            font-size: var(--text-xs);
            color: var(--color-ink-3);
            font-family: var(--font-mono);
        }

        .wf-cmd-trigger {
            display: inline-flex;
            align-items: center;
            gap: var(--space-sm);
            height: 34px;
            padding: 0 var(--space-sm);
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-md);
            color: var(--color-ink-2);
            font-family: var(--font-body);
            font-size: var(--text-sm);
            cursor: pointer;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                border-color var(--dur-micro) var(--ease-out),
                color var(--dur-micro) var(--ease-out);
        }

        @media (hover: hover) {
            .wf-cmd-trigger:hover {
                background-color: var(--color-paper-3);
                border-color: var(--color-rule-strong);
                color: var(--color-ink);
            }
        }

        .wf-cmd-trigger:focus-visible {
            outline: 2px solid var(--color-focus);
            outline-offset: 2px;
        }

        .wf-kbd {
            font-family: var(--font-mono);
            font-size: var(--text-xs);
            color: var(--color-ink-3);
            background-color: var(--color-paper-3);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-sm);
            padding: 1px 6px;
            line-height: 1.4;
        }

        .wf-topbar-pill {
            display: inline-flex;
            align-items: center;
            height: 30px;
            padding: 0 var(--space-xs);
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-full);
            font-family: var(--font-mono);
            font-size: var(--text-xs);
            font-weight: 500;
            color: var(--color-ink-2);
        }

        /* Topbar Currency & Profile Popovers (Rounded Rectangles matching Jump-To) */
        [class*="st-key-tb_curr_pop"] [data-testid="stPopoverButton"],
        [class*="st-key-tb_profile_pop"] [data-testid="stPopoverButton"] {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 6px !important;
            height: 34px !important;
            min-height: 34px !important;
            padding: 0 12px !important;
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            border-radius: var(--radius-md) !important;
            color: var(--color-ink-2) !important;
            font-family: var(--font-body) !important;
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            cursor: pointer !important;
            box-shadow: none !important;
            transition: all 0.15s ease !important;
            white-space: nowrap !important;
        }
        [class*="st-key-tb_curr_pop"] [data-testid="stPopoverButton"]:hover,
        [class*="st-key-tb_profile_pop"] [data-testid="stPopoverButton"]:hover {
            background-color: var(--color-paper-3) !important;
            border-color: var(--color-rule-strong) !important;
            color: var(--color-ink) !important;
        }
        [class*="st-key-tb_curr_pop"] [data-testid="stPopoverButton"] p,
        [class*="st-key-tb_profile_pop"] [data-testid="stPopoverButton"] p {
            color: inherit !important;
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            margin: 0 !important;
        }

        .wf-avatar {
            width: 32px;
            height: 32px;
            border-radius: var(--radius-full);
            background-color: var(--color-accent-low);
            border: 1px solid var(--color-accent-mid);
            color: var(--color-accent);
            font-size: var(--text-xs);
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            user-select: none;
        }

        /* ============================================================
           5. HOVER-EXPAND NAVIGATION RAIL (GPU clip-path, ZERO reflow)
        ============================================================ */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        [data-testid="stSidebar"] {
            background-color: var(--color-paper-2) !important;
            border-right: 1px solid var(--color-rule) !important;
        }

        /* Strip Streamlit's default nested sidebar padding so 72px rail icons sit dead-center */
        [data-testid="stSidebarContent"] {
            padding: 0 !important;
        }

        [data-testid="stSidebarUserContent"] {
            padding: var(--space-sm) 8px var(--space-md) 8px !important;
        }

        /* Desktop hover-expand rail (min-width: 60rem) */
        @media (min-width: 60rem) {
            /* Hide Streamlit's empty sidebar header, resize grip & clunky arrows on desktop */
            [data-testid="stSidebarHeader"],
            [data-testid="stSidebarCollapseButton"],
            [data-testid="collapsedControl"],
            [data-testid="stExpandSidebarButton"],
            [data-testid="stSidebar"] [data-testid="stSidebarResizeHandle"] {
                display: none !important;
            }

            [data-testid="stSidebar"] {
                position: fixed !important;
                inset: 0 auto 0 0 !important;
                width: var(--rail-expanded) !important;
                min-width: var(--rail-expanded) !important;
                max-width: var(--rail-expanded) !important;
                transform: none !important;
                z-index: var(--z-modal) !important;
                overflow-x: clip !important;
                overflow-y: auto !important;
                scrollbar-width: none;
                clip-path: inset(0 var(--rail-clip) 0 0);
                border-right: none !important;
                transition:
                    clip-path var(--dur-short) var(--ease-out),
                    box-shadow var(--dur-short) var(--ease-out) !important;
            }

            [data-testid="stSidebar"]::-webkit-scrollbar {
                width: 0;
            }

            /* Crisp hairline on the 72px collapsed rail edge */
            [data-testid="stSidebar"]::after {
                content: "";
                position: fixed;
                top: 0;
                bottom: 0;
                left: calc(var(--rail-collapsed) - 1px);
                width: 1px;
                background-color: var(--color-rule);
                pointer-events: none;
                opacity: 1;
                transition: opacity var(--dur-micro) var(--ease-out);
            }

            /* Expand smoothly on hover, keyboard focus, or user pin */
            [data-testid="stSidebar"]:hover,
            [data-testid="stSidebar"]:focus-within,
            [data-testid="stSidebar"].wf-pinned {
                clip-path: inset(0 0 0 0 round 0 var(--radius-lg) var(--radius-lg) 0);
                box-shadow: var(--shadow-rail);
                border-right: 1px solid var(--color-rule-strong) !important;
                scrollbar-width: thin;
            }

            [data-testid="stSidebar"]:hover::-webkit-scrollbar,
            [data-testid="stSidebar"]:focus-within::-webkit-scrollbar,
            [data-testid="stSidebar"].wf-pinned::-webkit-scrollbar {
                width: 6px;
            }

            /* When collapsed, show clean centered icon highlight without sliced blue bar */
            [data-testid="stSidebar"]:not(:hover):not(:focus-within):not(.wf-pinned) .stButton > button[kind="primary"] {
                background-color: var(--color-transparent) !important;
            }

            [data-testid="stSidebar"]:not(:hover):not(:focus-within):not(.wf-pinned) .stButton > button[kind="primary"] [data-testid="stIconMaterial"] {
                background-color: var(--color-accent-low);
                border-radius: var(--radius-sm);
                width: 36px !important;
                min-width: 36px !important;
                height: 36px !important;
                margin-left: -8px;
            }

            [data-testid="stSidebar"]:hover::after,
            [data-testid="stSidebar"]:focus-within::after,
            [data-testid="stSidebar"].wf-pinned::after {
                opacity: 0;
            }

            /* Offset main workspace ONLY when the sidebar rail is mounted (zero horizontal overflow) */
            [data-testid="stAppViewContainer"]:has([data-testid="stSidebar"]) [data-testid="stMain"] {
                margin-left: var(--rail-collapsed) !important;
                width: calc(100% - var(--rail-collapsed)) !important;
                max-width: calc(100% - var(--rail-collapsed)) !important;
            }

            body.wf-rail-pinned [data-testid="stAppViewContainer"]:has([data-testid="stSidebar"]) [data-testid="stMain"] {
                margin-left: var(--rail-expanded) !important;
                width: calc(100% - var(--rail-expanded)) !important;
                max-width: calc(100% - var(--rail-expanded)) !important;
            }

            body.wf-rail-pinned [data-testid="stSidebar"] {
                clip-path: inset(0 0 0 0);
                box-shadow: none;
                border-right: 1px solid var(--color-rule) !important;
            }

            /* Rail brand text, labels, currency picker fade in when expanded */
            [data-testid="stSidebar"] .wf-rail-text,
            [data-testid="stSidebar"] .wf-rail-extra,
            [data-testid="stSidebar"] .stSelectbox,
            [data-testid="stSidebar"] .stButton > button p,
            [data-testid="stSidebar"] [data-testid="stPopover"] button p {
                opacity: 0;
                transform: translateX(-4px);
                white-space: nowrap;
                transition:
                    opacity var(--dur-micro) var(--ease-out),
                    transform var(--dur-micro) var(--ease-out);
            }

            [data-testid="stSidebar"]:hover .wf-rail-text,
            [data-testid="stSidebar"]:focus-within .wf-rail-text,
            [data-testid="stSidebar"].wf-pinned .wf-rail-text,
            [data-testid="stSidebar"]:hover .wf-rail-extra,
            [data-testid="stSidebar"]:focus-within .wf-rail-extra,
            [data-testid="stSidebar"].wf-pinned .wf-rail-extra,
            [data-testid="stSidebar"]:hover .stSelectbox,
            [data-testid="stSidebar"]:focus-within .stSelectbox,
            [data-testid="stSidebar"].wf-pinned .stSelectbox,
            [data-testid="stSidebar"]:hover .stButton > button p,
            [data-testid="stSidebar"]:focus-within .stButton > button p,
            [data-testid="stSidebar"].wf-pinned .stButton > button p,
            [data-testid="stSidebar"]:hover [data-testid="stPopover"] button p,
            [data-testid="stSidebar"]:focus-within [data-testid="stPopover"] button p,
            [data-testid="stSidebar"].wf-pinned [data-testid="stPopover"] button p {
                opacity: 1;
                transform: translateX(0);
            }
        }

        /* Sidebar brand row */
        .wf-rail-brand {
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            padding: var(--space-xs) var(--space-xs) var(--space-md) 10px;
            margin-bottom: var(--space-xs);
            border-bottom: 1px solid var(--color-rule);
        }

        .wf-rail-brand-home {
            appearance: none;
            background: var(--color-transparent);
            border: none;
            padding: 0;
            margin: 0;
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            text-align: left;
            cursor: pointer;
            min-width: 0;
            border-radius: var(--radius-md);
        }

        .wf-rail-brand-home:focus-visible {
            outline: 2px solid var(--color-focus);
            outline-offset: 2px;
        }

        .wf-rail-logo {
            width: 36px;
            height: 36px;
            border-radius: var(--radius-md);
            object-fit: cover;
            flex-shrink: 0;
            background-color: var(--color-paper-3);
            border: 1px solid var(--color-rule);
        }

        .wf-rail-logo-fallback {
            width: 36px;
            height: 36px;
            border-radius: var(--radius-md);
            background-color: var(--color-accent-low);
            border: 1px solid var(--color-accent-mid);
            color: var(--color-accent);
            font-weight: 700;
            font-size: var(--text-md);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .wf-rail-title {
            font-size: var(--text-md);
            font-weight: 700;
            color: var(--color-ink);
            letter-spacing: -0.02em;
            line-height: 1.2;
        }

        .wf-rail-sub {
            font-size: var(--text-xs);
            color: var(--color-ink-3);
            line-height: 1.2;
        }

        .wf-pin-btn {
            margin-left: auto;
            width: 30px;
            height: 30px;
            border-radius: var(--radius-sm);
            border: 1px solid var(--color-rule);
            background-color: var(--color-paper-3);
            color: var(--color-ink-2);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                border-color var(--dur-micro) var(--ease-out),
                color var(--dur-micro) var(--ease-out);
        }

        @media (hover: hover) {
            .wf-pin-btn:hover {
                background-color: var(--color-paper-4);
                border-color: var(--color-rule-strong);
                color: var(--color-ink);
            }
        }

        /* Unmistakable red active highlight when sidebar rail is pinned */
        .wf-pin-btn.is-pinned {
            color: var(--color-danger) !important;
            background-color: var(--color-danger-low) !important;
            border-color: var(--color-danger-mid) !important;
        }

        .wf-pin-btn:focus-visible {
            outline: 2px solid var(--color-focus);
            outline-offset: 2px;
        }

        /* Sidebar section label (clean breathing room above Currency dropdown) */
        .wf-rail-label {
            display: block !important;
            font-size: var(--text-xs) !important;
            font-weight: 500 !important;
            color: var(--color-ink-3) !important;
            line-height: 1.4 !important;
            padding: 0 var(--space-sm) 0 12px !important;
            margin: var(--space-md) 0 var(--space-xs) 0 !important;
        }

        [data-testid="stSidebar"] .stSelectbox {
            padding: 0 6px !important;
            margin-top: var(--space-sm) !important;
        }

        /* Sidebar navigation buttons — ALL icons & labels locked to ONE straight vertical axis */
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] [data-testid="stPopover"] > div > button,
        [data-testid="stSidebar"] [data-testid="stPopover"] button {
            background-color: var(--color-transparent) !important;
            border: 1px solid var(--color-transparent) !important;
            box-shadow: none !important;
            color: var(--color-ink-2) !important;
            width: 100% !important;
            height: 40px !important;
            min-height: 40px !important;
            padding: 0 var(--space-sm) 0 18px !important;
            margin-bottom: 2px !important;
            border-radius: var(--radius-md) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            text-align: left !important;
            gap: var(--space-sm) !important;
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                color var(--dur-micro) var(--ease-out) !important;
        }

        /* Force EVERY nested Streamlit 1.57 button wrapper (div + span[data-has-shortcut]) to left-align */
        [data-testid="stSidebar"] .stButton > button > div,
        [data-testid="stSidebar"] .stButton > button > div > span,
        [data-testid="stSidebar"] [data-testid="stPopover"] button > div,
        [data-testid="stSidebar"] [data-testid="stPopover"] button > div > span {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            text-align: left !important;
            gap: var(--space-sm) !important;
            width: 100% !important;
        }

        [data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stPopover"] button [data-testid="stMarkdownContainer"] {
            text-align: left !important;
        }

        /* Keep Material icons crisp, left-anchored at x=36px center of 72px rail */
        [data-testid="stSidebar"] [data-testid="stIconMaterial"] {
            font-size: 20px !important;
            width: 20px !important;
            min-width: 20px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
            opacity: 1 !important;
        }

        @media (hover: hover) {
            [data-testid="stSidebar"] .stButton > button:hover,
            [data-testid="stSidebar"] [data-testid="stPopover"] > div > button:hover,
            [data-testid="stSidebar"] [data-testid="stPopover"] button:hover {
                background-color: var(--color-paper-3) !important;
                border-color: var(--color-transparent) !important;
                color: var(--color-ink) !important;
                transform: none !important;
                box-shadow: none !important;
            }
        }

        [data-testid="stSidebar"] .stButton > button:focus-visible,
        [data-testid="stSidebar"] [data-testid="stPopover"] > div > button:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: -2px !important;
        }

        /* Active nav item — crisp accent indicator & tinted pill (native kind="primary") */
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background-color: var(--color-accent-low) !important;
            color: var(--color-ink) !important;
            font-weight: 600 !important;
            position: relative !important;
        }

        [data-testid="stSidebar"] .stButton > button[kind="primary"]::before {
            content: "";
            position: absolute;
            left: 0;
            top: 8px;
            bottom: 8px;
            width: 3px;
            border-radius: var(--radius-full);
            background-color: var(--color-accent);
        }

        [data-testid="stSidebar"] .stButton > button[kind="primary"] [data-testid="stIconMaterial"] {
            color: var(--color-accent) !important;
        }

        @media (hover: hover) {
            [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
                background-color: var(--color-accent-mid) !important;
                color: var(--color-ink) !important;
                transform: none !important;
            }
        }

        /* Tighten vertical gaps inside sidebar */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 2px !important;
        }

        .sidebar-footer {
            margin-top: var(--space-md);
            padding-top: var(--space-sm);
            border-top: 1px solid var(--color-rule);
        }

        /* ============================================================
           6. HAIRLINE STAT STRIP (Dashboard KPIs — no card-in-card)
        ============================================================ */
        .wf-stat-strip {
            display: grid;
            grid-template-columns: repeat(var(--wf-cols, 4), minmax(0, 1fr));
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-lg);
            margin-bottom: var(--space-md);
            overflow: hidden;
        }

        .wf-stat-cell {
            padding: var(--space-md) var(--space-lg);
            display: flex;
            flex-direction: column;
            gap: var(--space-2xs);
            min-width: 0;
            position: relative;
        }

        .wf-stat-cell + .wf-stat-cell {
            border-left: 1px solid var(--color-rule);
        }

        .wf-stat-label {
            font-size: var(--text-sm);
            font-weight: 500;
            color: var(--color-ink-2);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .wf-stat-value {
            font-size: var(--text-xl);
            font-weight: 700;
            color: var(--color-ink);
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.025em;
            line-height: 1.2;
        }

        .wf-stat-delta {
            display: inline-flex;
            align-items: center;
            align-self: flex-start;
            margin-top: var(--space-3xs);
            padding: 2px 8px;
            border-radius: var(--radius-full);
            font-size: var(--text-xs);
            font-weight: 500;
            font-variant-numeric: tabular-nums;
            background-color: var(--color-paper-3);
            color: var(--color-ink-2);
        }

        .wf-stat-delta--positive {
            background-color: var(--color-success-low);
            color: var(--color-success);
        }

        .wf-stat-delta--negative {
            background-color: var(--color-danger-low);
            color: var(--color-danger);
        }

        .wf-stat-delta--accent {
            background-color: var(--color-accent-low);
            color: var(--color-accent);
        }

        @media (max-width: 56rem) {
            .wf-stat-strip {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .wf-stat-cell:nth-child(odd) {
                border-left: none;
            }
            .wf-stat-cell:nth-child(n + 3) {
                border-top: 1px solid var(--color-rule);
            }
        }

        @media (max-width: 30rem) {
            .wf-stat-strip {
                grid-template-columns: 1fr;
            }
            .wf-stat-cell + .wf-stat-cell {
                border-left: none;
                border-top: 1px solid var(--color-rule);
            }
        }

        /* ============================================================
           7. NATIVE STREAMLIT METRICS, EXPANDERS & CONTAINERS
        ============================================================ */
        div[data-testid="metric-container"],
        [data-testid="stMetric"] {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            border-radius: var(--radius-lg) !important;
            padding: var(--space-md) var(--space-lg) !important;
            box-shadow: var(--shadow-raised) !important;
            transition:
                border-color var(--dur-short) var(--ease-out),
                transform var(--dur-short) var(--ease-out) !important;
        }

        @media (hover: hover) {
            div[data-testid="metric-container"]:hover,
            [data-testid="stMetric"]:hover {
                border-color: var(--color-rule-strong) !important;
                transform: translateY(-1px);
            }
        }

        [data-testid="stMetricValue"] {
            font-size: var(--text-xl) !important;
            font-weight: 700 !important;
            color: var(--color-ink) !important;
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.025em;
        }

        [data-testid="stMetricLabel"] p {
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            color: var(--color-ink-2) !important;
        }

        [data-testid="stMetricDelta"] {
            font-size: var(--text-xs) !important;
            font-weight: 500 !important;
            font-variant-numeric: tabular-nums;
        }

        /* Expanders — clean rounded surface, zero blur jank */
        [data-testid="stExpander"] {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            border-radius: var(--radius-lg) !important;
            overflow: hidden;
        }

        [data-testid="stExpander"] details > summary {
            font-size: var(--text-base) !important;
            font-weight: 600 !important;
            color: var(--color-ink) !important;
            padding: var(--space-sm) var(--space-md) !important;
            transition: background-color var(--dur-micro) var(--ease-out);
        }

        @media (hover: hover) {
            [data-testid="stExpander"] details > summary:hover {
                background-color: var(--color-paper-3);
            }
        }

        [data-testid="stExpander"] details > summary:focus-visible {
            outline: 2px solid var(--color-focus);
            outline-offset: -2px;
        }

        /* Scrollable containers (e.g. Alerts box) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: var(--radius-lg) !important;
            border-color: var(--color-rule) !important;
        }

        /* Hide heading anchor chain-link icons (consistent across Streamlit versions) */
        [data-testid="stHeaderActionElements"],
        h1 a.header-anchor, h2 a.header-anchor, h3 a.header-anchor {
            display: none !important;
        }

        /* ============================================================
           8. SEGMENTED TABS & CONTROLS (BaseWeb + React Aria unified pill rail)
        ============================================================ */
        [data-testid="stTabs"] [role="tablist"],
        .stTabs [role="tablist"],
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            border-radius: var(--radius-md) !important;
            padding: 6px !important;
            gap: 8px !important;
            margin-bottom: var(--space-md) !important;
            overflow-x: auto !important;
            scrollbar-width: none !important;
            display: flex !important;
            align-items: center !important;
            width: fit-content !important;
            max-width: 100% !important;
        }

        [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar,
        .stTabs [role="tablist"]::-webkit-scrollbar {
            display: none;
        }

        /* Works on BOTH BaseWeb (<button role="tab">) and React Aria (<div data-testid="stTab" role="tab">) */
        [data-testid="stTabs"] [role="tab"],
        [data-testid="stTabs"] [data-testid="stTab"],
        [data-testid="stTabs"] button[role="tab"],
        .stTabs [role="tab"] {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: var(--radius-sm) !important;
            padding: 0 var(--space-md) !important;
            height: 36px !important;
            min-height: 36px !important;
            color: var(--color-ink-2) !important;
            font-family: var(--font-body) !important;
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            border: 1px solid var(--color-rule-strong) !important;
            background-color: var(--color-paper-3) !important;
            cursor: pointer !important;
            white-space: nowrap !important;
            flex-shrink: 0 !important;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                border-color var(--dur-micro) var(--ease-out),
                color var(--dur-micro) var(--ease-out),
                box-shadow var(--dur-micro) var(--ease-out) !important;
        }

        [data-testid="stTabs"] [role="tab"] p,
        [data-testid="stTabs"] [data-testid="stTab"] p,
        .stTabs [role="tab"] p {
            color: inherit !important;
            font-weight: inherit !important;
            font-size: var(--text-sm) !important;
            margin: 0 !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
        }

        /* Appealing, unmistakable active tab highlight */
        [data-testid="stTabs"] [role="tab"][aria-selected="true"],
        [data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"],
        [data-testid="stTabs"] [role="tab"][data-selected="true"],
        .stTabs [role="tab"][aria-selected="true"] {
            background-color: var(--color-accent) !important;
            border-color: var(--color-accent) !important;
            color: var(--color-accent-ink) !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 10px oklch(0.64 0.19 258 / 0.34) !important;
        }

        [data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
        [data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] *,
        .stTabs [role="tab"][aria-selected="true"] * {
            color: var(--color-accent-ink) !important;
        }

        @media (hover: hover) {
            [data-testid="stTabs"] [role="tab"]:not([aria-selected="true"]):hover,
            [data-testid="stTabs"] [data-testid="stTab"]:not([aria-selected="true"]):hover,
            .stTabs [role="tab"]:not([aria-selected="true"]):hover {
                color: var(--color-ink) !important;
                background-color: var(--color-paper-4) !important;
                border-color: var(--color-field-edge) !important;
            }
        }

        [data-testid="stTabs"] [role="tab"]:focus-visible,
        [data-testid="stTabs"] [data-testid="stTab"]:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: -2px !important;
        }

        /* Hide BOTH BaseWeb and React Aria default bottom underline indicators */
        [data-testid="stTabs"] [data-baseweb="tab-highlight"],
        [data-testid="stTabs"] [data-baseweb="tab-border"],
        [data-testid="stTabs"] .react-aria-SelectionIndicator,
        [data-testid="stTabs"] [role="tablist"]::after,
        .stTabs .react-aria-SelectionIndicator,
        .stTabs [role="tablist"]::after {
            display: none !important;
        }

        /* State-persisted Segmented Control (TripFlow tabs — matching crisp pill rail) */
        [data-testid="stSegmentedControl"] [role="radiogroup"],
        [data-testid="stButtonGroup"] > div {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule) !important;
            border-radius: var(--radius-md) !important;
            padding: 6px !important;
            gap: 8px !important;
            display: flex !important;
            flex-wrap: wrap !important;
        }

        [data-testid="stSegmentedControl"] button,
        [data-testid="stButtonGroup"] button {
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--color-rule-strong) !important;
            background-color: var(--color-paper-3) !important;
            color: var(--color-ink-2) !important;
            font-family: var(--font-body) !important;
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            height: 36px !important;
            padding: 0 var(--space-md) !important;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                border-color var(--dur-micro) var(--ease-out),
                color var(--dur-micro) var(--ease-out),
                box-shadow var(--dur-micro) var(--ease-out) !important;
        }

        [data-testid="stSegmentedControl"] button[aria-checked="true"],
        [data-testid="stButtonGroup"] button[kind="segmented_controlActive"],
        [data-testid="stButtonGroup"] button[aria-pressed="true"] {
            background-color: var(--color-accent) !important;
            border-color: var(--color-accent) !important;
            color: var(--color-accent-ink) !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 10px oklch(0.64 0.19 258 / 0.34) !important;
        }

        [data-testid="stSegmentedControl"] button[aria-checked="true"] *,
        [data-testid="stButtonGroup"] button[kind="segmented_controlActive"] *,
        [data-testid="stButtonGroup"] button[aria-pressed="true"] * {
            color: var(--color-accent-ink) !important;
        }

        @media (hover: hover) {
            [data-testid="stSegmentedControl"] button:not([aria-checked="true"]):hover,
            [data-testid="stButtonGroup"] button:not([kind="segmented_controlActive"]):not([aria-pressed="true"]):hover {
                background-color: var(--color-paper-4) !important;
                border-color: var(--color-field-edge) !important;
                color: var(--color-ink) !important;
            }
        }

        /* ============================================================
           8B. SLEEK UPCOMING DUES & ALERTS ROWS
        ============================================================ */
        .wf-alert-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-left: 3px solid var(--color-rule-strong);
            border-radius: var(--radius-md);
            padding: 10px 14px;
            min-height: 48px;
        }
        .wf-alert-row.tone-danger { border-left-color: var(--color-danger); }
        .wf-alert-row.tone-warning { border-left-color: var(--color-warning); }
        .wf-alert-row.tone-positive { border-left-color: var(--color-positive); }
        .wf-alert-row.tone-accent { border-left-color: var(--color-accent); }
        .wf-alert-row.tone-muted { border-left-color: var(--color-ink-3); }

        /* Alert Action Pill Buttons (Uniform size, Centered, Green hover on Received, Red hover on Paid) */
        [data-testid="stHorizontalBlock"]:has([class*="st-key-alert_act_"]) {
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
        }
        [data-testid="stHorizontalBlock"]:has([class*="st-key-alert_act_"]) > [data-testid="column"]:first-child {
            flex: 1 1 0px !important;
            min-width: 0 !important;
        }
        [data-testid="stHorizontalBlock"]:has([class*="st-key-alert_act_"]) > [data-testid="column"]:last-child {
            flex: 0 0 94px !important;
            width: 94px !important;
            min-width: 94px !important;
            max-width: 94px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        [class*="st-key-alert_act_"] {
            width: 100% !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        [class*="st-key-alert_act_"] button {
            width: 86px !important;
            min-width: 86px !important;
            max-width: 86px !important;
            height: 32px !important;
            min-height: 32px !important;
            padding: 0 10px !important;
            border-radius: var(--radius-full) !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            white-space: nowrap !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            margin: 0 auto !important;
            transition: all 0.15s ease !important;
        }
        /* Hover Green for Receive */
        [class*="st-key-alert_act_receive_"] button:hover {
            background-color: rgba(16, 185, 129, 0.18) !important;
            border-color: #10B981 !important;
            color: #10B981 !important;
        }
        [class*="st-key-alert_act_receive_"] button:hover * {
            color: #10B981 !important;
        }
        /* Hover Red for Paid */
        [class*="st-key-alert_act_sub_"] button:hover,
        [class*="st-key-alert_act_cc_emi_"] button:hover,
        [class*="st-key-alert_act_cc_bill_"] button:hover,
        [class*="st-key-alert_act_paid_"] button:hover {
            background-color: rgba(239, 68, 68, 0.18) !important;
            border-color: #EF4444 !important;
            color: #EF4444 !important;
        }
        [class*="st-key-alert_act_sub_"] button:hover *,
        [class*="st-key-alert_act_cc_emi_"] button:hover *,
        [class*="st-key-alert_act_cc_bill_"] button:hover *,
        [class*="st-key-alert_act_paid_"] button:hover * {
            color: #EF4444 !important;
        }

        .wf-alert-main {
            display: flex;
            flex-direction: column;
            gap: 3px;
            min-width: 0;
        }
        .wf-alert-title {
            font-size: var(--text-sm);
            font-weight: 600;
            color: var(--color-ink);
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .wf-alert-cat {
            font-size: 11px;
            font-weight: 500;
            color: var(--color-ink-3);
            background-color: var(--color-paper-3);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-full);
            padding: 1px 8px;
            line-height: 1.4;
        }
        .wf-alert-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: var(--text-xs);
            color: var(--color-ink-3);
        }
        .wf-alert-due {
            font-weight: 600;
            padding: 1px 7px;
            border-radius: var(--radius-full);
            font-size: 11px;
            line-height: 1.4;
        }
        .wf-alert-due.tone-danger { background: var(--color-danger-low); color: var(--color-danger); }
        .wf-alert-due.tone-warning { background: var(--color-warning-low); color: var(--color-warning); }
        .wf-alert-due.tone-positive { background: var(--color-positive-low); color: var(--color-positive); }
        .wf-alert-due.tone-accent { background: var(--color-accent-low); color: var(--color-accent); }
        .wf-alert-due.tone-muted { background: var(--color-paper-3); color: var(--color-ink-2); }

        .wf-alert-amt {
            font-family: var(--font-mono);
            font-variant-numeric: tabular-nums;
            font-size: var(--text-sm);
            font-weight: 600;
            color: var(--color-ink);
            white-space: nowrap;
            flex-shrink: 0;
        }

        /* Compact pill-style alert action buttons (Paid / Received) */
        [class*="st-key-alert_act_"] .stButton > button,
        [class*="st-key-alert_act_"] button {
            height: 32px !important;
            min-height: 32px !important;
            padding: 0 14px !important;
            border-radius: var(--radius-full) !important;
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule-strong) !important;
            color: var(--color-ink-2) !important;
            font-size: var(--text-xs) !important;
            font-weight: 600 !important;
            width: auto !important;
            min-width: 86px !important;
        }
        @media (hover: hover) {
            [class*="st-key-alert_act_"] .stButton > button:hover,
            [class*="st-key-alert_act_"] button:hover {
                background-color: var(--color-success-low) !important;
                border-color: var(--color-success-mid) !important;
                color: var(--color-success) !important;
            }
            [class*="st-key-alert_act_"] button:hover * {
                color: var(--color-success) !important;
            }
        }

        /* Floating Toast Popups (positioned cleanly at top-right below topbar) */
        [data-testid="stToastContainer"] {
            top: 64px !important;
            right: 24px !important;
            bottom: auto !important;
            z-index: var(--z-toast) !important;
        }

        [data-testid="stToast"] {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-success-mid) !important;
            border-left: 3px solid var(--color-success) !important;
            border-radius: var(--radius-md) !important;
            box-shadow: var(--shadow-float) !important;
            color: var(--color-ink) !important;
            font-family: var(--font-body) !important;
        }

        /* ============================================================
           9. FORM CONTROLS (8-state discipline, no border-width jump)
        ============================================================ */
        input, select, textarea,
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div,
        [data-baseweb="textarea"] > div {
            background-color: var(--color-paper-3) !important;
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--color-field-edge) !important;
            color: var(--color-ink) !important;
            font-family: var(--font-body) !important;
            font-size: var(--text-base) !important;
            transition:
                border-color var(--dur-micro) var(--ease-out),
                background-color var(--dur-micro) var(--ease-out),
                box-shadow var(--dur-micro) var(--ease-out) !important;
        }

        @media (hover: hover) {
            [data-baseweb="select"] > div:hover,
            [data-baseweb="input"] > div:hover,
            [data-baseweb="textarea"] > div:hover {
                border-color: var(--color-rule-strong) !important;
                background-color: var(--color-paper-4) !important;
            }
        }

        input:focus, select:focus, textarea:focus,
        [data-baseweb="select"]:focus-within > div,
        [data-baseweb="input"]:focus-within > div,
        [data-baseweb="textarea"]:focus-within > div {
            border-color: var(--color-accent) !important;
            box-shadow: 0 0 0 3px var(--color-accent-low) !important;
        }

        input:focus-visible, select:focus-visible, textarea:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: -2px !important;
        }

        /* Dropdown menu */
        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="menu"] {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule-strong) !important;
            border-radius: var(--radius-md) !important;
            box-shadow: var(--shadow-float) !important;
            padding: 4px !important;
        }

        [data-baseweb="option"] {
            border-radius: var(--radius-sm) !important;
            font-size: var(--text-sm) !important;
        }

        [data-baseweb="option"]:hover,
        [data-baseweb="option"][aria-selected="true"] {
            background-color: var(--color-accent-low) !important;
            color: var(--color-ink) !important;
        }

        /* Radio buttons (e.g., Calendar / Fiscal toggle) */
        [data-testid="stRadio"] > div {
            gap: var(--space-sm) !important;
        }

        /* ============================================================
           10. BUTTONS (tactile micro-motion, restrained accent)
        ============================================================ */
        .stButton > button,
        [data-testid="stFormSubmitButton"] > button {
            background-color: var(--color-paper-3) !important;
            color: var(--color-ink) !important;
            border: 1px solid var(--color-field-edge) !important;
            border-radius: var(--radius-md) !important;
            padding: 0 var(--space-md) !important;
            height: 38px !important;
            min-height: 38px !important;
            font-family: var(--font-body) !important;
            font-size: var(--text-sm) !important;
            font-weight: 500 !important;
            letter-spacing: 0 !important;
            white-space: nowrap !important;
            box-shadow: none !important;
            transition:
                background-color var(--dur-micro) var(--ease-out),
                border-color var(--dur-micro) var(--ease-out),
                transform var(--dur-press) var(--ease-out) !important;
        }

        .stButton > button [data-testid="stMarkdownContainer"] p,
        [data-testid="stFormSubmitButton"] > button [data-testid="stMarkdownContainer"] p {
            white-space: nowrap !important;
            margin: 0 !important;
            line-height: 1.2 !important;
        }

        /* Primary CTA buttons & form submit buttons get the cobalt signal */
        .stButton button[kind="primary"],
        [data-testid="stFormSubmitButton"] button {
            background-color: var(--color-accent) !important;
            color: #FFFFFF !important;
            border-color: var(--color-transparent) !important;
            font-weight: 600 !important;
        }

        .stButton button[kind="primary"] *,
        .stButton button[kind="primary"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stFormSubmitButton"] button,
        [data-testid="stFormSubmitButton"] button *,
        [data-testid="stFormSubmitButton"] button div,
        [data-testid="stFormSubmitButton"] button p,
        [data-testid="stFormSubmitButton"] button span,
        [data-testid="stFormSubmitButton"] button [data-testid="stMarkdownContainer"] p {
            color: #FFFFFF !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        @media (hover: hover) {
            .stButton > button:hover {
                background-color: var(--color-paper-4) !important;
                border-color: var(--color-rule-strong) !important;
                transform: translateY(-1px);
            }

            .stButton > button[kind="primary"]:hover,
            [data-testid="stFormSubmitButton"] > button:hover {
                background-color: var(--color-accent-hover) !important;
                border-color: var(--color-transparent) !important;
                transform: translateY(-1px);
            }
        }

        .stButton > button:active,
        [data-testid="stFormSubmitButton"] > button:active {
            transform: translateY(1px) !important;
        }

        .stButton > button[kind="primary"]:active,
        [data-testid="stFormSubmitButton"] > button:active {
            background-color: var(--color-accent-active) !important;
        }

        .stButton > button:focus-visible,
        [data-testid="stFormSubmitButton"] > button:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: 2px !important;
        }

        .stButton > button:disabled,
        [data-testid="stFormSubmitButton"] > button:disabled {
            opacity: 0.52 !important;
            cursor: not-allowed !important;
            transform: none !important;
        }

        /* Popovers */
        [data-testid="stPopover"] > div > button {
            background-color: var(--color-paper-3) !important;
            border: 1px solid var(--color-field-edge) !important;
            color: var(--color-ink) !important;
            border-radius: var(--radius-md) !important;
            font-size: var(--text-sm) !important;
            height: 38px !important;
            transition: background-color var(--dur-micro) var(--ease-out) !important;
        }

        [data-testid="stPopover"] > div > button:focus-visible {
            outline: 2px solid var(--color-focus) !important;
            outline-offset: 2px !important;
        }

        [data-testid="stPopoverBody"] {
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-rule-strong) !important;
            border-radius: var(--radius-lg) !important;
            box-shadow: var(--shadow-float) !important;
            width: 276px !important;
            min-width: 260px !important;
            max-width: 92% !important;
        }

        /* Delete confirmation popover message */
        .wf-del-confirm-msg {
            background-color: rgba(245, 158, 11, 0.12);
            border: 1px solid rgba(245, 158, 11, 0.28);
            border-radius: var(--radius-md);
            padding: 10px 12px;
            margin-bottom: 12px;
            font-size: var(--text-sm);
            color: var(--color-ink);
            line-height: 1.4;
            word-break: break-word;
        }

        .wf-del-confirm-msg strong {
            color: var(--color-ink);
            font-weight: 600;
        }

        /* ============================================================
           11. DATAFRAMES, PROGRESS BARS, ALERTS & CHARTS
        ============================================================ */
        [data-testid="stDataFrame"],
        [data-testid="stDataFrameGlideDataEditor"] {
            border-radius: var(--radius-lg) !important;
            overflow: hidden;
            border: 1px solid var(--color-rule) !important;
        }

        .stProgress > div > div > div {
            background-color: var(--color-paper-3) !important;
            border-radius: var(--radius-full) !important;
            height: 8px !important;
        }

        .stProgress > div > div > div > div {
            background-color: var(--color-accent) !important;
            border-radius: var(--radius-full) !important;
        }

        [data-testid="stAlert"] {
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--color-rule) !important;
            background-color: var(--color-paper-2) !important;
            font-size: var(--text-sm) !important;
        }

        /* Plotly charts — smooth internal horizontal scroll so wide charts never clip outside the box */
        [data-testid="stPlotlyChart"] {
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-lg);
            padding: var(--space-sm) var(--space-md);
            overflow-x: auto !important;
            overflow-y: hidden !important;
        }

        .wf-chart-period {
            display: inline-flex;
            align-items: center;
            gap: var(--space-xs);
            padding: 4px 12px;
            margin: var(--space-xs) 0 var(--space-sm) 0;
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-full);
            font-size: var(--text-sm);
            font-weight: 600;
            color: var(--color-ink);
            font-variant-numeric: tabular-nums;
        }

        .scrollable-chart {
            overflow-x: auto;
            overflow-y: hidden;
            width: 100%;
            padding-bottom: var(--space-xs);
            border-radius: var(--radius-lg);
        }

        .scrollable-chart [data-testid="elementContainer"],
        .scrollable-chart [data-testid="stPlotlyChart"] {
            width: fit-content !important;
            min-width: fit-content !important;
            border: none;
            background-color: var(--color-transparent);
            padding: 0;
        }

        /* ============================================================
           12. CUSTOM COMPONENTS (Empty, Skeleton, Chips, Auth, Modals)
        ============================================================ */
        .wf-section-head {
            margin: var(--space-lg) 0 var(--space-sm) 0;
        }

        .wf-section-head h3 {
            margin: 0 !important;
        }

        .wf-section-sub {
            color: var(--color-ink-3);
            font-size: var(--text-sm);
            margin: var(--space-3xs) 0 0 0;
        }

        .wf-empty {
            text-align: center;
            padding: var(--space-xl) var(--space-lg);
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-lg);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: var(--space-xs);
        }

        .wf-empty-icon {
            width: 44px;
            height: 44px;
            border-radius: var(--radius-md);
            background-color: var(--color-paper-3);
            border: 1px solid var(--color-rule);
            color: var(--color-ink-2);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: var(--space-2xs);
        }

        .wf-empty-title {
            font-size: var(--text-md);
            font-weight: 600;
            color: var(--color-ink);
        }

        .wf-empty-body {
            font-size: var(--text-sm);
            color: var(--color-ink-3);
            max-width: 42ch;
        }

        .wf-skeleton {
            display: flex;
            flex-direction: column;
            gap: var(--space-sm);
            padding: var(--space-md);
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-lg);
        }

        .wf-skeleton-line {
            height: 14px;
            border-radius: var(--radius-sm);
            background-color: var(--color-paper-3);
        }

        .wf-chip {
            display: inline-flex;
            align-items: center;
            padding: 2px 10px;
            background-color: var(--color-paper-3);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-full);
            font-size: var(--text-xs);
            font-weight: 500;
            color: var(--color-ink-2);
        }

        .wf-chip--accent {
            background-color: var(--color-accent-low);
            border-color: var(--color-accent-mid);
            color: var(--color-accent);
        }

        .wf-chip--success {
            background-color: var(--color-success-low);
            border-color: var(--color-success-mid);
            color: var(--color-success);
        }

        .wf-chip--warning {
            background-color: var(--color-warning-low);
            border-color: var(--color-warning-mid);
            color: var(--color-warning);
        }

        .wf-chip--danger {
            background-color: var(--color-danger-low);
            border-color: var(--color-danger-mid);
            color: var(--color-danger);
        }

        .wf-cc-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 1px 7px;
            margin-right: 6px;
            background-color: rgba(245, 158, 11, 0.18);
            border: 1px solid rgba(245, 158, 11, 0.45);
            border-radius: var(--radius-full);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.04em;
            color: #FBBF24;
            vertical-align: middle;
        }

        /* Login / Auth surface */
        .auth-container {
            max-width: 420px;
            margin: 4vh auto var(--space-md);
            padding: var(--space-xl) var(--space-lg) var(--space-md);
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-modal);
        }

        .auth-logo {
            text-align: center;
            margin-bottom: var(--space-md);
            font-size: var(--text-xl);
            font-weight: 700;
            color: var(--color-ink);
            letter-spacing: -0.025em;
        }

        .auth-logo img {
            width: 64px;
            height: 64px;
            border-radius: var(--radius-lg);
            margin-bottom: var(--space-xs);
            border: 1px solid var(--color-rule);
        }

        /* Center notification popup */
        .center-popup {
            position: fixed !important;
            inset: 0 !important;
            pointer-events: none !important;
            display: grid !important;
            place-items: center !important;
            z-index: var(--z-toast) !important;
        }

        .center-popup > div {
            pointer-events: auto !important;
            width: min(90%, 420px) !important;
            background-color: var(--color-paper-2) !important;
            border: 1px solid var(--color-accent-mid) !important;
            box-shadow: var(--shadow-modal) !important;
            text-align: center !important;
            border-radius: var(--radius-xl) !important;
            padding: var(--space-xs) !important;
        }

        .center-popup [data-testid="stNotification"] {
            position: relative !important;
            transform: none !important;
            width: 100% !important;
            margin: 0 !important;
        }

        /* ============================================================
           13. COMMAND PALETTE (⌘K Quick Jump)
        ============================================================ */
        .wf-cmd-overlay {
            position: fixed;
            inset: 0;
            z-index: var(--z-tooltip);
            background-color: var(--color-backdrop);
            display: none;
            align-items: flex-start;
            justify-content: center;
            padding-top: 14vh;
        }

        .wf-cmd-overlay.is-open {
            display: flex;
            animation: wf-cmd-fade var(--dur-micro) var(--ease-out);
        }

        @keyframes wf-cmd-fade {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .wf-cmd-dialog {
            width: min(92%, 480px);
            background-color: var(--color-paper-2);
            border: 1px solid var(--color-rule-strong);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-modal);
            overflow: hidden;
            font-family: var(--font-body);
            animation: wf-cmd-pop var(--dur-short) var(--ease-out);
        }

        @keyframes wf-cmd-pop {
            from {
                opacity: 0;
                transform: translateY(-6px) scale(0.98);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        .wf-cmd-input-wrap {
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            padding: var(--space-sm) var(--space-md);
            border-bottom: 1px solid var(--color-rule);
        }

        .wf-cmd-input {
            flex: 1;
            border: none !important;
            background-color: var(--color-transparent) !important;
            box-shadow: none !important;
            color: var(--color-ink) !important;
            font-family: var(--font-body);
            font-size: var(--text-base);
            outline: none !important;
            padding: var(--space-2xs) 0;
        }

        .wf-cmd-list {
            max-height: 320px;
            overflow-y: auto;
            padding: var(--space-xs);
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .wf-cmd-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            padding: var(--space-xs) var(--space-sm);
            border-radius: var(--radius-md);
            border: none;
            background-color: var(--color-transparent);
            color: var(--color-ink-2);
            font-family: var(--font-body);
            font-size: var(--text-sm);
            font-weight: 500;
            text-align: left;
            cursor: pointer;
            transition:
                background-color var(--dur-press) var(--ease-out),
                color var(--dur-press) var(--ease-out);
        }

        .wf-cmd-item.is-selected,
        .wf-cmd-item:hover {
            background-color: var(--color-accent-low);
            color: var(--color-ink);
        }

        .wf-cmd-item:focus-visible {
            outline: 2px solid var(--color-focus);
            outline-offset: -2px;
        }

        .wf-cmd-hint {
            font-size: var(--text-xs);
            color: var(--color-ink-3);
        }

        /* ============================================================
           14. MOBILE RESPONSIVE + BOTTOM NAVIGATION BAR (< 60rem)
        ============================================================ */
        .wf-bottom-nav {
            display: none;
        }

        @media (max-width: 59.99rem) {
            .main .block-container,
            [data-testid="stMainBlockContainer"] {
                padding: var(--space-sm) var(--space-md) 88px !important;
            }

            .wf-topbar {
                margin: calc(var(--space-sm) * -1) calc(var(--space-md) * -1) var(--space-md);
                padding: 0 var(--space-md);
            }

            .wf-cmd-trigger .wf-kbd {
                display: none;
            }

            .wf-pin-btn {
                display: none !important;
            }

            .wf-bottom-nav {
                display: grid;
                grid-template-columns: repeat(5, minmax(0, 1fr));
                position: fixed;
                left: var(--space-sm);
                right: var(--space-sm);
                bottom: max(var(--space-xs), env(safe-area-inset-bottom));
                height: 60px;
                background-color: var(--color-paper-2);
                border: 1px solid var(--color-rule-strong);
                border-radius: var(--radius-xl);
                box-shadow: var(--shadow-float);
                z-index: var(--z-sticky-nav);
                padding: 4px;
            }

            .wf-bottom-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 3px;
                border: none;
                background-color: var(--color-transparent);
                color: var(--color-ink-3);
                border-radius: var(--radius-lg);
                font-family: var(--font-body);
                font-size: 11px;
                font-weight: 500;
                cursor: pointer;
                transition:
                    background-color var(--dur-micro) var(--ease-out),
                    color var(--dur-micro) var(--ease-out);
            }

            .wf-bottom-item.is-active {
                background-color: var(--color-accent-low);
                color: var(--color-accent);
                font-weight: 600;
            }

            .wf-bottom-item:focus-visible {
                outline: 2px solid var(--color-focus);
                outline-offset: -2px;
            }
        }

        /* ============================================================
           15. REDUCED MOTION (Hallmark Floor #7)
        ============================================================ */
        @media (prefers-reduced-motion: reduce) {
            html, body,
            [data-testid="stApp"],
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"],
            .main {
                scroll-behavior: auto !important;
            }

            [data-testid="stMainBlockContainer"] > div,
            .wf-cmd-overlay.is-open,
            .wf-cmd-dialog {
                animation: none !important;
            }

            *, *::before, *::after {
                transition-duration: 0.01ms !important;
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
