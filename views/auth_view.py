"""
views/auth_view.py
==================
Modular Authentication & Governance Portal for Pen2Publish AI.

MULTI-PORT DEPLOYMENT READINESS:
--------------------------------
This module exports two decoupled entry points:
  1. `render_author_auth()`: Mountable independently on standard public ports (e.g., :8501).
  2. `render_admin_auth()`: Mountable independently on isolated management ports (e.g., :8502
     or behind a VPC/VPN reverse-proxy) without exposing author endpoints.
  3. `render_auth_page()`: Unified dual-portal selector for single-port deployments.
"""

import streamlit as st
from database.auth import login_user, register_user
from database import admin_db
from utils.styles import (
    PRIMARY, PRIMARY_DARK, BUTTON_GRADIENT,
    HERO_GRADIENT, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, render_html
)


def render_auth_page():
    """
    Unified entry point providing a modern selector between Author Portal and Admin Governance Console.
    """
    # Clean top brand presentation
    render_html(f"""
    <div style="max-width: 580px; margin: 1.5rem auto 1rem auto;
                background: #FFFFFF;
                border-radius: 24px; padding: 2.5rem; text-align: center;
                box-shadow: 0 15px 35px -10px rgba(26, 26, 26, 0.06);
                border: 1.5px solid #E5E5DC;">
        <div style="font-size: 2.8rem; margin-bottom: 0.4rem;">📚</div>
        <div style="font-size: 1.9rem; font-weight: 900; color: #1A1A1A; letter-spacing: -0.025em;">
            PEN2PUBLISH <span style="color: #046A38;">AI</span>
        </div>
        <div style="font-size: 0.92rem; color: #4A4A4A; margin-top: 0.5rem; line-height: 1.6;">
            Select your portal to authenticate your session or provision a new authoring workspace.
        </div>
    </div>
    """)

    auth_tab = st.radio(
        "Select Portal Mode:",
        ["👤 Author Portal", "⚙️ Admin Governance Portal"],
        horizontal=True,
        key="auth_portal_mode_selector"
    )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    if auth_tab == "👤 Author Portal":
        render_author_auth()
    else:
        render_admin_auth()


# ==============================================================================
# AUTHOR PORTAL AUTHENTICATION (Standalone Mountable on Port 8501)
# ==============================================================================
def render_author_auth():
    """
    Author authentication view containing Sign In and Account Registration.
    Can be run independently on a public port.
    """
    tab_signin, tab_signup = st.tabs(["🔐 Author Sign In", "✨ Create Author Account"])

    with tab_signin:
        _render_author_login_form()

    with tab_signup:
        _render_author_signup_form()


def _render_author_login_form():
    col_left, col_center, col_right = st.columns([1, 2.5, 1])
    with col_center:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-weight: 800; font-size: 1.25rem; color: #1A1A1A;">Author Sign In</div>
            <div style="font-size: 0.85rem; color: #5C5C5C;">Access your manuscripts, character bibles, and exports</div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username or Pen Name", key="author_login_uname", placeholder="e.g. jennifer_writer")
        password = st.text_input("Password", type="password", key="author_login_pwd", placeholder="••••••••••••")

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Sign In to Author Studio", key="btn_author_signin", use_container_width=True, type="primary"):
            if username and password:
                try:
                    success, result = login_user(username, password)
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = result
                        st.session_state["username"] = username
                        st.session_state["user_role"] = "user"
                        st.session_state["is_admin"] = False
                        st.session_state["show_login"] = False
                        st.session_state["nav_page"] = "dashboard"
                        st.rerun()
                    else:
                        st.error(result)
                except Exception as e:
                    st.error(f"Sign-in error: {str(e)}")
            else:
                st.warning("Please provide both username and password")


def _render_author_signup_form():
    col_left, col_center, col_right = st.columns([1, 2.5, 1])
    with col_center:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-weight: 800; font-size: 1.25rem; color: #1A1A1A;">Create Author Account</div>
            <div style="font-size: 0.85rem; color: #5C5C5C;">Join thousands of authors publishing with Gemini AI</div>
        </div>
        """, unsafe_allow_html=True)

        new_username = st.text_input("Preferred Username / Pen Name", key="author_signup_uname", placeholder="e.g. alex_rivera")
        new_email = st.text_input("Email Address", key="author_signup_email", placeholder="author@domain.com")
        new_password = st.text_input("Create Password", type="password", key="author_signup_pwd", placeholder="••••••••••••")

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Create Author Account", key="btn_author_signup", use_container_width=True, type="primary"):
            if new_username and new_email and new_password:
                try:
                    success, msg = register_user(new_username, new_email, new_password)
                    if success:
                        st.success("✅ Account created successfully! Please switch to 'Author Sign In' to log in.")
                    else:
                        st.error(msg)
                except Exception as e:
                    st.error(f"Registration error: {str(e)}")
            else:
                st.warning("Please complete all fields to register")


# ==============================================================================
# ADMIN GOVERNANCE AUTHENTICATION (Standalone Mountable on Port 8502)
# ==============================================================================
def render_admin_auth():
    """
    Isolated Administrator Governance Console authentication.
    Can be run independently on an internal port without exposing author signups.
    """
    col_left, col_center, col_right = st.columns([1, 2.5, 1])
    with col_center:
        adm_hdr_html = f"""
        <div style="background: #FFFFFF;
                    border: 1.5px solid #E5E5DC;
                    border-radius: 18px; padding: 1.75rem 1.5rem; text-align: center; color: #1A1A1A;
                    margin-bottom: 1.25rem; box-shadow: 0 6px 18px rgba(26, 26, 26, 0.04);">
            <div style="font-size: 2.2rem; margin-bottom: 0.35rem;">🛡️</div>
            <div style="font-size: 1.25rem; font-weight: 900; color: #046A38; letter-spacing: -0.01em;">
                System Governance Console
            </div>
            <div style="font-size: 0.84rem; color: #5C5C5C; margin-top: 0.3rem; line-height: 1.5;">
                Restricted authentication for platform infrastructure, CMS control & user administration
            </div>
        </div>
        """
        render_html(adm_hdr_html)

        admin_user = st.text_input("Administrator Username", key="admin_auth_user_fld", placeholder="admin")
        admin_pass = st.text_input("Administrator Password", type="password", key="admin_auth_pass_fld", placeholder="••••••••")

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Authenticate Admin Console", key="btn_admin_signin", use_container_width=True, type="primary"):
            if admin_user and admin_pass:
                try:
                    success, result = admin_db.login_admin(admin_user, admin_pass)
                    if success:
                        st.session_state["is_admin"] = True
                        st.session_state["user_role"] = "admin"
                        st.session_state["admin_bypass"] = True
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = admin_user
                        st.session_state["show_login"] = False
                        st.session_state["nav_page"] = "admin"
                        st.rerun()
                    else:
                        st.error(result)
                except Exception as e:
                    st.error(f"Admin authentication error: {str(e)}")
            else:
                st.warning("Please enter administrator credentials")

        st.markdown("""
        <div style="text-align: center; margin-top: 1.25rem; font-size: 0.8rem; color: #737373;">
            Default Super Admin: <strong style="color: #046A38;">admin</strong> / <strong style="color: #1A1A1A;">admin123</strong>
        </div>
        """, unsafe_allow_html=True)
