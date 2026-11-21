import streamlit as st
from config.pricing import PRICING_TIERS
from database import admin_db
from utils.styles import (
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, SECONDARY, ACCENT, BORDER,
    BUTTON_GRADIENT, BUTTON_HOVER_GRADIENT, EMERALD_GRADIENT,
    HERO_GRADIENT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, render_html
)
from utils.three_d_viewer import render_3d_book_viewer


def _get_cms(section, defaults):
    try:
        saved = admin_db.get_cms_content(section)
        for key, val in defaults.items():
            if key in saved and saved[key]:
                defaults[key] = saved[key]
    except Exception:
        pass
    return defaults


def _get_dynamic_pricing():
    try:
        db_tiers = admin_db.get_pricing_tiers()
        if db_tiers:
            return db_tiers
    except Exception:
        pass
    return PRICING_TIERS


def render_landing_page():
    section = st.session_state.get("nav_section", "home")

    if section == "home":
        _render_hero()
        _render_home_expanded_features()
        _render_vision()
        _render_team_showcase()
        _render_testimonials()
        _render_faq()
        _render_footer()
    elif section == "about":
        _render_vision()
        _render_team_showcase()
        _render_footer()
    elif section in ("engines", "portfolio"):
        _render_core_engines_page()
        _render_footer()
    elif section == "packages":
        _render_packages()
        _render_footer()
    elif section == "book_call":
        _render_book_call()
        _render_footer()


# ==============================================================================
# HERO SECTION (MINIMAL, HIGH-IMPACT & NO DUPLICATE BADGES)
# ==============================================================================
def _render_hero():
    cms = _get_cms("hero", {
        "headline": "Turn Ideas Into Published Books and<br><span style='color: #046A38;'>Scalable Author Systems</span>",
        "subheadline": "Pen2Publish AI is the world's foremost end-to-end autonomous authoring, formatting, and reader discovery suite. Powered by Gemini generative intelligence.",
        "cta_text": "Start Authoring Now",
    })

    col_3d, col_content = st.columns([1.1, 1.25], gap="large")

    with col_3d:
        render_3d_book_viewer(height=520)

    with col_content:
        # High-impact Warm Ivory / White Hero Card
        hero_card_html = f"""
        <div class="ivory-glass-card" style="padding: 2.25rem; margin-top: 0.25rem; background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 24px; box-shadow: 0 15px 35px -10px rgba(26,26,26,0.06);">
            <div style="font-size: 2.45rem; font-weight: 900; color: #1A1A1A; line-height: 1.22;
                        letter-spacing: -0.03em; margin-bottom: 1.15rem;">
                {cms['headline']}
            </div>

            <div style="font-size: 1.05rem; color: #4A4A4A; line-height: 1.75; margin-bottom: 1.8rem; max-width: 540px; font-weight: 400;">
                {cms['subheadline']}
            </div>

            <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
                <div style="background: #F5F5ED; border: 1px solid #E5E5DC;
                            border-radius: 12px; padding: 0.45rem 0.85rem;
                            font-size: 0.82rem; color: #1A1A1A; font-weight: 700;
                            display: flex; align-items: center; gap: 0.4rem; box-shadow: 0 2px 4px rgba(26,26,26,0.03);">
                    <span style="color: #E34234;">⚡</span> <span>Gemini 3.8 & 2.5 Flash</span>
                </div>
                <div style="background: #F5F5ED; border: 1px solid #E5E5DC;
                            border-radius: 12px; padding: 0.45rem 0.85rem;
                            font-size: 0.82rem; color: #1A1A1A; font-weight: 700;
                            display: flex; align-items: center; gap: 0.4rem; box-shadow: 0 2px 4px rgba(26,26,26,0.03);">
                    <span style="color: #046A38;">📖</span> <span>Automated PDF, EPUB & DOCX</span>
                </div>
                <div style="background: #F5F5ED; border: 1px solid #E5E5DC;
                            border-radius: 12px; padding: 0.45rem 0.85rem;
                            font-size: 0.82rem; color: #1A1A1A; font-weight: 700;
                            display: flex; align-items: center; gap: 0.4rem; box-shadow: 0 2px 4px rgba(26,26,26,0.03);">
                    <span style="color: #E34234;">🎨</span> <span>3D Neural Spine Studio</span>
                </div>
            </div>
        </div>
        """
        render_html(hero_card_html)

        render_html("<div style='height: 0.75rem;'></div>")

        col_cta, col_sec = st.columns([1.3, 1.1])
        with col_cta:
            if st.button(f"🚀 {cms['cta_text']}", key="hero_cta", use_container_width=True, type="primary"):
                if not st.session_state.get("logged_in"):
                    st.session_state["show_login"] = True
                else:
                    st.session_state["nav_page"] = "creator"
                st.rerun()

        with col_sec:
            if st.button("✨ Explore Core Engines", key="hero_sec_cta", use_container_width=True):
                st.session_state["nav_page"] = "landing"
                st.session_state["nav_section"] = "engines"
                st.rerun()

    # Metrics Counter Banner in Warm Ivory
    metrics_cms = _get_cms("metrics", {
        "m1_val": "10K+", "m1_lbl": "Covers Scanned",
        "m2_val": "50K+", "m2_lbl": "AI Summaries Generated",
        "m3_val": "3K+", "m3_lbl": "Authors Publishing",
        "m4_val": "99.4%", "m4_lbl": "Platform Satisfaction",
    })

    metrics_html = f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; padding: 1.75rem 2rem;
                background: #FFFFFF; border-radius: 20px; margin: 2.5rem 0;
                box-shadow: 0 10px 30px -5px rgba(26, 26, 26, 0.05);
                border: 1.5px solid #E5E5DC;">
        <div style="text-align: center;">
            <div style="font-size: 2.2rem; font-weight: 900; color: #046A38;">{metrics_cms['m1_val']}</div>
            <div style="font-size: 0.85rem; color: {TEXT_SECONDARY}; font-weight: 700; margin-top: 0.25rem;">{metrics_cms['m1_lbl']}</div>
        </div>
        <div style="text-align: center; border-left: 1.5px solid #E5E5DC;">
            <div style="font-size: 2.2rem; font-weight: 900; color: #E34234;">{metrics_cms['m2_val']}</div>
            <div style="font-size: 0.85rem; color: {TEXT_SECONDARY}; font-weight: 700; margin-top: 0.25rem;">{metrics_cms['m2_lbl']}</div>
        </div>
        <div style="text-align: center; border-left: 1.5px solid #E5E5DC;">
            <div style="font-size: 2.2rem; font-weight: 900; color: #046A38;">{metrics_cms['m3_val']}</div>
            <div style="font-size: 0.85rem; color: {TEXT_SECONDARY}; font-weight: 700; margin-top: 0.25rem;">{metrics_cms['m3_lbl']}</div>
        </div>
        <div style="text-align: center; border-left: 1.5px solid #E5E5DC;">
            <div style="font-size: 2.2rem; font-weight: 900; color: #046A38;">{metrics_cms['m4_val']}</div>
            <div style="font-size: 0.85rem; color: {TEXT_SECONDARY}; font-weight: 700; margin-top: 0.25rem;">{metrics_cms['m4_lbl']}</div>
        </div>
    </div>
    """
    render_html(metrics_html)


# ==============================================================================
# 5 CORE HIGH-PRECISION FEATURES (3 READER TOOLS + 2 WRITER TOOLS)
# ==============================================================================
def _render_home_expanded_features():
    st.markdown("""
    <div style="text-align: center; margin: 3.5rem 0 1.75rem 0;">
        <div style="font-size: 0.85rem; color: #046A38; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.4rem;">
            THE 5 CORE ARCHITECTURAL ENGINES
        </div>
        <div style="font-size: 2.3rem; font-weight: 900; color: #1A1A1A; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
            Precision AI Engines for Readers & Writers
        </div>
        <div style="font-size: 0.95rem; color: #4A4A4A; max-width: 680px; margin: 0 auto; line-height: 1.6;">
            A streamlined ecosystem focused on 5 high-precision tools: 3 intelligent discovery engines for readers, and 2 production-grade studios for authors.
        </div>
    </div>
    """, unsafe_allow_html=True)

    suite_features = [
        ("🔍", "Smart Book Search Engine", "Reader Tool 1: Instant search across 60,000+ free Project Gutenberg & Open Library books with direct read/download links.", "reader", "Search Books"),
        ("🤖", "Reader AI Book Assistant", "Reader Tool 2: Deep literary summaries, chapter breakdowns, author background, and conversational knowledge for any book.", "reader", "Consult AI Assistant"),
        ("📷", "Visual Book Cover Scanner", "Reader Tool 3: Live camera scanner & image uploader using Gemini Vision to identify covers and provide digital PDFs immediately.", "reader", "Scan Book Cover"),
        ("🎨", "Interactive Book Editor & Studio", "Writer Tool 1: CapCut-style template workflow (Modern, Classic, Academic, Minimalist) with integrated AI Co-Pilot and multi-format export.", "creator", "Open Design Studio"),
        ("🚀", "Automated Full Book Generator", "Writer Tool 2: 1-Click engine turning raw manuscripts into complete publish-ready books with Cover, Copyright, Auto TOC, Chapters & Blurb.", "creator", "Generate Full Book"),
    ]

    cols_top = st.columns(3)
    for j, (icon, title, desc, target_route, btn_label) in enumerate(suite_features[:3]):
        with cols_top[j]:
            render_html(f"""
            <div style="background: #FFFFFF; border-radius: 18px; padding: 1.65rem; border: 1.5px solid #E5E5DC;
                        box-shadow: 0 8px 24px -6px rgba(26, 26, 26, 0.05); margin-bottom: 0.85rem; min-height: 220px;
                        display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 2.2rem;">{icon}</span>
                        <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; font-size: 0.7rem; font-weight: 800; padding: 0.2rem 0.55rem; border-radius: 9999px;">READER TOOL</span>
                    </div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #1A1A1A; margin-bottom: 0.45rem;">
                        {title}
                    </div>
                    <div style="font-size: 0.88rem; color: #4A4A4A; line-height: 1.6; margin-bottom: 1rem;">
                        {desc}
                    </div>
                </div>
            </div>
            """)
            if st.button(f"Launch {btn_label} →", key=f"suite_feat_btn_{j}", use_container_width=True, type="primary" if j == 0 else "secondary"):
                st.session_state["nav_page"] = target_route
                st.rerun()

    cols_bottom = st.columns(2)
    for k, (icon, title, desc, target_route, btn_label) in enumerate(suite_features[3:]):
        with cols_bottom[k]:
            render_html(f"""
            <div style="background: #FFFFFF; border-radius: 18px; padding: 1.65rem; border: 1.5px solid #E5E5DC;
                        box-shadow: 0 8px 24px -6px rgba(26, 26, 26, 0.05); margin-bottom: 0.85rem; min-height: 220px;
                        display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 2.2rem;">{icon}</span>
                        <span style="background: rgba(227, 66, 52, 0.08); color: #E34234; font-size: 0.7rem; font-weight: 800; padding: 0.2rem 0.55rem; border-radius: 9999px;">WRITER ENGINE</span>
                    </div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #1A1A1A; margin-bottom: 0.45rem;">
                        {title}
                    </div>
                    <div style="font-size: 0.88rem; color: #4A4A4A; line-height: 1.6; margin-bottom: 1rem;">
                        {desc}
                    </div>
                </div>
            </div>
            """)
            if st.button(f"Launch {btn_label} →", key=f"suite_feat_btn_{3+k}", use_container_width=True, type="primary"):
                st.session_state["nav_page"] = target_route
                st.rerun()


# ==============================================================================
# "THE VISION" & FOUNDING TEAM SHOWCASE
# ==============================================================================
def _render_vision():
    cms = _get_cms("vision", {
        "heading": "Meet the Visionaries Behind the AI Authoring Engine",
        "body": "Our core mission is to empower first-time authors, researchers, and creators with automated research, chapter formatting, and cover designs. We believe every great idea deserves to be a beautifully published book.",
    })

    vision_header_html = """
    <div style="text-align: center; margin: 3.5rem 0 1.5rem 0;">
        <div style="display: inline-block; border-bottom: 2.5px solid #046A38; padding-bottom: 0.4rem;
                    color: #046A38; font-size: 0.85rem; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;">
            The Vision
        </div>
        <div style="font-size: 2.3rem; font-weight: 900; color: #1A1A1A; margin-top: 0.6rem; letter-spacing: -0.02em;">
            Meet the Engineers Behind Pen2Publish AI
        </div>
    </div>
    """
    render_html(vision_header_html)

    vision_left_html = f"""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                border-radius: 24px; padding: 2.25rem; box-shadow: 0 10px 30px -10px rgba(26,26,26,0.05); margin-bottom: 2rem;">
        <div style="font-size: 1.85rem; font-weight: 900; color: #1A1A1A; line-height: 1.25; margin-bottom: 1.15rem;">
            {cms['heading']}
        </div>
        <div style="font-size: 1.02rem; color: #333333; line-height: 1.8; margin-bottom: 1.25rem;">
            {cms['body']}
        </div>
        <div style="font-size: 0.95rem; color: #5C5C5C; line-height: 1.8; margin-bottom: 1.5rem;">
            Pen2Publish AI simplifies the entire publishing workflow — from raw outline to beautifully structured,
            formatted manuscript — using cutting-edge Gemini AI acting as your autonomous co-author, editor, and designer.
        </div>
        <div style="display: flex; gap: 0.85rem; flex-wrap: wrap;">
            <div style="background: #F5F5ED; border: 1px solid #E5E5DC;
                        border-radius: 12px; padding: 0.85rem 1.35rem; font-size: 0.88rem; color: #046A38; font-weight: 700;">
                ✅ Automated Research Engine
            </div>
            <div style="background: #F5F5ED; border: 1px solid #E5E5DC;
                        border-radius: 12px; padding: 0.85rem 1.35rem; font-size: 0.88rem; color: #046A38; font-weight: 700;">
                ✅ Smart Chapter Formatting
            </div>
            <div style="background: #F5F5ED; border: 1px solid #E5E5DC;
                        border-radius: 12px; padding: 0.85rem 1.35rem; font-size: 0.88rem; color: #046A38; font-weight: 700;">
                ✅ 3D Neural Cover Studio
            </div>
        </div>
    </div>
    """
    render_html(vision_left_html)


def _render_team_showcase():
    team_cms = _get_cms("team", {})

    team_members = [
        {
            "name": team_cms.get("m0_name", "Shahbaz Ali"),
            "role": team_cms.get("m0_role", "System Architect & AI/Cloud Engineer"),
            "initial": "S",
            "color": "linear-gradient(135deg, #046A38 0%, #0F5257 100%)",
            "bio": team_cms.get("m0_bio", "Core Logic Architect for the entire platform. Great experience in building logic for the whole project, with expertise in Cloud Computing infrastructure, scalable systems, and Generative AI integration (gemini-3.8-flash)."),
            "badge": "SYSTEM ARCHITECT",
            "skills": ["Gemini 3.8 Flash", "Cloud Infrastructure", "Core Logic Engine"]
        },
        {
            "name": team_cms.get("m1_name", "Huzaifa Tanveer"),
            "role": team_cms.get("m1_role", "Cybersecurity & Infrastructure Lead"),
            "initial": "H",
            "color": "linear-gradient(135deg, #E34234 0%, #D9381E 100%)",
            "bio": team_cms.get("m1_bio", "Great experience with Cybersecurity, Ethical Hacking, system hardening, secure data hashing, and extensive knowledge about industry standards."),
            "badge": "CYBERSECURITY LEAD",
            "skills": ["System Hardening", "Ethical Hacking", "Secure Hashing & Auth"]
        },
        {
            "name": team_cms.get("m2_name", "Arsalan Rasheed Abbasi"),
            "role": team_cms.get("m2_role", "Systems Upgrade & Lifecycle Engineer"),
            "initial": "A",
            "color": "linear-gradient(135deg, #0F5257 0%, #046A38 100%)",
            "bio": team_cms.get("m2_bio", "Specialist in updates, upgrades, feature maintenance, CI/CD pipelines, and continuous software lifecycle optimization for the project."),
            "badge": "LIFECYCLE & UPGRADES",
            "skills": ["CI/CD Pipelines", "Lifecycle Optimization", "Feature Maintenance"]
        }
    ]

    t1, t2, t3 = st.columns(3)

    for col, m in zip([t1, t2, t3], team_members):
        with col:
            skills_html = "".join([f"<span style='background: #F5F5ED; color: #046A38; font-size: 0.74rem; padding: 0.25rem 0.6rem; border-radius: 9999px; font-weight: 700; border: 1px solid #E5E5DC;'>{s}</span>" for s in m["skills"]])
            render_html(f"""
            <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                        border-radius: 22px; padding: 2.25rem 1.75rem; text-align: center;
                        box-shadow: 0 12px 30px -8px rgba(26, 26, 26, 0.06); min-height: 420px;
                        display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: inline-block; background: rgba(4, 106, 56, 0.08); color: #046A38; font-size: 0.7rem; font-weight: 800; padding: 0.22rem 0.65rem; border-radius: 9999px; border: 1px solid rgba(4, 106, 56, 0.28); margin-bottom: 1.1rem; letter-spacing: 0.05em;">
                        {m['badge']}
                    </div>
                    <div style="width: 86px; height: 86px; border-radius: 50%; margin: 0 auto 1.25rem auto;
                                background: {m['color']}; display: flex; align-items: center; justify-content: center;
                                font-size: 2.4rem; font-weight: 900; color: #FAFAF5;
                                box-shadow: 0 8px 20px rgba(4, 106, 56, 0.25); border: 3px solid #FFFFFF;">
                        {m['initial']}
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 900; color: #1A1A1A; margin-bottom: 0.3rem;">
                        {m['name']}
                    </div>
                    <div style="font-size: 0.86rem; color: #046A38; font-weight: 700; margin-bottom: 1rem;">
                        {m['role']}
                    </div>
                    <div style="font-size: 0.88rem; color: #4A4A4A; line-height: 1.65; margin-bottom: 1.25rem;">
                        {m['bio']}
                    </div>
                </div>
                <div style="display: flex; gap: 0.4rem; justify-content: center; flex-wrap: wrap; padding-top: 1rem; border-top: 1.5px solid #F0F0E8;">
                    {skills_html}
                </div>
            </div>
            """)


# ==============================================================================
# "CORE ENGINES & AI AUTHORING SUITE" SECTION (RENAMED FROM PORTFOLIO)
# ==============================================================================
def _render_core_engines_page():
    port_header = f"""
    <div style="text-align: center; margin: 1.5rem 0 2.5rem 0;">
        <div style="font-size: 0.85rem; color: #046A38; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.4rem;">
            SYSTEM ARCHITECTURE & PRODUCTION MODULES
        </div>
        <div style="font-size: 2.4rem; font-weight: 900; color: #1A1A1A; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
            Core Engines & AI Authoring Suite
        </div>
        <div style="font-size: 1rem; color: {TEXT_SECONDARY}; max-width: 680px; margin: 0 auto; line-height: 1.6;">
            A streamlined ecosystem of 5 core precision tools: 3 intelligent discovery engines for readers, and 2 production-grade authoring studios for writers.
        </div>
    </div>
    """
    render_html(port_header)
    _render_core_engines_grid()


def _render_core_engines_grid():
    default_items = [
        ("🔍", "Smart Book Search Engine",
         "Search 60,000+ public domain literary works across Project Gutenberg and Open Library with instant cover previews and direct reading links.",
         "Search Library", "reader"),
        ("🤖", "Reader AI Book Assistant",
         "Query our conversational literary AI for deep book summaries, top 5 key takeaways, chapter-by-chapter breakdowns, and author historical context.",
         "Consult Assistant", "reader"),
        ("📷", "Visual Book Cover Scanner",
         "Point your live camera or upload any physical book cover. Gemini Vision AI identifies titles and author bylines, retrieving digital copies immediately.",
         "Scan Book Cover", "reader"),
        ("🎨", "Interactive Book Editor & Studio",
         "CapCut-style template workflow (Modern Non-Fiction, Classic Novel, Academic, Minimalist) with integrated AI Co-Pilot drawer and multi-format export.",
         "Open Design Studio", "creator"),
        ("🚀", "Automated Full Book Generator",
         "Paste complete manuscripts of 50 to 500+ pages. With one click, compile a publish-ready book with Front Cover, Copyright, Auto TOC, Chapters, and Blurb.",
         "Generate Full Book", "creator"),
    ]

    engines_cms = _get_cms("engines", {})

    cols_top = st.columns(3)
    for j, (icon, title, desc, btn_label, nav_target) in enumerate(default_items[:3]):
        db_icon = engines_cms.get(f"item_{j}_icon", icon)
        db_title = engines_cms.get(f"item_{j}_title", title)
        db_desc = engines_cms.get(f"item_{j}_desc", desc)

        with cols_top[j]:
            card_html = f"""
            <div style="background: #FFFFFF; border-radius: 20px; padding: 2rem; border: 1.5px solid #E5E5DC;
                        box-shadow: 0 10px 25px -5px rgba(26, 26, 26, 0.05); margin-bottom: 0.85rem; min-height: 230px;
                        display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                        <div style="font-size: 2.6rem;">{db_icon}</div>
                        <span style="font-size: 0.72rem; background: rgba(4, 106, 56, 0.08); color: #046A38;
                                     border: 1px solid rgba(4, 106, 56, 0.28); padding: 0.2rem 0.65rem; border-radius: 9999px; font-weight: 800;">
                            READER TOOL
                        </span>
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #1A1A1A; margin-bottom: 0.6rem;">
                        {db_title}
                    </div>
                    <div style="font-size: 0.92rem; color: #4A4A4A; line-height: 1.65; margin-bottom: 1.25rem;">
                        {db_desc}
                    </div>
                </div>
            </div>
            """
            render_html(card_html)
            if st.button(f"Launch {btn_label} →", key=f"engine_launch_{j}", use_container_width=True, type="primary" if j == 0 else "secondary"):
                st.session_state["nav_page"] = nav_target
                st.session_state["active_reader_tab"] = j
                st.rerun()

    cols_bottom = st.columns(2)
    for k, (icon, title, desc, btn_label, nav_target) in enumerate(default_items[3:]):
        db_icon = engines_cms.get(f"item_{3+k}_icon", icon)
        db_title = engines_cms.get(f"item_{3+k}_title", title)
        db_desc = engines_cms.get(f"item_{3+k}_desc", desc)

        with cols_bottom[k]:
            card_html = f"""
            <div style="background: #FFFFFF; border-radius: 20px; padding: 2rem; border: 1.5px solid #E5E5DC;
                        box-shadow: 0 10px 25px -5px rgba(26, 26, 26, 0.05); margin-bottom: 0.85rem; min-height: 230px;
                        display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                        <div style="font-size: 2.6rem;">{db_icon}</div>
                        <span style="font-size: 0.72rem; background: rgba(227, 66, 52, 0.08); color: #E34234;
                                     border: 1px solid rgba(227, 66, 52, 0.28); padding: 0.2rem 0.65rem; border-radius: 9999px; font-weight: 800;">
                            WRITER ENGINE
                        </span>
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #1A1A1A; margin-bottom: 0.6rem;">
                        {db_title}
                    </div>
                    <div style="font-size: 0.92rem; color: #4A4A4A; line-height: 1.65; margin-bottom: 1.25rem;">
                        {db_desc}
                    </div>
                </div>
            </div>
            """
            render_html(card_html)
            if st.button(f"Launch {btn_label} →", key=f"engine_launch_{3+k}", use_container_width=True, type="primary"):
                st.session_state["nav_page"] = nav_target
                st.rerun()


# ==============================================================================
# PACKAGES & MEMBERSHIP TIERS
# ==============================================================================
def _render_packages():
    pkg_header = f"""
    <div style="text-align: center; margin: 1.5rem 0 2.5rem 0;">
        <div style="font-size: 0.85rem; color: #046A38; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.4rem;">
            TRANSPARENT VALUE PLANS
        </div>
        <div style="font-size: 2.4rem; font-weight: 900; color: #1A1A1A; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
            Packages & Pricing
        </div>
        <div style="font-size: 1rem; color: {TEXT_SECONDARY}; max-width: 600px; margin: 0 auto;">
            Transparent, scalable tiers designed for indie authors, researchers, and professional publishers.
        </div>
    </div>
    """
    render_html(pkg_header)

    tiers = _get_dynamic_pricing()
    tier_keys = list(tiers.keys())
    num_cols = min(len(tier_keys), 4)
    cols = st.columns(num_cols)

    for i, tier_name in enumerate(tier_keys[:4]):
        tier = tiers[tier_name]
        with cols[i]:
            is_featured = tier.get("featured", False)
            border_css = "border: 2px solid #E34234; box-shadow: 0 10px 30px rgba(227, 66, 52, 0.15);" if is_featured else "border: 1.5px solid #E5E5DC; box-shadow: 0 4px 15px rgba(26,26,26,0.04);"
            badge_html = '<div style="background: rgba(227, 66, 52, 0.1); color: #E34234; border: 1px solid rgba(227, 66, 52, 0.35); padding: 0.25rem 0.9rem; border-radius: 20px; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.05em; display: inline-block; margin-bottom: 0.75rem; text-transform: uppercase;">✦ Most Popular</div>' if is_featured else '<div style="height: 28px;"></div>'

            price_val = tier.get("price", 0)
            period_val = tier.get("period", "month")
            price_str = f"${price_val}" if price_val > 0 else "FREE"
            period_str = f"/{period_val}" if price_val > 0 else ""

            features_list = tier.get("features", [])
            features_html = ""
            for feat in features_list:
                if isinstance(feat, list) and len(feat) >= 2:
                    icon_color = "#046A38" if feat[0] == "✅" else "#94A3B8"
                    features_html += f'<div style="font-size: 0.85rem; color: #333333; padding: 0.45rem 0; border-bottom: 1px solid #F0F0E8; display: flex; gap: 0.5rem;"><span style="color:{icon_color}; font-weight:bold;">{feat[0]}</span> <span>{feat[1]}</span></div>'
                elif isinstance(feat, str):
                    features_html += f'<div style="font-size: 0.85rem; color: #333333; padding: 0.45rem 0; border-bottom: 1px solid #F0F0E8;">{feat}</div>'

            tier_card_html = f"""
            <div style="background: #FFFFFF; border-radius: 22px; padding: 2rem 1.25rem; {border_css}
                        text-align: center; min-height: 440px; margin-bottom: 1rem;">
                {badge_html}
                <div style="font-size: 1.35rem; font-weight: 800; color: #1A1A1A;">{tier_name}</div>
                <div style="font-size: 2.5rem; font-weight: 900; color: #046A38; margin: 0.75rem 0;">
                    {price_str}<span style="font-size: 0.9rem; color: #737373; font-weight: 500;">{period_str}</span>
                </div>
                <div style="text-align: left; margin-top: 1.5rem;">
                    {features_html}
                </div>
            </div>
            """
            render_html(tier_card_html)

            btn_type = "primary" if is_featured else "secondary"
            if st.button(f"Select {tier_name}", key=f"tier_select_btn_{i}", use_container_width=True, type=btn_type):
                if not st.session_state.get("logged_in"):
                    st.session_state["show_login"] = True
                else:
                    st.session_state["nav_page"] = "creator"
                st.rerun()


# ==============================================================================
# BOOK A CALL CONSULTATION
# ==============================================================================
def _render_book_call():
    call_cms = _get_cms("book_call", {
        "title": "Book a 1-on-1 Consultation",
        "subtitle": "Speak directly with our AI publishing architects to map out your book, workflow, or custom integration.",
        "office": "Pen2Publish AI Systems, San Francisco & Islamabad",
        "email": "advisory@pen2publish.ai",
        "response": "Under 4 Hours (Monday – Saturday)",
        "perk": "✦ 100% Free 30-Minute Architecture & Publishing Discovery Session"
    })

    call_header = f"""
    <div style="text-align: center; margin: 1.5rem 0 2.5rem 0;">
        <div style="font-size: 0.85rem; color: #046A38; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.4rem;">
            DIRECT ARCHITECTURAL ADVISORY
        </div>
        <div style="font-size: 2.4rem; font-weight: 900; color: #1A1A1A; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
            {call_cms['title']}
        </div>
        <div style="font-size: 1rem; color: {TEXT_SECONDARY}; max-width: 600px; margin: 0 auto; line-height: 1.6;">
            {call_cms['subtitle']}
        </div>
    </div>
    """
    render_html(call_header)

    col_left, col_right = st.columns([1, 1.2], gap="large")

    with col_left:
        info_html = f"""
        <div style="background: #FFFFFF; border-radius: 20px; padding: 2.25rem; border: 1.5px solid #E5E5DC;
                    box-shadow: 0 10px 30px -10px rgba(26, 26, 26, 0.05); height: 100%;">
            <div style="font-size: 1.4rem; font-weight: 800; margin-bottom: 1.5rem; color: #1A1A1A;">
                Direct Advisory & Support
            </div>
            <div style="font-size: 0.95rem; color: #333333; line-height: 2.4;">
                <strong style="color: #046A38;">📍 Global Engineering Hub:</strong><br>
                {call_cms['office']}<br><br>
                <strong style="color: #046A38;">📧 Core Founders Line:</strong><br>
                {call_cms['email']}<br><br>
                <strong style="color: #046A38;">🕒 Response Window:</strong><br>
                {call_cms['response']}
            </div>
            <div style="margin-top: 2rem; padding: 1.25rem; background: rgba(4, 106, 56, 0.08);
                        border-radius: 14px; border: 1px solid rgba(4, 106, 56, 0.28); font-size: 0.88rem; color: #046A38; font-weight: 700;">
                {call_cms['perk']}
            </div>
        </div>
        """
        render_html(info_html)

    with col_right:
        with st.form("contact_form"):
            st.markdown("##### Complete Consultation Request")
            name = st.text_input("Full Name *", key="contact_name", placeholder="e.g. Dr. Jennifer Hayes")
            email = st.text_input("Email Address *", key="contact_email", placeholder="author@domain.com")
            preferred_time = st.text_input("Preferred Date & Time *", placeholder="e.g. Thursday 3:00 PM EST", key="contact_time")
            project_details = st.text_area("Book Concept or System Needs", height=90,
                                           placeholder="Describe your book genre, target audience, or desired publishing goals...",
                                           key="contact_project")

            submitted = st.form_submit_button("Confirm Consultation Call", use_container_width=True, type="primary")

            if submitted:
                if name and email and preferred_time:
                    try:
                        admin_db.add_booking_lead(name, email, preferred_time, project_details)
                    except Exception:
                        pass
                    st.success(f"✅ Consultation Confirmed! Thank you {name}. Our team has recorded your session for {preferred_time} and sent confirmation details to {email}.")
                else:
                    st.warning("Please fill in all required fields marked with (*)")


# ==============================================================================
# TESTIMONIALS & FAQ
# ==============================================================================
def _render_testimonials():
    test_header = f"""
    <div style="text-align: center; margin: 3.5rem 0 2rem 0;">
        <div style="font-size: 2.2rem; font-weight: 900; color: #1A1A1A; margin-bottom: 0.5rem;">
            What Published Authors Say
        </div>
        <div style="font-size: 0.95rem; color: {TEXT_SECONDARY};">
            Trusted by indie writers, academic researchers, and content creators worldwide
        </div>
    </div>
    """
    render_html(test_header)

    default_testimonials = [
        ("Dr. Jennifer Hayes", "Academic Author & Book Blogger", "The book formatter and 3D preview saved me weeks of manual work. Uploaded raw research papers, received a structured manuscript in minutes."),
        ("David Chen", "Sci-Fi Indie Author", "The Creator Studio gave me the structure I was missing for 3 years. It generated cohesive chapter outlines and a phenomenal cover concept."),
        ("Aisha Patel", "AI Researcher & Speaker", "The literary assistant chatbot acts like having an Oxford editor on standby 24/7. It identified character plot holes instantly."),
    ]

    test_cms = _get_cms("testimonials", {})

    cols = st.columns(3)
    for i in range(3):
        author = test_cms.get(f"t_{i}_author", default_testimonials[i][0])
        role = test_cms.get(f"t_{i}_role", default_testimonials[i][1])
        text = test_cms.get(f"t_{i}_text", default_testimonials[i][2])

        with cols[i]:
            card_html = f"""
            <div style="background: #FFFFFF; border-radius: 20px; padding: 2rem; border: 1.5px solid #E5E5DC;
                        margin-bottom: 1rem; min-height: 230px; box-shadow: 0 10px 25px -10px rgba(26, 26, 26, 0.05);">
                <div style="font-size: 2.2rem; color: #E34234; margin-bottom: 0.5rem; line-height: 1; font-weight: bold;">"</div>
                <div style="font-size: 0.92rem; color: #333333; line-height: 1.7; margin-bottom: 1.5rem;">
                    {text}
                </div>
                <div style="display: flex; align-items: center; gap: 0.85rem;">
                    <div style="width: 44px; height: 44px; border-radius: 50%;
                                background: linear-gradient(135deg, #046A38 0%, #0F5257 100%);
                                display: flex; align-items: center; justify-content: center;
                                color: white; font-weight: 800; font-size: 1rem;
                                border: 2px solid rgba(4, 106, 56, 0.4);">
                        {author[0].upper() if author else 'U'}
                    </div>
                    <div>
                        <div style="font-size: 0.95rem; font-weight: 800; color: #1A1A1A;">{author}</div>
                        <div style="font-size: 0.8rem; color: #046A38; font-weight: 700;">{role}</div>
                    </div>
                </div>
            </div>
            """
            render_html(card_html)


def _render_faq():
    faq_header = f"""
    <div style="text-align: center; margin: 3.5rem 0 2rem 0;">
        <div style="font-size: 2.2rem; font-weight: 900; color: #1A1A1A; margin-bottom: 0.5rem;">
            Frequently Asked Questions
        </div>
        <div style="font-size: 0.95rem; color: {TEXT_SECONDARY};">
            Everything you need to know about Pen2Publish AI and our agentic authoring suite
        </div>
    </div>
    """
    render_html(faq_header)

    default_faqs = [
        ("How does the 3D Book Viewer and Cover Scanner work?", "Our 3D viewer renders your book in spatial WebGL so you can rotate it 360 degrees. The OCR cover scanner utilizes Gemini Vision AI to extract titles and authors from live camera frames or uploads in milliseconds."),
        ("Can I generate and format an entire manuscript?", "Yes. You can upload raw thoughts, text notes, or research documents. The Creator Studio structures them into numbered chapters, adds titles, generates table of contents, and produces clean PDF, EPUB, and Word DOCX exports."),
        ("What makes the Pen2Publish AI engine unique?", "Unlike generic chatbots, our platform orchestrates specialized multi-agent subtasks: research synthesis, tone-polishing, chapter structuring, world-building lore bibles, and cover artwork synthesis via Gemini models."),
        ("Is the Free Tier really unlimited forever?", "Yes! You receive free daily book searches, AI summaries, and cover scanner access every single day with no credit card required."),
        ("How does the consultation call work?", "When you book a call, our team prepares an architecture evaluation for your book project and conducts a 30-minute strategic walkthrough via Google Meet."),
    ]

    faq_cms = _get_cms("faq", {})
    faq_count = len([k for k in faq_cms if k.startswith("q_")])
    num_faqs = max(faq_count, len(default_faqs))

    for i in range(num_faqs):
        q = faq_cms.get(f"q_{i}", default_faqs[i][0] if i < len(default_faqs) else "")
        a = faq_cms.get(f"a_{i}", default_faqs[i][1] if i < len(default_faqs) else "")
        if q:
            with st.expander(f"✦ {q}"):
                render_html(f"<div style='color: #333333; line-height: 1.7; font-size: 0.92rem; padding: 0.5rem 0;'>{a}</div>")


def _render_footer():
    footer_html = f"""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                padding: 2.75rem; border-radius: 24px; text-align: center; color: #1A1A1A; margin-top: 4rem;
                box-shadow: 0 10px 30px -10px rgba(26, 26, 26, 0.05);">
        <div style="font-size: 1.6rem; font-weight: 900; margin-bottom: 0.5rem; letter-spacing: -0.01em; color: #1A1A1A;">
            📚 PEN2PUBLISH <span style="color: #046A38;">AI</span> · Autonomous Authoring & Book Discovery Engine
        </div>
        <div style="font-size: 0.92rem; color: {TEXT_SECONDARY}; max-width: 520px; margin: 0 auto 1.5rem auto;">
            Empowering the next generation of authors with autonomous agentic intelligence.
        </div>
        <div style="font-size: 0.82rem; color: #737373;">
            © 2026 Pen2Publish AI Systems · Final Year Project · All Rights Reserved
        </div>
    </div>
    """
    render_html(footer_html)
