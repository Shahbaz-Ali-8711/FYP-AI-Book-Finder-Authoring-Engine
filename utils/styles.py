import streamlit as st

# ==============================================================================
# MANDATORY DESIGN SYSTEM & COLOR PALETTE
# Warm Ivory (#FAFAF5) · Emerald Green (#046A38) · Vermilion (#E34234) · Dark Slate (#1A1A1A)
# ==============================================================================
PRIMARY = "#046A38"                     # Deep Luxury Emerald Green
PRIMARY_DARK = "#03522B"                # Forest Emerald Dark
PRIMARY_LIGHT = "#0F5257"               # Deep Pine / Teal Emerald
PRIMARY_TINT = "rgba(4, 106, 56, 0.08)"
EMERALD = "#046A38"
EMERALD_DARK = "#03522B"
EMERALD_LIGHT = "#0F5257"
EMERALD_TINT = "rgba(4, 106, 56, 0.08)"
EMERALD_BORDER = "rgba(4, 106, 56, 0.28)"

ACCENT = "#E34234"                      # Vibrant Vermilion (CTA / Actions)
SECONDARY_ACCENT = "#E34234"
VERMILION = "#E34234"
VERMILION_DARK = "#D9381E"
VERMILION_HOVER = "#C72E20"
VERMILION_TINT = "rgba(227, 66, 52, 0.08)"

BG = "#FAFAF5"                          # Soft Clean Warm Ivory Background
SECONDARY_BG = "#F5F5ED"                # Warm Ivory Secondary Surface
CARD_BG = "#FFFFFF"                     # Pure White Card Surface for optimal contrast
CARD_BG_SECONDARY = "#FAF8F2"           # Soft Ivory Neutral Light
CARD_BG_WARM = "#FAF8F2"

TEXT_PRIMARY = "#1A1A1A"                # Ultra-High Contrast Dark Slate
TEXT_SECONDARY = "#4A4A4A"              # Slate Gray Secondary
TEXT_MUTED = "#737373"                  # Muted Caption Gray

BORDER = "#E5E5DC"                      # Warm Ivory Subtle Border
BORDER_STRONG = "#D4D4CA"               # Medium Slate / Warm Border
BORDER_EMERALD = "rgba(4, 106, 56, 0.28)"
BORDER_VERMILION = "rgba(227, 66, 52, 0.35)"

HERO_GRADIENT = "linear-gradient(135deg, #FAFAF5 0%, #FFFFFF 50%, #F5F5ED 100%)"
BUTTON_GRADIENT = "linear-gradient(135deg, #E34234 0%, #D9381E 100%)"
BUTTON_HOVER_GRADIENT = "linear-gradient(135deg, #F04E3E 0%, #E34234 100%)"
EMERALD_GRADIENT = "linear-gradient(135deg, #046A38 0%, #0F5257 100%)"
HEADER_BANNER_GRADIENT = "linear-gradient(135deg, #046A38 0%, #0F5257 100%)"
CARD_GRADIENT = "linear-gradient(135deg, #FFFFFF 0%, #FAF8F2 100%)"
ACCENT_GRADIENT = "linear-gradient(135deg, #E34234 0%, #D9381E 100%)"
SECONDARY = "#1A1A1A"


def inject_global_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {{
        --primary: {PRIMARY};
        --primary-dark: {PRIMARY_DARK};
        --primary-light: {PRIMARY_LIGHT};
        --secondary: {SECONDARY};
        --accent: {ACCENT};
        --bg: {BG};
        --card-bg: {CARD_BG};
        --text-primary: {TEXT_PRIMARY};
        --text-secondary: {TEXT_SECONDARY};
        --border: {BORDER};
    }}

    * {{
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        box-sizing: border-box;
    }}

    /* Global App Background - Warm Ivory Soft Theme */
    .stApp {{
        background: radial-gradient(circle at 12% 10%, rgba(4, 106, 56, 0.04) 0%, transparent 45%),
                    radial-gradient(circle at 88% 85%, rgba(227, 66, 52, 0.035) 0%, transparent 45%),
                    {BG} !important;
        color: {TEXT_PRIMARY} !important;
    }}

    /* Hide Default Streamlit Chrome */
    #MainMenu, footer {{
        visibility: hidden;
        height: 0;
    }}

    header[data-testid="stHeader"] {{
        background: transparent !important;
        display: none !important;
    }}

    [data-testid="collapsedControl"], [data-testid="stSidebar"] {{
        display: none !important;
    }}

    /* Block Padding Optimization */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1320px !important;
    }}

    /* Typography - Dark Slate for optimal readability */
    h1, h2, h3, h4, h5, h6 {{
        color: {TEXT_PRIMARY} !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em;
    }}

    p, span, label, div {{
        color: {TEXT_PRIMARY};
    }}

    /* Clean Card Utilities */
    .white-glass-card, .ivory-glass-card {{
        background: #FFFFFF !important;
        border: 1.5px solid #E5E5DC !important;
        box-shadow: 0 15px 35px -12px rgba(26, 26, 26, 0.06), 0 4px 12px -2px rgba(26, 26, 26, 0.02) !important;
        border-radius: 20px !important;
    }}

    /* Code blocks reset */
    .stMarkdown pre, .stMarkdown code, [data-testid="stCodeBlock"], [data-testid="stCopyButton"] {{
        background: #F5F5ED !important;
        border: 1px solid #E5E5DC !important;
        color: {TEXT_PRIMARY} !important;
        box-shadow: none !important;
    }}

    /* NO TEXT TRUNCATION / NO ELLIPSIS BUTTON STYLING */
    .stButton > button {{
        white-space: nowrap !important;
        text-overflow: clip !important;
        overflow: visible !important;
        min-width: max-content !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 1.15rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em !important;
        border-radius: 12px !important;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 8px rgba(26, 26, 26, 0.04) !important;
        cursor: pointer !important;
    }}

    /* Vibrant Vermilion Primary Button Styling with translateY(-2px) */
    .stButton > button, .stButton > button[kind="primary"] {{
        background: {BUTTON_GRADIENT} !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        box-shadow: 0 4px 14px -2px rgba(227, 66, 52, 0.38), 0 2px 6px -1px rgba(26, 26, 26, 0.05) !important;
    }}

    .stButton > button:hover, .stButton > button[kind="primary"]:hover {{
        background: {BUTTON_HOVER_GRADIENT} !important;
        color: #FFFFFF !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 24px -4px rgba(227, 66, 52, 0.48), 0 4px 10px -2px rgba(26, 26, 26, 0.08) !important;
    }}

    .stButton > button:active, .stButton > button[kind="primary"]:active {{
        transform: translateY(0) !important;
        box-shadow: 0 2px 6px rgba(227, 66, 52, 0.35) !important;
    }}

    /* Secondary Buttons - Warm Ivory with Emerald Green Border */
    .stButton > button[kind="secondary"] {{
        background: #FFFFFF !important;
        color: {EMERALD} !important;
        border: 1.5px solid {EMERALD} !important;
        box-shadow: 0 2px 6px rgba(4, 106, 56, 0.06) !important;
    }}

    .stButton > button[kind="secondary"]:hover {{
        background: #F0F8F4 !important;
        border-color: {EMERALD} !important;
        color: {EMERALD} !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px -2px rgba(4, 106, 56, 0.16) !important;
    }}

    /* Top Navigation Action Buttons Container */
    .nav-action-btn button {{
        padding: 0.6rem 1.4rem !important;
        font-weight: 800 !important;
    }}

    /* Inputs, Textareas, Selectboxes - Crisp Warm Ivory / White */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {{
        background: #FFFFFF !important;
        color: {TEXT_PRIMARY} !important;
        border: 1.5px solid #D4D4CA !important;
        border-radius: 12px !important;
        padding: 0.65rem 0.9rem !important;
        font-size: 0.92rem !important;
        box-shadow: 0 1px 3px rgba(26, 26, 26, 0.04) !important;
        transition: all 0.2s ease !important;
    }}

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {EMERALD} !important;
        box-shadow: 0 0 0 3px rgba(4, 106, 56, 0.16) !important;
        background: #FFFFFF !important;
    }}

    /* Tabs Styling - Warm Ivory Container with Emerald Active Pill */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: #EFEFE7;
        padding: 0.35rem;
        border-radius: 14px;
        border: 1px solid #E5E5DC;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px !important;
        padding: 0.5rem 1.25rem !important;
        color: {TEXT_SECONDARY} !important;
        font-weight: 700 !important;
        transition: all 0.2s ease;
        border: none !important;
        white-space: nowrap !important;
    }}

    .stTabs [aria-selected="true"] {{
        background: #FFFFFF !important;
        color: {EMERALD} !important;
        box-shadow: 0 4px 12px rgba(4, 106, 56, 0.12) !important;
    }}

    /* Expanders - Warm Clean Accordion */
    div[data-testid="stExpander"] {{
        background: #FFFFFF;
        border: 1.5px solid #E5E5DC;
        border-radius: 14px;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 8px rgba(26, 26, 26, 0.03);
        transition: all 0.2s ease;
    }}

    div[data-testid="stExpander"]:hover {{
        border-color: {EMERALD};
        box-shadow: 0 6px 16px -4px rgba(4, 106, 56, 0.1);
    }}

    /* Metrics - Dark Slate with Emerald Highlight */
    [data-testid="stMetricValue"] {{
        color: {TEXT_PRIMARY} !important;
        font-weight: 900 !important;
    }}

    [data-testid="stMetricLabel"] {{
        color: {TEXT_SECONDARY} !important;
        font-weight: 700 !important;
    }}

    /* Progress bar custom styling - Vermilion to Emerald */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, #E34234 0%, #046A38 100%) !important;
        border-radius: 8px;
    }}

    /* Minimal Warm Ivory Scrollbars */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: #F5F5ED;
    }}
    ::-webkit-scrollbar-thumb {{
        background: #D4D4CA;
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #046A38;
    }}
    </style>
    """, unsafe_allow_html=True)


def section_header(title, subtitle=""):
    st.markdown(f"""
    <div style="text-align: center; margin: 2rem 0 1.5rem 0;">
        <div style="font-size: 2.2rem; font-weight: 900; color: {TEXT_PRIMARY}; letter-spacing: -0.025em; margin-bottom: 0.5rem;">
            {title}
        </div>
        <div style="font-size: 1rem; color: {TEXT_SECONDARY}; max-width: 640px; margin: 0 auto; line-height: 1.6;">
            {subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)


def feature_card(icon, title, description):
    return f"""
    <div style="background: #FFFFFF; border-radius: 18px; padding: 1.75rem; border: 1.5px solid #E5E5DC;
                box-shadow: 0 10px 25px -5px rgba(26, 26, 26, 0.05); transition: all 0.3s ease; height: 100%;">
        <div style="font-size: 2.4rem; margin-bottom: 0.75rem;">{icon}</div>
        <div style="font-size: 1.2rem; font-weight: 800; color: #046A38; margin-bottom: 0.5rem;">
            {title}
        </div>
        <div style="font-size: 0.9rem; color: {TEXT_SECONDARY}; line-height: 1.6;">
            {description}
        </div>
    </div>
    """


def stat_card(number, label):
    return f"""
    <div style="background: #FFFFFF; border-radius: 16px; padding: 1.5rem;
                text-align: center; border: 1.5px solid #E5E5DC; box-shadow: 0 6px 18px rgba(26, 26, 26, 0.04);">
        <div style="font-size: 2.2rem; font-weight: 900; color: #E34234;">
            {number}
        </div>
        <div style="font-size: 0.85rem; color: {TEXT_SECONDARY}; font-weight: 700; margin-top: 0.25rem;">
            {label}
        </div>
    </div>
    """


def clean_html(html_str: str) -> str:
    """Strips all leading and trailing whitespace from every line and eliminates empty lines.
    Guarantees that Streamlit markdown will NEVER interpret any HTML line as a 4-space code block.
    """
    return "\n".join(line.strip() for line in html_str.strip().splitlines() if line.strip())


def render_html(html_str: str):
    """Safely renders HTML markup without markdown code block interpretation or copy button leaks."""
    cleaned = clean_html(html_str)
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)
