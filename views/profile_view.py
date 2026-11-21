import streamlit as st
from config.pricing import get_user_tier, get_tier_limits, PRICING_TIERS
from utils.styles import (
    HERO_GRADIENT, PRIMARY, PRIMARY_DARK, ACCENT, BORDER,
    BUTTON_GRADIENT, TEXT_PRIMARY, TEXT_SECONDARY,
    render_html
)


def render_profile():
    username = st.session_state.get("username", "Author")
    user_tier = get_user_tier()
    limits = get_tier_limits(user_tier)

    # Clean White Profile Header Card with Royal Blue Avatar
    render_html(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0;
                border-radius: 20px; padding: 2.5rem; color: #0F172A;
                margin-bottom: 2rem; box-shadow: 0 10px 30px -10px rgba(15, 23, 42, 0.08);">
        <div style="display: flex; align-items: center; gap: 1.5rem;">
            <div style="width: 76px; height: 76px; border-radius: 50%;
                        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
                        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
                        display: flex; align-items: center; justify-content: center;
                        font-size: 2.2rem; font-weight: 900; color: #FFFFFF; border: 3px solid #EFF6FF;">
                {username[0].upper() if username else 'U'}
            </div>
            <div>
                <div style="font-size: 2rem; font-weight: 900; color: #0F172A; letter-spacing: -0.02em;">{username}</div>
                <div style="font-size: 0.92rem; color: #2563EB; font-weight: 700; margin-top: 0.2rem; letter-spacing: 0.04em;">
                    {user_tier.upper()} AUTHOR TIER · Registered Member
                </div>
            </div>
        </div>
    </div>
    """)

    st.subheader("Your Quotas & Operational Limits")

    col1, col2, col3 = st.columns(3)

    with col1:
        ai_limit = limits["daily_ai_calls"]
        ai_display = "Unlimited" if ai_limit == -1 else str(ai_limit)
        render_html(f"""
        <div style="background: #FFFFFF;
                    border-radius: 18px; padding: 1.75rem; text-align: center;
                    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04); border: 1.5px solid #E2E8F0;">
            <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🤖</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #0F172A;">{ai_display}</div>
            <div style="font-size: 0.85rem; color: {TEXT_SECONDARY}; margin-top: 0.25rem; font-weight: 600;">Daily AI Calls</div>
        </div>
        """)

    with col2:
        fmt_limit = limits["daily_formatting_pages"]
        fmt_display = "Unlimited" if fmt_limit == -1 else (str(fmt_limit) if fmt_limit > 0 else "N/A")
        render_html(f"""
        <div style="background: #FFFFFF;
                    border-radius: 18px; padding: 1.75rem; text-align: center;
                    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04); border: 1.5px solid #E2E8F0;">
            <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">📖</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #2563EB;">{fmt_display}</div>
            <div style="font-size: 0.85rem; color: {TEXT_SECONDARY}; margin-top: 0.25rem; font-weight: 600;">Formatting Pages / Mo</div>
        </div>
        """)

    with col3:
        cover_display = "✅ Active" if limits["cover_generation"] else "❌ Inactive"
        cover_color = "#2563EB" if limits["cover_generation"] else "#DC2626"
        render_html(f"""
        <div style="background: #FFFFFF;
                    border-radius: 18px; padding: 1.75rem; text-align: center;
                    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04); border: 1.5px solid #E2E8F0;">
            <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🎨</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: {cover_color};">{cover_display}</div>
            <div style="font-size: 0.85rem; color: {TEXT_SECONDARY}; margin-top: 0.25rem; font-weight: 600;">3D Cover Studio</div>
        </div>
        """)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
