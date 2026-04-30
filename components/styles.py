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
        
        /* Secondary / Navigation Buttons in Sidebar */
        [data-testid="stSidebar"] .stButton > button {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            text-align: left !important;
            padding: 12px 18px !important;
            margin-bottom: 4px !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(59, 130, 246, 0.1) !important;
            border-color: rgba(59, 130, 246, 0.3) !important;
        }

        /* Active Page Button Highlight */
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
        }

        .stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 15px rgba(37, 99, 235, 0.4) !important;
        }

        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(30, 41, 59, 0.3);
            border-radius: 12px;
            padding: 8px 18px;
            color: #94a3b8;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #3b82f6 !important;
            color: white !important;
        }

        /* Mobile Sidebar Optimization */
        @media (max-width: 768px) {
            [data-testid="stSidebar"] {
                width: 100% !important;
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
        </style>
    """, unsafe_allow_html=True)
