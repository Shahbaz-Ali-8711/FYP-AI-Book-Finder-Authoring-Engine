import streamlit as st
import json
import csv
import io
import textwrap
from database import admin_db
from utils.styles import (
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, SECONDARY, ACCENT,
    BORDER, BUTTON_GRADIENT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    render_html
)


def init_admin_session_state():
    """
    Centralized state initialization helper to guarantee zero widget key collisions
    and eliminate StreamlitWidgetAlreadyInstantiatedError.
    """
    defaults = {
        "admin_bypass": True,
        "editing_tier": None,
        "show_db_reset_confirm": False,
        "admin_selected_tab": 0,
        "cms_active_section": "🏠 Home Section",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_admin_panel():
    init_admin_session_state()

    # Executive Warm Ivory & Emerald Admin Control Header
    adm_hdr = f"""
    <div style="background: #FFFFFF;
                border-radius: 20px; padding: 2rem 2.25rem;
                color: #1A1A1A; margin-bottom: 2rem; border: 1.5px solid #E5E5DC;
                box-shadow: 0 10px 30px -10px rgba(26, 26, 26, 0.06);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
                    <span style="font-size: 2rem;">⚙️</span>
                    <span style="font-size: 1.85rem; font-weight: 900; letter-spacing: -0.025em; color: #1A1A1A;">
                        Pen2Publish <span style="color: #046A38;">Admin Control Center</span>
                    </span>
                    <span style="background: rgba(4, 106, 56, 0.08); color: #046A38;
                                 border: 1px solid rgba(4, 106, 56, 0.28); font-size: 0.72rem;
                                 padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 800; letter-spacing: 0.05em;">
                        SUPER ADMIN
                    </span>
                </div>
                <div style="font-size: 0.95rem; color: #4A4A4A; margin-top: 0.5rem; max-width: 680px; line-height: 1.6;">
                    Centralized governance for feature quotas, dynamic landing CMS, team profiles, pricing tiers, consultation leads, and database persistence.
                </div>
            </div>
            <div style="background: #FAFAF5; border: 1px solid #E5E5DC; border-radius: 12px; padding: 0.6rem 1.1rem; text-align: right;">
                <div style="font-size: 0.75rem; color: #737373; font-weight: 700; text-transform: uppercase;">System Status</div>
                <div style="font-size: 0.92rem; color: #046A38; font-weight: 800;">● Online & Operational</div>
            </div>
        </div>
    </div>
    """
    render_html(adm_hdr)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔧 App Settings",
        "📝 Content Manager (CMS)",
        "💎 Pricing Tiers",
        "📞 Call Leads",
        "📊 System & Users"
    ])

    with tab1:
        _render_app_settings()
    with tab2:
        _render_content_manager()
    with tab3:
        _render_pricing_management()
    with tab4:
        _render_call_leads()
    with tab5:
        _render_system_users()


# ==============================================================================
# TAB 1: APP SETTINGS & FEATURE QUOTA CONTROL
# ==============================================================================
def _render_app_settings():
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 1.35rem; font-weight: 800; color: #1A1A1A;">Feature Access & Quota Control</div>
        <div style="font-size: 0.88rem; color: #5C5C5C;">Configure freemium daily quotas and universal bypass for administrator test accounts.</div>
    </div>
    """, unsafe_allow_html=True)

    col_bypass, col_info = st.columns([1.2, 2])
    with col_bypass:
        st.markdown("##### Admin Bypass Mode")
        current_bypass = st.session_state.get("admin_bypass", False)
        bypass_toggle = st.checkbox(
            "Unlock ALL features (No quotas / paywalls)",
            value=current_bypass,
            key="admin_bypass_widget"
        )
        st.session_state["admin_bypass"] = bypass_toggle

        if bypass_toggle:
            st.success("✅ Admin Bypass Active: Unlimited AI scans, formatting & cover generations unlocked.")
        else:
            st.info("ℹ️ Standard tier enforcement active.")

    with col_info:
        st.markdown(f"""
        <div style="background: #FAFAF5; border: 1.5px solid #E5E5DC;
                    border-radius: 14px; padding: 1.25rem; font-size: 0.88rem; color: #1A1A1A; line-height: 1.65;">
            <strong style="color: #046A38;">System Advisory:</strong> When bypass mode is enabled, API calls to Gemini (gemini-3.8-flash) and formatting engines execute without daily quota deduction for verified accounts.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown("##### Feature Toggles & Usage Limits")

    try:
        features = admin_db.get_feature_settings()
    except Exception:
        features = []

    seen_features = set()
    deduped_features = []
    for f in features:
        if f['feature_name'] not in seen_features:
            seen_features.add(f['feature_name'])
            deduped_features.append(f)

    for i, feat in enumerate(deduped_features):
        fname = feat['feature_name']
        col1, col2, col3, col4 = st.columns([2, 1.5, 1.2, 1])
        with col1:
            enabled = st.checkbox(
                f"**{fname.replace('_', ' ').title()}**",
                value=feat['is_enabled'],
                key=f"feat_en_{i}_{fname}"
            )
        with col2:
            levels = ["free", "free_trial", "paid"]
            lvl_index = levels.index(feat['access_level']) if feat['access_level'] in levels else 0
            level = st.selectbox(
                "Access Level",
                levels,
                index=lvl_index,
                key=f"feat_lvl_{i}_{fname}"
            )
        with col3:
            limit = st.number_input(
                "Daily Limit",
                min_value=0,
                value=feat['daily_limit'],
                key=f"feat_lim_{i}_{fname}"
            )
        with col4:
            st.write("")
            if st.button("Save", key=f"feat_save_{i}_{fname}", use_container_width=True, type="primary"):
                try:
                    admin_db.update_feature_setting(fname, level, limit, enabled)
                    st.success(f"Saved {fname}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update {fname}: {e}")


# ==============================================================================
# TAB 2: ADVANCED DYNAMIC CMS CONTENT MANAGER (ALL 5 SECTIONS)
# ==============================================================================
def _render_content_manager():
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 1.35rem; font-weight: 800; color: #1A1A1A;">Dynamic Site Content Editor (CMS)</div>
        <div style="font-size: 0.88rem; color: #5C5C5C;">
            Add, edit, and delete headlines, narratives, team member profiles, core engines, pricing tiers, and advisory details across all 5 platform sections.
        </div>
    </div>
    """, unsafe_allow_html=True)

    cms_sections = [
        "🏠 Home Section",
        "📖 About Us & The Vision",
        "👥 Founding Team Showcase",
        "⚙️ Core Engines & Authoring Suite",
        "💎 Packages & Pricing Plans",
        "📞 Book a Call Advisory",
        "💬 Testimonials & FAQs",
    ]

    content_section = st.selectbox(
        "Select Section to Configure",
        cms_sections,
        key="cms_section_selector_master"
    )

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    if content_section == "🏠 Home Section":
        _edit_home_section_cms()
    elif content_section == "📖 About Us & The Vision":
        _edit_vision_content()
    elif content_section == "👥 Founding Team Showcase":
        _edit_founding_team_cms()
    elif content_section == "⚙️ Core Engines & Authoring Suite":
        _edit_core_engines_cms()
    elif content_section == "💎 Packages & Pricing Plans":
        _edit_packages_cms()
    elif content_section == "📞 Book a Call Advisory":
        _edit_book_call_cms()
    elif content_section == "💬 Testimonials & FAQs":
        _edit_testimonials_and_faq_cms()


# --- SECTION 1: HOME SECTION (HEADLINE, SUBHEADLINE, CTA & METRICS) ---
def _edit_home_section_cms():
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1.15rem; font-weight: 800; color: #046A38; margin-bottom: 0.4rem;">🏠 Hero Headline & Core CTA</div>
        <div style="font-size: 0.85rem; color: #5C5C5C;">Modify the high-converting copy displayed on the landing page hero card.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        existing_hero = admin_db.get_cms_content("hero")
    except Exception:
        existing_hero = {}

    col_h1, col_h2 = st.columns([1.5, 1])
    with col_h1:
        headline = st.text_input(
            "Main Hero Headline (HTML formatting supported)",
            value=existing_hero.get("headline", "Turn Ideas Into Published Books and<br><span style='color: #046A38;'>Scalable Author Systems</span>"),
            key="cms_hero_hl_val"
        )
        subheadline = st.text_area(
            "Sub-headline Narrative",
            value=existing_hero.get("subheadline", "Pen2Publish AI is the world's foremost end-to-end autonomous authoring, formatting, and reader discovery suite. Powered by Gemini generative intelligence."),
            key="cms_hero_sub_val",
            height=100
        )
        cta_text = st.text_input(
            "Primary CTA Button Text",
            value=existing_hero.get("cta_text", "Start Authoring Now"),
            key="cms_hero_cta_val"
        )

    with col_h2:
        st.markdown("**Live Hero Preview:**")
        preview_html = f"""
        <div style="background: #FAFAF5; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.25rem;">
            <div style="font-size: 1.15rem; font-weight: 900; color: #1A1A1A; line-height: 1.3; margin-bottom: 0.6rem;">
                {headline}
            </div>
            <div style="font-size: 0.8rem; color: #4A4A4A; line-height: 1.5; margin-bottom: 1rem;">
                {subheadline}
            </div>
            <div style="background: #E34234; color: #FFFFFF; font-size: 0.78rem; font-weight: 700; padding: 0.5rem 1rem; border-radius: 8px; display: inline-block;">
                🚀 {cta_text}
            </div>
        </div>
        """
        render_html(preview_html)

    if st.button("💾 Save Hero Settings", key="save_hero_cms_action", type="primary"):
        try:
            admin_db.set_cms_content("hero", "headline", headline)
            admin_db.set_cms_content("hero", "subheadline", subheadline)
            admin_db.set_cms_content("hero", "cta_text", cta_text)
            st.success("✅ Hero Section copy updated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving hero content: {e}")

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 2rem 0;'>", unsafe_allow_html=True)

    # Metrics Counter Banner Editor
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1.15rem; font-weight: 800; color: #046A38; margin-bottom: 0.4rem;">📊 Platform Metrics Counter Bar</div>
        <div style="font-size: 0.85rem; color: #5C5C5C;">Configure the four statistics showcased directly below the hero section.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        metrics = admin_db.get_cms_content("metrics")
    except Exception:
        metrics = {}

    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    with m_c1:
        m1_v = st.text_input("Metric 1 Value", value=metrics.get("m1_val", "10K+"), key="m1_v_inp")
        m1_l = st.text_input("Metric 1 Label", value=metrics.get("m1_lbl", "Covers Scanned"), key="m1_l_inp")
    with m_c2:
        m2_v = st.text_input("Metric 2 Value", value=metrics.get("m2_val", "50K+"), key="m2_v_inp")
        m2_l = st.text_input("Metric 2 Label", value=metrics.get("m2_lbl", "AI Summaries"), key="m2_l_inp")
    with m_c3:
        m3_v = st.text_input("Metric 3 Value", value=metrics.get("m3_val", "3K+"), key="m3_v_inp")
        m3_l = st.text_input("Metric 3 Label", value=metrics.get("m3_lbl", "Authors Publishing"), key="m3_l_inp")
    with m_c4:
        m4_v = st.text_input("Metric 4 Value", value=metrics.get("m4_val", "99.4%"), key="m4_v_inp")
        m4_l = st.text_input("Metric 4 Label", value=metrics.get("m4_lbl", "Platform Satisfaction"), key="m4_l_inp")

    if st.button("💾 Save Metrics Bar", key="save_metrics_cms_action", type="primary"):
        try:
            admin_db.set_cms_content("metrics", "m1_val", m1_v)
            admin_db.set_cms_content("metrics", "m1_lbl", m1_l)
            admin_db.set_cms_content("metrics", "m2_val", m2_v)
            admin_db.set_cms_content("metrics", "m2_lbl", m2_l)
            admin_db.set_cms_content("metrics", "m3_val", m3_v)
            admin_db.set_cms_content("metrics", "m3_lbl", m3_l)
            admin_db.set_cms_content("metrics", "m4_val", m4_v)
            admin_db.set_cms_content("metrics", "m4_lbl", m4_l)
            st.success("✅ Platform metrics updated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving metrics: {e}")


# --- SECTION 2: ABOUT US & THE VISION ---
def _edit_vision_content():
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1.15rem; font-weight: 800; color: #046A38; margin-bottom: 0.4rem;">📖 The Vision & Company Mission</div>
        <div style="font-size: 0.85rem; color: #5C5C5C;">Craft the narrative that explains the core purpose of Pen2Publish AI.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        existing = admin_db.get_cms_content("vision")
    except Exception:
        existing = {}

    heading = st.text_input(
        "Section Heading",
        value=existing.get("heading", "Meet the Visionaries Behind the AI Authoring Engine"),
        key="cms_vision_heading_inp"
    )
    body = st.text_area(
        "Vision Narrative",
        value=existing.get("body", "Our core mission is to empower first-time authors, researchers, and creators with automated research, chapter formatting, and cover designs. We believe every great idea deserves to be a beautifully published book."),
        key="cms_vision_body_inp",
        height=140
    )

    with st.expander("👁️ Preview Vision Section"):
        render_html(f"""
        <div style="background: #FAFAF5; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem;">
            <div style="color: #046A38; font-size: 0.8rem; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;">THE VISION</div>
            <div style="font-size: 1.4rem; font-weight: 900; color: #1A1A1A; margin: 0.5rem 0;">{heading}</div>
            <div style="font-size: 0.95rem; color: #333333; line-height: 1.7;">{body}</div>
        </div>
        """)

    if st.button("💾 Save Vision Content", key="save_vision_btn", type="primary"):
        try:
            admin_db.set_cms_content("vision", "heading", heading)
            admin_db.set_cms_content("vision", "body", body)
            st.success("✅ Vision content updated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving vision: {e}")


# --- SECTION 3: FOUNDING TEAM SHOWCASE (SHAHBAZ ALI, HUZAIFA TANVEER, ARSALAN RASHEED ABBASI) ---
def _edit_founding_team_cms():
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1.15rem; font-weight: 800; color: #046A38; margin-bottom: 0.4rem;">👥 Founding Team Member Profiles</div>
        <div style="font-size: 0.85rem; color: #5C5C5C;">Manage profile details, engineering roles, and biographies for the 3 core platform engineers.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        team_cms = admin_db.get_cms_content("team")
    except Exception:
        team_cms = {}

    default_members = [
        {
            "id": 0,
            "def_name": "Shahbaz Ali",
            "def_role": "System Architect & AI/Cloud Engineer",
            "def_bio": "Core Logic Architect for the entire platform. Great experience in building logic for the whole project, with expertise in Cloud Computing infrastructure, scalable systems, and Generative AI integration (gemini-3.8-flash).",
            "def_badge": "SYSTEM ARCHITECT"
        },
        {
            "id": 1,
            "def_name": "Huzaifa Tanveer",
            "def_role": "Cybersecurity & Infrastructure Lead",
            "def_bio": "Great experience with Cybersecurity, Ethical Hacking, system hardening, secure data hashing, and extensive knowledge about industry standards.",
            "def_badge": "CYBERSECURITY LEAD"
        },
        {
            "id": 2,
            "def_name": "Arsalan Rasheed Abbasi",
            "def_role": "Systems Upgrade & Lifecycle Engineer",
            "def_bio": "Specialist in updates, upgrades, feature maintenance, CI/CD pipelines, and continuous software lifecycle optimization for the project.",
            "def_badge": "LIFECYCLE & UPGRADES"
        }
    ]

    for m in default_members:
        mid = m["id"]
        prefix = f"m{mid}"
        st.markdown(f"##### Member #{mid+1}: {m['def_name']}")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(
                f"Full Name (Member {mid+1})",
                value=team_cms.get(f"{prefix}_name", m["def_name"]),
                key=f"team_m_{mid}_name"
            )
            role = st.text_input(
                f"Engineering Role",
                value=team_cms.get(f"{prefix}_role", m["def_role"]),
                key=f"team_m_{mid}_role"
            )
        with col2:
            bio = st.text_area(
                f"Professional Bio & Experience",
                value=team_cms.get(f"{prefix}_bio", m["def_bio"]),
                key=f"team_m_{mid}_bio",
                height=90
            )

        if st.button(f"💾 Save {name}", key=f"save_team_m_{mid}_btn", type="primary"):
            try:
                admin_db.set_cms_content("team", f"{prefix}_name", name)
                admin_db.set_cms_content("team", f"{prefix}_role", role)
                admin_db.set_cms_content("team", f"{prefix}_bio", bio)
                st.success(f"✅ Saved profile for {name}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving team profile: {e}")
        st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1.5rem 0;'>", unsafe_allow_html=True)


# --- SECTION 4: CORE ENGINES & AUTHORING SUITE ---
def _edit_core_engines_cms():
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1.15rem; font-weight: 800; color: #046A38; margin-bottom: 0.4rem;">⚙️ Core Engines & Production Modules</div>
        <div style="font-size: 0.85rem; color: #5C5C5C;">Customize the 6 core authoring and discovery engine cards presented in the platform showcase.</div>
    </div>
    """, unsafe_allow_html=True)

    default_engines = [
        ("✍️", "AI Creator Studio & Formatter",
         "Research, plot, compose, structure, and format books into publication-ready PDFs, EPUBs, and Word DOCX editions with automated TOC."),
        ("📖", "AI Reader Hub & Companion",
         "Discover books by atmospheric vibe, matchmaker recommendations, visual cover search, chapter summaries, and browser audio narration."),
        ("📷", "OCR Book Cover Scanner",
         "Snap or upload any book cover. Gemini Vision AI extracts title, author, and edition metadata instantly with automated catalog lookup."),
        ("🔍", "Gutenberg Library Search",
         "Search 60,000+ free public domain masterpieces. Read full books with direct chapter downloads and format viewer."),
        ("🤖", "AI Literary Assistant Chatbot",
         "Chat with our literary AI. Get deep thematic insights, character analysis, chapter breakdowns, and personalized storytelling advice."),
        ("🌐", "Platform & Author Marketplace",
         "Explore the public author showcase directory, manage freemium daily quotas, and inspect real-time telemetry analytics."),
    ]

    try:
        engines_cms = admin_db.get_cms_content("engines")
    except Exception:
        engines_cms = {}

    for i, (def_icon, def_title, def_desc) in enumerate(default_engines):
        st.markdown(f"**Engine #{i+1} Configuration**")
        col_ic, col_ti = st.columns([1, 4])
        with col_ic:
            icon = st.text_input("Icon", value=engines_cms.get(f"item_{i}_icon", def_icon), key=f"eng_icon_{i}")
        with col_ti:
            title = st.text_input("Title", value=engines_cms.get(f"item_{i}_title", def_title), key=f"eng_title_{i}")
        desc = st.text_area("Description", value=engines_cms.get(f"item_{i}_desc", def_desc), key=f"eng_desc_{i}", height=75)

        if st.button(f"💾 Save Engine #{i+1}", key=f"save_eng_btn_{i}"):
            try:
                # Save to both engines and portfolio for complete backward-compatibility
                admin_db.set_cms_content("engines", f"item_{i}_icon", icon)
                admin_db.set_cms_content("engines", f"item_{i}_title", title)
                admin_db.set_cms_content("engines", f"item_{i}_desc", desc)
                admin_db.set_cms_content("portfolio", f"item_{i}_icon", icon)
                admin_db.set_cms_content("portfolio", f"item_{i}_title", title)
                admin_db.set_cms_content("portfolio", f"item_{i}_desc", desc)
                st.success(f"✅ Saved {title}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving engine: {e}")
        st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1.25rem 0;'>", unsafe_allow_html=True)


# --- SECTION 5: PACKAGES & PRICING PLANS ---
def _edit_packages_cms():
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1.15rem; font-weight: 800; color: #046A38; margin-bottom: 0.4rem;">💎 Packages & Membership Configuration</div>
        <div style="font-size: 0.85rem; color: #5C5C5C;">Direct link to full Tier Management in the dedicated Pricing Tiers tab, or configure promotional messaging below.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        pkg_cms = admin_db.get_cms_content("packages")
    except Exception:
        pkg_cms = {}

    badge_msg = st.text_input(
        "Promotional Banner / Sub-title",
        value=pkg_cms.get("subtitle", "Transparent, scalable tiers designed for indie authors, researchers, and professional publishers."),
        key="pkg_sub_inp"
    )
    if st.button("💾 Save Package Messaging", key="save_pkg_msg_btn", type="primary"):
        try:
            admin_db.set_cms_content("packages", "subtitle", badge_msg)
            st.success("✅ Package messaging saved!")
        except Exception as e:
            st.error(f"Error: {e}")

    st.info("💡 To modify pricing numbers, monthly costs, or feature checklists, use the dedicated '💎 Pricing Tiers' tab above.")


# --- SECTION 6: BOOK A CALL ADVISORY ---
def _edit_book_call_cms():
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1.15rem; font-weight: 800; color: #046A38; margin-bottom: 0.4rem;">📞 Book a Call Advisory Details</div>
        <div style="font-size: 0.85rem; color: #5C5C5C;">Customize consultation contact information, office locations, and guaranteed response windows.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        call_cms = admin_db.get_cms_content("book_call")
    except Exception:
        call_cms = {}

    title = st.text_input("Consultation Heading", value=call_cms.get("title", "Book a 1-on-1 Consultation"), key="call_t_inp")
    subtitle = st.text_area("Consultation Subtitle", value=call_cms.get("subtitle", "Speak directly with our AI publishing architects to map out your book, workflow, or custom integration."), key="call_sub_inp", height=70)

    c1, c2 = st.columns(2)
    with c1:
        office = st.text_input("Engineering Hub Address", value=call_cms.get("office", "Pen2Publish AI Systems, San Francisco & Islamabad"), key="call_off_inp")
        email = st.text_input("Core Founders Line / Email", value=call_cms.get("email", "advisory@pen2publish.ai"), key="call_em_inp")
    with c2:
        response = st.text_input("Response Window", value=call_cms.get("response", "Under 4 Hours (Monday – Saturday)"), key="call_resp_inp")
        perk = st.text_input("Consultation Perk Highlight", value=call_cms.get("perk", "✦ 100% Free 30-Minute Architecture & Publishing Discovery Session"), key="call_perk_inp")

    if st.button("💾 Save Consultation Settings", key="save_call_cms_btn", type="primary"):
        try:
            admin_db.set_cms_content("book_call", "title", title)
            admin_db.set_cms_content("book_call", "subtitle", subtitle)
            admin_db.set_cms_content("book_call", "office", office)
            admin_db.set_cms_content("book_call", "email", email)
            admin_db.set_cms_content("book_call", "response", response)
            admin_db.set_cms_content("book_call", "perk", perk)
            st.success("✅ Consultation details updated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving consultation settings: {e}")


# --- SECTION 7: TESTIMONIALS & FAQS ---
def _edit_testimonials_and_faq_cms():
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1.15rem; font-weight: 800; color: #046A38; margin-bottom: 0.4rem;">💬 Testimonials & Frequently Asked Questions</div>
        <div style="font-size: 0.85rem; color: #5C5C5C;">Manage social proof quotes from published authors and answer common onboarding questions.</div>
    </div>
    """, unsafe_allow_html=True)

    tab_t, tab_f = st.tabs(["Author Testimonials", "Frequently Asked Questions (FAQ)"])

    with tab_t:
        try:
            test_cms = admin_db.get_cms_content("testimonials")
        except Exception:
            test_cms = {}

        defaults_t = [
            ("Dr. Jennifer Hayes", "Academic Author & Book Blogger", "The book formatter and 3D preview saved me weeks of manual work. Uploaded raw research papers, received a structured manuscript in minutes."),
            ("David Chen", "Sci-Fi Indie Author", "The Creator Studio gave me the structure I was missing for 3 years. It generated cohesive chapter outlines and a phenomenal cover concept."),
            ("Aisha Patel", "AI Researcher & Speaker", "The literary assistant chatbot acts like having an Oxford editor on standby 24/7. It identified character plot holes instantly."),
        ]

        for i in range(3):
            st.markdown(f"**Testimonial #{i+1}**")
            col1, col2 = st.columns(2)
            with col1:
                author = st.text_input(f"Author #{i+1}", value=test_cms.get(f"t_{i}_author", defaults_t[i][0]), key=f"t_auth_{i}")
                role = st.text_input(f"Role/Title #{i+1}", value=test_cms.get(f"t_{i}_role", defaults_t[i][1]), key=f"t_role_{i}")
            with col2:
                quote = st.text_area(f"Quote #{i+1}", value=test_cms.get(f"t_{i}_text", defaults_t[i][2]), key=f"t_quote_{i}", height=75)

            if st.button(f"💾 Save Testimonial #{i+1}", key=f"save_test_btn_{i}"):
                try:
                    admin_db.set_cms_content("testimonials", f"t_{i}_author", author)
                    admin_db.set_cms_content("testimonials", f"t_{i}_role", role)
                    admin_db.set_cms_content("testimonials", f"t_{i}_text", quote)
                    st.success(f"✅ Saved Testimonial #{i+1}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving testimonial: {e}")
            st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1rem 0;'>", unsafe_allow_html=True)

    with tab_f:
        try:
            faq_cms = admin_db.get_cms_content("faq")
        except Exception:
            faq_cms = {}

        defaults_f = [
            ("How does the 3D Book Viewer work?", "Our 3D viewer renders your book in spatial WebGL so you can rotate it 360 degrees."),
            ("Can I format a full book?", "Yes! Upload raw text or PDF. AI structures it into chapters with table of contents."),
            ("What is the Cover Generator?", "AI-powered tool that creates professional book cover artwork from a text prompt."),
            ("Is the free tier really free?", "Yes! Free daily AI searches, summaries, and scanning every day — forever."),
        ]

        for i in range(4):
            st.markdown(f"**FAQ #{i+1}**")
            q = st.text_input(f"Question #{i+1}", value=faq_cms.get(f"q_{i}", defaults_f[i][0]), key=f"faq_q_{i}")
            a = st.text_area(f"Answer #{i+1}", value=faq_cms.get(f"a_{i}", defaults_f[i][1]), key=f"faq_a_{i}", height=65)

            if st.button(f"💾 Save FAQ #{i+1}", key=f"save_faq_btn_{i}"):
                try:
                    admin_db.set_cms_content("faq", f"q_{i}", q)
                    admin_db.set_cms_content("faq", f"a_{i}", a)
                    st.success(f"✅ Saved FAQ #{i+1}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving FAQ: {e}")
            st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1rem 0;'>", unsafe_allow_html=True)


# ==============================================================================
# TAB 3: DYNAMIC PRICING TIER MANAGEMENT
# ==============================================================================
def _render_pricing_management():
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 1.35rem; font-weight: 800; color: #1A1A1A;">Dynamic Pricing Tier Management</div>
        <div style="font-size: 0.88rem; color: #5C5C5C;">Create, edit, or toggle subscription tiers live across the platform.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        tiers = admin_db.get_all_pricing_tiers()
    except Exception:
        tiers = []

    st.markdown("##### Current Configured Tiers")
    for idx, tier in enumerate(tiers):
        tier_id, name, price, period, color, featured, active = tier
        col1, col2, col3, col4 = st.columns([2, 1.2, 1, 1])
        with col1:
            badge = "⭐ Featured" if featured else ""
            status = "(Inactive)" if not active else ""
            st.markdown(f"**{name}** `{badge}` `{status}`")
        with col2:
            st.text(f"${price}/{period}")
        with col3:
            if st.button("Edit", key=f"edit_tier_btn_{idx}_{tier_id}", use_container_width=True):
                st.session_state["editing_tier"] = name
                st.rerun()
        with col4:
            if st.button("Deactivate", key=f"del_tier_btn_{idx}_{tier_id}", use_container_width=True):
                try:
                    admin_db.delete_pricing_tier(name)
                    st.success(f"Deactivated {name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deactivating tier: {e}")

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 2rem 0;'>", unsafe_allow_html=True)
    editing = st.session_state.get("editing_tier")
    try:
        existing_tiers = admin_db.get_pricing_tiers()
    except Exception:
        existing_tiers = {}

    edit_data = existing_tiers.get(editing, {}) if editing else {}

    st.markdown(f"##### {'Edit Tier: ' + editing if editing else 'Create New Tier'}")

    with st.form("tier_management_form"):
        col1, col2 = st.columns(2)
        with col1:
            tier_name = st.text_input("Tier Name", value=editing or "", key="tier_name_fld")
            price = st.number_input(
                "Price ($)",
                min_value=0.0,
                value=float(edit_data.get("price", 0.0)),
                step=0.01,
                key="tier_price_fld"
            )
            period = st.text_input("Billing Period", value=edit_data.get("period", "month"), key="tier_period_fld")
        with col2:
            color = st.text_input("Brand Color (HEX)", value=edit_data.get("color", "#046A38"), key="tier_color_fld")
            is_featured = st.checkbox("Featured (Most Popular Badge)", value=bool(edit_data.get("featured", False)), key="tier_featured_fld")

        features_default = "\n".join([f"{f[0]} {f[1]}" for f in edit_data.get("features", [])]) if edit_data.get("features") else "✅ 50 AI searches/day\n✅ Unlimited AI summaries\n✅ Advanced book scanner"
        features_text = st.text_area(
            "Features (one per line, format: ✅ Feature text)",
            value=features_default,
            height=100,
            key="tier_features_fld"
        )
        limits_default = json.dumps(edit_data.get("limits", {"daily_ai_calls": 50, "daily_formatting_pages": 20, "cover_generation": True}))
        limits_json = st.text_area("Limits (JSON)", value=limits_default, height=60, key="tier_limits_fld")

        submitted = st.form_submit_button("Save Pricing Tier", type="primary")

        if submitted and tier_name:
            features_list = [[line[:2], line[3:].strip()] for line in features_text.strip().split("\n") if line.strip()]
            features_json = json.dumps(features_list)
            try:
                limits_parsed = json.loads(limits_json)
                limits_json_valid = json.dumps(limits_parsed)
            except json.JSONDecodeError:
                limits_json_valid = limits_json

            try:
                if editing and editing in existing_tiers:
                    admin_db.update_pricing_tier(tier_name, price, period, color, is_featured, features_json, limits_json_valid)
                    st.success(f"✅ Updated {tier_name}!")
                else:
                    success, msg = admin_db.add_pricing_tier(tier_name, price, period, color, is_featured, features_json, limits_json_valid)
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(msg)
                st.session_state["editing_tier"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Error saving tier: {e}")


# ==============================================================================
# TAB 4: CONSULTATION LEADS MANAGEMENT
# ==============================================================================
def _render_call_leads():
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 1.35rem; font-weight: 800; color: #1A1A1A;">Consultation Lead Inquiries</div>
        <div style="font-size: 0.88rem; color: #5C5C5C;">Review and follow up with authors booking 1-on-1 strategy calls.</div>
    </div>
    """, unsafe_allow_html=True)

    col_filter, col_export = st.columns([1.5, 1])
    with col_filter:
        status_filter = st.selectbox(
            "Filter by Lead Status",
            ["all", "pending", "contacted", "archived"],
            key="lead_status_filter_sel"
        )
    with col_export:
        st.write("")
        export = st.button("📥 Prepare CSV Export", key="export_leads_action_btn", use_container_width=True)

    try:
        leads = admin_db.get_booking_leads(status_filter)
    except Exception:
        leads = []

    if export and leads:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Email", "Preferred Time", "Project Details", "Status", "Created At"])
        for lead in leads:
            writer.writerow(lead)
        st.download_button(
            "⬇️ Download CSV File",
            data=output.getvalue(),
            file_name="pen2publish_consultation_leads.csv",
            mime="text/csv",
            key="download_leads_csv_btn"
        )

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    if not leads:
        st.info("ℹ️ No consultation leads found matching this filter.")
    else:
        for idx, lead in enumerate(leads):
            lead_id, name, email, time, details, status, created = lead
            badge_color = "#046A38" if status == "contacted" else ("#E34234" if status == "pending" else "#737373")
            with st.expander(f"Lead #{lead_id} — {name} [{status.upper()}] — {created}"):
                st.markdown(f"**Email:** `{email}`")
                st.markdown(f"**Requested Consultation Window:** `{time or 'N/A'}`")
                st.markdown(f"**Project Details:**\n{details or 'N/A'}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("Mark Contacted", key=f"lead_contacted_{idx}_{lead_id}"):
                        admin_db.update_lead_status(lead_id, "contacted")
                        st.rerun()
                with c2:
                    if st.button("Mark Pending", key=f"lead_pending_{idx}_{lead_id}"):
                        admin_db.update_lead_status(lead_id, "pending")
                        st.rerun()
                with c3:
                    if st.button("Archive", key=f"lead_archived_{idx}_{lead_id}"):
                        admin_db.update_lead_status(lead_id, "archived")
                        st.rerun()


# ==============================================================================
# TAB 5: SYSTEM INFRASTRUCTURE & USER GOVERNANCE
# ==============================================================================
def _render_system_users():
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 1.35rem; font-weight: 800; color: #1A1A1A;">System Infrastructure & User Governance</div>
        <div style="font-size: 0.88rem; color: #5C5C5C;">Platform telemetry statistics, database maintenance, and administrative accounts.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        stats = admin_db.get_user_stats()
    except Exception:
        stats = {"total_users": 0, "total_leads": 0, "pending_leads": 0, "total_searches": 0}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Registered Users", stats.get("total_users", 0))
    with col2:
        st.metric("Total Inquiries", stats.get("total_leads", 0))
    with col3:
        st.metric("Pending Inquiries", stats.get("pending_leads", 0))
    with col4:
        st.metric("Total AI Scans", stats.get("total_searches", 0))

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 2rem 0;'>", unsafe_allow_html=True)

    tab_users, tab_admins, tab_cleanup = st.tabs(["Registered Users", "Admin Accounts", "System Maintenance"])

    with tab_users:
        try:
            users = admin_db.get_all_users()
        except Exception:
            users = []

        if users:
            for idx, user in enumerate(users):
                c1, c2, c3, c4 = st.columns([1, 2, 2.5, 1])
                with c1:
                    st.text(f"ID #{user[0]}")
                with c2:
                    st.markdown(f"**{user[1]}**")
                with c3:
                    st.text(user[2])
                with c4:
                    if st.button("Delete", key=f"del_user_btn_{idx}_{user[0]}"):
                        try:
                            admin_db.delete_user(user[0])
                            st.success(f"Deleted user {user[1]}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting user: {e}")
        else:
            st.info("ℹ️ No registered users recorded.")

    with tab_admins:
        try:
            admins = admin_db.get_all_admin_users()
        except Exception:
            admins = []

        for a in admins:
            st.markdown(f"👤 **{a[1]}** {'(Super Admin)' if a[2] else ''} — Registered: `{a[3]}`")

        st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("##### Provision New Admin Account")
        with st.form("new_admin_provision_form"):
            new_user = st.text_input("Admin Username", key="new_adm_user_fld")
            new_pass = st.text_input("Admin Password", type="password", key="new_adm_pass_fld")
            is_super = st.checkbox("Grant Super Admin Privileges", key="new_adm_super_fld")
            if st.form_submit_button("Create Administrator", type="primary"):
                if new_user and new_pass:
                    try:
                        success, msg = admin_db.create_admin_user(new_user, new_pass, is_super)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    except Exception as e:
                        st.error(f"Error creating admin: {e}")
                else:
                    st.warning("Please specify both username and password")

    with tab_cleanup:
        st.markdown("##### Maintenance & Data Sanitization")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧹 Clear Temporary Files & Cache", key="clear_temp_cache_btn"):
                try:
                    if admin_db.clear_temp_files():
                        st.success("Cleaned temporary cache files!")
                    else:
                        st.info("No temporary files required purging.")
                except Exception as e:
                    st.error(f"Error purging cache: {e}")

        with c2:
            if not st.session_state.get("show_db_reset_confirm", False):
                if st.button("⚠️ Reset Database Tables", key="init_db_reset_btn"):
                    st.session_state["show_db_reset_confirm"] = True
                    st.rerun()
            else:
                st.warning("⚠️ WARNING: This will re-initialize database schemas and seeds. Are you certain?")
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("🚨 Yes, Confirm Full Reset", key="execute_db_reset_btn", type="primary"):
                        try:
                            from database.db_handler import init_db
                            init_db()
                            st.session_state["show_db_reset_confirm"] = False
                            st.success("Database schemas re-initialized successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error resetting database: {e}")
                with rc2:
                    if st.button("Cancel", key="cancel_db_reset_btn"):
                        st.session_state["show_db_reset_confirm"] = False
                        st.rerun()
