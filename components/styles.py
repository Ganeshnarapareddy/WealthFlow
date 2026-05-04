import streamlit as st

def apply_styles():
    """Premium Glassmorphism Theme - Mobile Optimized"""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

        /* Base Settings */
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Outfit', sans-serif !important;
            background: linear-gradient(135deg, #0f172a 0%, #020617 100%);
            color: #f8fafc;
        }

        /* Sidebar Logo */
        [data-testid="stSidebar"] h1 {
            background: linear-gradient(to right, #ffffff, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -1px;
        }

        /* Mobile Container Fixes */
        .main .block-container {
            padding: 1.5rem 1rem !important;
            max-width: 100% !important;
        }

        /* Glass Cards */
        div[data-testid="metric-container"], [data-testid="stExpander"] {
            background: rgba(30, 41, 59, 0.4) !important;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 18px !important;
            padding: 15px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        div[data-testid="metric-container"]:hover {
            border-color: rgba(59, 130, 246, 0.4) !important;
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }

        /* Premium Headers */
        .main-header {
            font-size: clamp(1.8rem, 6vw, 3rem) !important;
            font-weight: 800 !important;
            background: linear-gradient(to right, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1.5rem !important;
        }

        /* Section Titles */
        h3, .section-header {
            font-weight: 600 !important;
            color: #cbd5e1 !important;
            border-left: 4px solid #3b82f6;
            padding-left: 12px;
            margin-top: 1.5rem !important;
        }

        /* Form Controls */
        input, select, textarea, [data-baseweb="select"] {
            background-color: rgba(15, 23, 42, 0.6) !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
        }

        /* Buttons - Modern Gradient */
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3) !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
            background-image: linear-gradient(180deg, #0f172a 0%, #020617 100%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
            width: 300px !important;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding-top: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }

        /* Sidebar Logo & Branding */
        .sidebar-branding {
            text-align: center;
            padding: 1.5rem 0;
            margin-bottom: 1rem;
        }
        .sidebar-branding img {
            width: 80px;
            margin-bottom: 10px;
            mix-blend-mode: screen;
            border-radius: 16px;
            filter: drop-shadow(0 0 10px rgba(59, 130, 246, 0.5));
        }
        .sidebar-title {
            font-size: 1.8rem !important;
            font-weight: 800 !important;
            background: linear-gradient(to right, #ffffff, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0 !important;
        }
        .sidebar-subtitle {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: -5px;
            font-style: italic;
        }

        /* Sidebar User Info */
        .sidebar-user-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .sidebar-welcome {
            font-size: 0.85rem;
            color: #94a3b8;
        }
        .sidebar-username {
            font-weight: 600;
            color: #60a5fa;
            display: block;
        }

        /* Navigation Buttons in Sidebar */
        [data-testid="stSidebar"] .stButton > button {
            background: transparent !important;
            border: 1px solid transparent !important;
            text-align: left !important;
            padding: 10px 15px !important;
            margin-bottom: 4px !important;
            box-shadow: none !important;
            color: #94a3b8 !important;
            justify-content: flex-start !important;
            font-weight: 500 !important;
            border-radius: 10px !important;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(59, 130, 246, 0.1) !important;
            color: #ffffff !important;
            border-color: rgba(59, 130, 246, 0.2) !important;
            transform: none !important;
        }

        /* Active Navigation Button */
        [data-testid="stSidebar"] .nav-active button {
            background: rgba(59, 130, 246, 0.15) !important;
            color: #ffffff !important;
            border-left: 4px solid #3b82f6 !important;
            border-radius: 4px 10px 10px 4px !important;
            font-weight: 700 !important;
        }

        /* Profile & Logout at Bottom */
        .sidebar-footer {
            margin-top: auto;
            padding-top: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        /* Hide Default Elements */
        [data-testid="stSidebarNav"] { display: none !important; }
        
        /* Mobile Sidebar Optimization */
        @media (max-width: 768px) {
            [data-testid="stSidebar"] {
                width: 85vw !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.4rem !important;
            }
        }

        /* Progress Bars */
        .stProgress > div > div > div > div {
            background-color: #3b82f6 !important;
            border-radius: 10px;
        }

        /* Center Popup Styles - Robust Centering */
        .center-popup {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
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
            max-width: 450px !important;
            background: rgba(15, 23, 42, 0.98) !important;
            backdrop-filter: blur(25px) !important;
            border: 2px solid #3b82f6 !important;
            box-shadow: 0 0 120px rgba(0,0,0,0.95) !important;
            text-align: center !important;
            border-radius: 24px !important;
            padding: 10px !important;
        }
        
        /* Ensure the inner Streamlit notification doesn't have its own fixed positioning */
        .center-popup [data-testid="stNotification"] {
            position: relative !important;
            top: 0 !important;
            left: 0 !important;
            transform: none !important;
            width: 100% !important;
            margin: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
