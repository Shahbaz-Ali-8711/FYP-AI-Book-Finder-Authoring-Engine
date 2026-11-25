import streamlit as st
import textwrap
from database.db_handler import init_db
from utils.helpers import init_session_state
from utils.styles import (
    inject_global_css, PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT,
    SECONDARY, ACCENT, BUTTON_GRADIENT, BORDER, TEXT_PRIMARY,
    TEXT_SECONDARY, render_html
)
from views.landing_view import render_landing_page
from views.auth_view import render_auth_page
from views.dashboard_view import render_dashboard
from views.scanner_view import render_scanner
from views.search_view import render_search
from views.creator_view import render_creator_view
from views.chatbot_view import render_chatbot
from views.profile_view import render_profile
from views.admin_view import render_admin_panel
from views.reader_view import render_reader_view
from views.platform_view import render_platform_view

st.set_page_config(
    page_title="PEN2PUBLISH AI · Autonomous Authoring & Book Discovery Engine",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize Database, State & Global CSS
init_db()
init_session_state()
inject_global_css()

st.markdown("""
<style>
    [data-testid="collapsedControl"], [data-testid="stSidebar"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 5 Functional Navigation Links: Home, Reader Hub, Writer Studio, Core Engines, About & Team
NAV_ITEMS = [
    ("Home", "home", "landing"),
    ("Reader Hub", "reader", "reader"),
    ("Writer Studio", "creator", "creator"),
    ("Core Engines", "engines", "landing"),
    ("About & Team", "about", "landing"),
]


def _render_top_nav():
    username = st.session_state.get("username", "Author")
    user_role = st.session_state.get("user_role")
    current_section = st.session_state.get("nav_section", "home")
    current_page = st.session_state.get("nav_page", "landing")

    # Clean, Minimal Header Banner without duplicate badges
    render_html(f"""
    <div style="background: rgba(250, 250, 245, 0.98); backdrop-filter: blur(20px);
                border-bottom: 1.5px solid #E5E5DC; padding: 0.85rem 2rem;
                display: flex; align-items: center; justify-content: space-between;
                border-radius: 0 0 18px 18px; box-shadow: 0 4px 20px -2px rgba(26, 26, 26, 0.05);
                margin-bottom: 1.25rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.6rem;">📚</span>
            <span style="font-size: 1.35rem; font-weight: 900; color: #1A1A1A; letter-spacing: -0.025em;">
                PEN2PUBLISH <span style="color: #046A38;">AI</span>
            </span>
            <span style="font-size: 0.84rem; color: #737373; font-weight: 600; margin-left: 0.4rem;">
                · Autonomous Authoring & Book Discovery Engine
            </span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="background: rgba(227, 66, 52, 0.08); color: #E34234; border: 1px solid rgba(227, 66, 52, 0.28); font-size: 0.72rem; font-weight: 800; padding: 0.2rem 0.6rem; border-radius: 9999px;">
                ⚡ Groq LPU
            </span>
            <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28); font-size: 0.72rem; font-weight: 800; padding: 0.2rem 0.6rem; border-radius: 9999px;">
                👁️ Gemini Multimodal
            </span>
        </div>
    </div>
    """)

    # 5 Functional Navigation Links + Right Auth Trigger
    nav_cols = st.columns([1.0, 1.3, 1.4, 1.3, 1.3, 2.1], gap="small")

    for i, (label, section_key, page_target) in enumerate(NAV_ITEMS):
        with nav_cols[i]:
            if page_target == "landing":
                is_active = (current_page == "landing" and current_section == section_key)
            else:
                is_active = (current_page == page_target)
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_btn_{section_key}", use_container_width=True, type=btn_type):
                st.session_state["nav_page"] = page_target
                st.session_state["nav_section"] = section_key
                st.session_state["show_login"] = False
                st.rerun()

    with nav_cols[-1]:
        if user_role == "admin":
            # Admin Exclusive Controls (Plenty of room, zero text truncation)
            adm_c1, adm_c2 = st.columns([1.2, 1.0], gap="small")
            with adm_c1:
                is_admin_active = (current_page == "admin")
                if st.button("⚙️ Admin Panel", key="nav_admin_panel_btn", use_container_width=True,
                             type="primary" if is_admin_active else "secondary"):
                    st.session_state["nav_page"] = "admin"
                    st.session_state["show_login"] = False
                    st.rerun()
            with adm_c2:
                if st.button("🚪 Sign Out", key="nav_admin_exit_btn", use_container_width=True):
                    _logout_user()
                    st.rerun()

        elif st.session_state.get("logged_in") or st.session_state.get("admin_bypass"):
            # Registered Author Controls (Cleanly displays Dashboard and Sign Out)
            usr_c1, usr_c2 = st.columns([1.2, 1.0], gap="small")
            with usr_c1:
                is_dash_active = (current_page == "dashboard")
                display_name = username if len(username) <= 10 else f"{username[:9]}…"
                if st.button(f"📊 Dashboard", key="nav_user_dash_btn", use_container_width=True,
                             type="primary" if is_dash_active else "secondary"):
                    st.session_state["nav_page"] = "dashboard"
                    st.session_state["show_login"] = False
                    st.rerun()
            with usr_c2:
                if st.button("🚪 Sign Out", key="nav_user_logout_btn", use_container_width=True):
                    _logout_user()
                    st.rerun()

        else:
            # Unauthenticated User CTA in Prominent Vermilion
            if st.button("Sign In / Portal →", key="nav_portal_signin_btn", use_container_width=True, type="primary"):
                st.session_state["show_login"] = True
                st.rerun()

    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)


def _logout_user():
    st.session_state["is_admin"] = False
    st.session_state["user_role"] = None
    st.session_state["admin_bypass"] = False
    st.session_state["logged_in"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = ""
    st.session_state["nav_page"] = "landing"
    st.session_state["nav_section"] = "home"
    st.session_state["show_login"] = False


def _render_back_to_home():
    col_back, col_title, _ = st.columns([1.4, 6.6, 1])
    with col_back:
        if st.button("← Back to Hub", key="back_to_home_main_btn", use_container_width=True):
            st.session_state["nav_page"] = "dashboard" if st.session_state.get("logged_in") else "landing"
            st.session_state["nav_section"] = "home"
            st.rerun()


# --- UNIFIED ROUTING FLOW ---
if not st.session_state.get("logged_in") and st.session_state.get("show_login"):
    _render_top_nav()
    col_back, _, _ = st.columns([1.2, 7, 1])
    with col_back:
        if st.button("← Back to Overview", key="back_from_login_screen_btn"):
            st.session_state["show_login"] = False
            st.rerun()
    render_auth_page()
else:
    _render_top_nav()

    page = st.session_state.get("nav_page", "landing")
    user_role = st.session_state.get("user_role")

    # Strict Role Guard: Only authenticated administrators can access the admin view
    if page == "admin":
        if user_role == "admin":
            render_admin_panel()
        else:
            st.session_state["nav_page"] = "landing"
            st.rerun()
    elif page == "landing":
        render_landing_page()
    elif page in ("dashboard", "scanner", "search", "creator", "chatbot", "profile", "reader", "platform"):
        # Protected feature routes: require login or admin bypass (or default author session)
        if st.session_state.get("logged_in") or st.session_state.get("admin_bypass") or st.session_state.get("username"):
            _render_back_to_home()
            if page == "dashboard":
                render_dashboard()
            elif page == "scanner":
                render_scanner()
            elif page == "search":
                render_search()
            elif page == "creator":
                render_creator_view()
            elif page == "chatbot":
                render_chatbot()
            elif page == "profile":
                render_profile()
            elif page == "reader":
                render_reader_view()
            elif page == "platform":
                render_platform_view()
        else:
            st.session_state["show_login"] = True
            st.rerun()
    else:
        render_landing_page()
