import streamlit as st
from utils.styles import (
    stat_card, PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT,
    SECONDARY, ACCENT, BUTTON_GRADIENT, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, CARD_BG, CARD_BG_SECONDARY,
    render_html
)


def render_dashboard():
    username = st.session_state.get("username", "Author")

    # Warm Ivory & Luxury Emerald Hero Card
    render_html(f"""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                border-radius: 20px; padding: 2.25rem;
                margin-bottom: 2rem;
                box-shadow: 0 10px 30px -10px rgba(26, 26, 26, 0.06), 0 2px 8px -2px rgba(26, 26, 26, 0.04);">
        <div style="display: inline-block; background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28);
                    font-size: 0.82rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;
                    padding: 0.25rem 0.75rem; border-radius: 9999px; margin-bottom: 0.5rem;">
            AUTHOR WORKSPACE · PEN2PUBLISH AI
        </div>
        <div style="font-size: 2.2rem; font-weight: 900; margin-bottom: 0.4rem; color: #1A1A1A; letter-spacing: -0.02em;">
            👋 Welcome back, {username}!
        </div>
        <div style="font-size: 1rem; color: #4A4A4A; max-width: 680px; line-height: 1.6;">
            Your Gemini-powered authoring and reader suite is fully active and synchronized. Select an engine below to start drafting, discovering, or showcasing manuscripts in our high-contrast Warm Ivory workspace.
        </div>
    </div>
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(stat_card("Active", "Vision OCR Engine"), unsafe_allow_html=True)
    with col2:
        st.markdown(stat_card("60K+", "Gutenberg Library"), unsafe_allow_html=True)
    with col3:
        st.markdown(stat_card("Unlimited", "AI Queries"), unsafe_allow_html=True)
    with col4:
        st.markdown(stat_card("Pro", "Author Tier"), unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size: 1.5rem; font-weight: 800; color: #1A1A1A; margin-bottom: 1.25rem; letter-spacing: -0.02em;">
        ⚡ Rapid Launch Engines
    </div>
    """, unsafe_allow_html=True)

    modules = [
        ("📷", "Book Cover Scanner", "Extract titles, author details, and publication metadata using real-time Gemini Vision OCR.", "scanner", "Scan Cover"),
        ("🔍", "Gutenberg Library Search", "Search 60,000+ public domain literary works with direct chapter downloads and viewer.", "search", "Search Books"),
        ("✍️", "AI Creator Studio", "Generate full manuscripts, auto-format chapters, plot twists, and compile professional PDF, EPUB & DOCX.", "creator", "Open Studio"),
        ("🤖", "Literary AI Assistant", "Receive deep character analyses, plot structuring ideas, and thematic advice from our AI chatbot.", "chatbot", "Chat with AI"),
        ("📖", "Reader Hub & Companion", "Discover books by emotional vibe, AI matchmaker, visual cover finder, chapter summarizer & TTS audio narrator.", "reader", "Open Reader"),
        ("🌐", "Platform & Marketplace", "Browse the public author showcase directory, manage freemium quotas & subscriptions, and inspect real-time analytics.", "platform", "Explore Platform"),
    ]

    for i in range(0, len(modules), 2):
        cols = st.columns(2)
        for j, (icon, title, desc, target_page, btn_label) in enumerate(modules[i:i+2]):
            with cols[j]:
                render_html(f"""
                <div style="background: #FFFFFF;
                            border-radius: 18px; padding: 1.75rem; border: 1.5px solid #E5E5DC;
                            box-shadow: 0 8px 24px -6px rgba(26, 26, 26, 0.05); margin-bottom: 0.75rem; min-height: 195px;
                            transition: all 0.25s ease;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem;">
                        <span style="font-size: 2.2rem;">{icon}</span>
                        <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28); font-size: 0.72rem; padding: 0.2rem 0.65rem; border-radius: 9999px; font-weight: 800;">ACTIVE</span>
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: #1A1A1A; margin-bottom: 0.4rem; letter-spacing: -0.01em;">
                        {title}
                    </div>
                    <div style="font-size: 0.88rem; color: #4A4A4A; line-height: 1.6; margin-bottom: 1rem;">
                        {desc}
                    </div>
                </div>
                """)
                is_featured = (target_page in ("creator", "reader"))
                if st.button(f"Launch {btn_label} →", key=f"dash_mod_{i+j}", use_container_width=True, type="primary" if is_featured else "secondary"):
                    st.session_state["nav_page"] = target_page
                    st.rerun()

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    render_html(f"""
    <div style="background: #FFFFFF;
                border-radius: 18px; padding: 1.75rem; border: 1.5px solid #E5E5DC;
                box-shadow: 0 4px 16px rgba(26, 26, 26, 0.04);">
        <div style="font-size: 1.15rem; font-weight: 800; color: #1A1A1A; margin-bottom: 0.5rem; letter-spacing: -0.01em;">
            📋 System Activity Feed & Status
        </div>
        <div style="color: #4A4A4A; font-size: 0.9rem; line-height: 1.6;">
            All system endpoints are operational in the <strong>Pen2Publish AI</strong> workspace. Start your session by launching the Creator Studio, discovering titles in the Reader Hub, or browsing the Author Marketplace.
        </div>
    </div>
    """)
