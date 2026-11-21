import streamlit as st
from utils.helpers import init_session_state
from utils.styles import (
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, SECONDARY, ACCENT,
    BORDER, BUTTON_GRADIENT, TEXT_PRIMARY,
    TEXT_SECONDARY, render_html
)
from database.db_handler import (
    get_marketplace_books, publish_book_to_marketplace, increment_marketplace_views,
    get_user_quota, set_user_subscription, consume_user_credit,
    get_author_analytics, log_author_event
)


def render_platform_view():
    init_session_state()

    # Warm Ivory & Luxury Emerald Header Banner
    render_html(f"""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                border-radius: 20px; padding: 2rem 2.25rem;
                margin-bottom: 1.75rem;
                box-shadow: 0 10px 30px -10px rgba(26, 26, 26, 0.06);">
        <div style="display: inline-block; background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28);
                    font-size: 0.82rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;
                    padding: 0.25rem 0.75rem; border-radius: 9999px; margin-bottom: 0.5rem;">
            PEN2PUBLISH ECOSYSTEM
        </div>
        <div style="font-size: 2.1rem; font-weight: 900; color: #1A1A1A; letter-spacing: -0.02em;">
            🌐 Platform, Marketplace & Author Analytics
        </div>
        <div style="font-size: 0.95rem; color: #4A4A4A; margin-top: 0.35rem; max-width: 800px; line-height: 1.6;">
            Browse the public author marketplace, manage freemium daily quotas and tier subscriptions, and inspect real-time author analytics on book previews, searches, and multi-format exports.
        </div>
    </div>
    """)

    tabs = st.tabs([
        "🏪 Author Marketplace & Showcase",
        "💳 Freemium Credits & Plans",
        "📊 Author Analytics Dashboard"
    ])

    with tabs[0]:
        _render_marketplace_tab()

    with tabs[1]:
        _render_subscription_tab()

    with tabs[2]:
        _render_analytics_tab()


# ==============================================================================
# TAB 1: AUTHOR MARKETPLACE & SHOWCASE
# ==============================================================================
def _render_marketplace_tab():
    user_id = st.session_state.get("user_id", 1)
    username = st.session_state.get("username", "Author")

    st.markdown("### 🏪 Author Showcase Directory")
    st.caption("Publicly showcased publications authored, structured, and compiled directly on Pen2Publish AI.")

    col_filter1, col_filter2, col_pub_btn = st.columns([1.5, 2, 1.2])

    with col_filter1:
        genre_filter = st.selectbox(
            "Filter by Genre:",
            ["All Genres", "Technology & AI", "Sci-Fi Cyberpunk", "Dark Fantasy", "Self-Help & Productivity", "Fiction"],
            key="market_genre_filter"
        )
    with col_filter2:
        search_filter = st.text_input(
            "Search Titles or Authors:",
            placeholder="e.g., Agentic AI, Elena Vance...",
            key="market_search_input"
        )
    with col_pub_btn:
        st.write("")
        st.write("")
        show_publish_modal = st.checkbox("➕ Publish Book", key="chk_show_publish")

    if show_publish_modal:
        with st.expander("📝 Publish Your Manuscript to Marketplace", expanded=True):
            p_title = st.text_input("Book Title *", placeholder="e.g., The Autonomous Dawn", key="pub_title")
            p_author = st.text_input("Author Byline *", value=username, key="pub_author")
            p_genre = st.selectbox("Genre *", ["Technology & AI", "Sci-Fi Cyberpunk", "Dark Fantasy", "Self-Help & Productivity", "Fiction"], key="pub_genre")
            p_synopsis = st.text_area("Book Synopsis *", placeholder="Summary of the book...", height=80, key="pub_synopsis")
            p_excerpt = st.text_area("Sample Chapter Excerpt *", placeholder="First 1-2 pages of the manuscript...", height=120, key="pub_excerpt")
            p_cover = st.text_input("Cover Image URL (Optional):", value="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80", key="pub_cover")
            p_price = st.number_input("Listing Price ($0.00 for Free):", min_value=0.0, max_value=49.99, value=0.0, step=0.99, key="pub_price")

            if st.button("🚀 Publish to Showcase Now", key="btn_confirm_publish", type="primary"):
                if p_title.strip() and p_synopsis.strip() and p_excerpt.strip():
                    success, msg = publish_book_to_marketplace(
                        p_author.strip(), p_title.strip(), p_genre,
                        p_synopsis.strip(), p_excerpt.strip(), p_cover.strip(),
                        p_price, user_id=user_id
                    )
                    if success:
                        st.success(f"🎉 '{p_title}' is now live in the Author Marketplace!")
                        log_author_event("preview", f"Published: {p_title}")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in Title, Synopsis, and Excerpt.")

    books = get_marketplace_books(genre=genre_filter, search_query=search_filter)

    if not books:
        st.info("No books match your criteria in the directory.")
    else:
        st.markdown(f"#### 📚 Catalog ({len(books)} Publications)")
        cols = st.columns(2)
        for idx, book in enumerate(books):
            with cols[idx % 2]:
                price_is_free = (book["price"] == 0.0)
                price_tag = "FREE" if price_is_free else f"${book['price']:.2f}"
                badge_bg = "rgba(4, 106, 56, 0.08)" if price_is_free else "rgba(227, 66, 52, 0.08)"
                badge_color = "#046A38" if price_is_free else "#E34234"
                badge_border = "rgba(4, 106, 56, 0.28)" if price_is_free else "rgba(227, 66, 52, 0.28)"

                render_html(f"""
                <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                            border-radius: 16px; padding: 1.35rem; margin-bottom: 1rem;
                            box-shadow: 0 4px 18px rgba(26, 26, 26, 0.04); min-height: 270px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
                            <span style="font-size: 1.25rem; font-weight: 800; color: #1A1A1A; letter-spacing: -0.01em;">
                                {book['title']}
                            </span>
                            <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border};
                                         font-size: 0.75rem; padding: 0.2rem 0.6rem; border-radius: 9999px; font-weight: 800;">
                                {price_tag}
                            </span>
                        </div>
                        <div style="font-size: 0.88rem; color: #046A38; font-weight: 700; margin-bottom: 0.5rem;">
                            by {book['author_name']} · <span style="color: #E34234;">{book['genre']}</span>
                        </div>
                        <div style="font-size: 0.88rem; color: #4A4A4A; line-height: 1.55; margin-bottom: 0.85rem;">
                            {book['synopsis']}
                        </div>
                        <div style="font-size: 0.78rem; color: #737373; margin-bottom: 0.4rem; font-weight: 600;">
                            👀 {book['views_count']} Views · ⬇ {book['downloads_count']} Reader Downloads
                        </div>
                    </div>
                </div>
                """)
                with st.expander(f"📖 Read Sample Excerpt: {book['title']}", expanded=False):
                    increment_marketplace_views(book["id"])
                    st.markdown(f"**Sample Chapter Preview:**\n\n> {book['sample_excerpt']}")
                    if st.button("⬇ Download Reader Copy", key=f"dl_mkt_{book['id']}"):
                        st.success(f"Downloading preview copy of '{book['title']}'...")


# ==============================================================================
# TAB 2: FREEMIUM CREDIT & SUBSCRIPTION MANAGER
# ==============================================================================
def _render_subscription_tab():
    user_id = st.session_state.get("user_id", 1)
    st.markdown("### 💳 Freemium Credit & Subscription Quotas")
    st.caption("Inspect your daily AI consumption quotas, view live tier benefits, and upgrade your tier.")

    quota = get_user_quota(user_id=user_id)
    current_tier = quota.get("subscription_tier", "Free")
    used = quota.get("daily_credits_used", 0)
    max_credits = quota.get("daily_credits_max", 15)

    if current_tier in ("Gold", "Premium"):
        ratio = 0.05
        usage_text = "Unlimited (VIP Plan)"
    else:
        ratio = min(1.0, used / max(1, max_credits))
        usage_text = f"{used} / {max_credits} Credits Consumed Today"

    # Live Quota Card in Clean Warm Ivory / White
    render_html(f"""
    <div style="background: #FFFFFF;
                border: 1.5px solid #E5E5DC; border-radius: 16px; padding: 1.5rem 1.75rem; margin-bottom: 1.5rem;
                box-shadow: 0 6px 20px rgba(26, 26, 26, 0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div>
                <span style="font-size: 0.8rem; color: #046A38; font-weight: 800; text-transform: uppercase;">Current Active Plan</span>
                <div style="font-size: 1.8rem; font-weight: 900; color: #1A1A1A;">{current_tier} Tier</div>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.8rem; color: {TEXT_SECONDARY};">Daily Quota Status</span>
                <div style="font-size: 1.25rem; font-weight: 800; color: #E34234;">{usage_text}</div>
            </div>
        </div>
    </div>
    """)
    st.progress(ratio)

    st.markdown("#### ⚡ Compare & Upgrade Membership Plans")
    p1, p2, p3, p4 = st.columns(4)

    plans = [
        ("Free", "$0", "Forever", ["15 Daily AI Credits", "Basic Vibe Search", "Standard Book Scanner", "Community Support"], "Free", "#737373"),
        ("Standard", "$9.99", "/month", ["75 Daily AI Credits", "Cover Page Generator (10/mo)", "Formatting (20 Pages)", "Unlimited Summaries"], "Standard", "#046A38"),
        ("Gold", "$24.99", "/month", ["300 Daily AI Credits", "Cover Page Generator (50/mo)", "Formatting (50 Pages)", "High-Res Export"], "Gold", "#E34234"),
        ("Premium", "$49.99", "/month", ["Unlimited AI Credits", "All Creator Tools Unlocked", "Priority API Speed", "Unlimited Publishing"], "Premium", "#0F5257")
    ]

    for col, (name, price, period, perks, tier_key, plan_color) in zip([p1, p2, p3, p4], plans):
        with col:
            is_active = (current_tier == tier_key)
            border_color = "#E34234" if is_active else ("#046A38" if name == "Gold" else "#E5E5DC")
            featured_badge = "<div style='background: rgba(227, 66, 52, 0.1); color: #E34234; border: 1px solid rgba(227, 66, 52, 0.35); font-size: 0.68rem; padding: 0.15rem 0.5rem; border-radius: 9999px; font-weight: 800; display: inline-block; margin-bottom: 0.4rem;'>★ MOST POPULAR</div>" if name == "Gold" else ""
            perks_html = "".join([f"<li style='font-size: 0.82rem; color: #4A4A4A; margin-bottom: 0.4rem; list-style-type: none;'>✓ {p}</li>" for p in perks])
            render_html(f"""
            <div style="background: #FFFFFF; border: 2px solid {border_color};
                        border-radius: 14px; padding: 1.25rem; min-height: 310px; display: flex; flex-direction: column; justify-content: space-between;
                        box-shadow: 0 4px 15px rgba(26, 26, 26, 0.04);">
                <div>
                    {featured_badge}
                    <div style="font-weight: 800; color: #1A1A1A; font-size: 1.15rem;">{name}</div>
                    <div style="margin: 0.4rem 0 0.8rem 0;">
                        <span style="font-size: 1.6rem; font-weight: 900; color: #1A1A1A;">{price}</span>
                        <span style="font-size: 0.75rem; color: {TEXT_SECONDARY};">{period}</span>
                    </div>
                    <ul style="padding-left: 0; margin-bottom: 1rem;">
                        {perks_html}
                    </ul>
                </div>
            </div>
            """)
            if is_active:
                st.button("✅ Current Plan", key=f"plan_act_{name}", disabled=True, use_container_width=True)
            else:
                if st.button(f"Upgrade to {name}", key=f"plan_btn_{name}", type="primary" if name in ("Gold", "Premium") else "secondary", use_container_width=True):
                    set_user_subscription(tier_key, user_id=user_id)
                    st.success(f"🎉 Subscribed to {name} Tier!")
                    st.rerun()


# ==============================================================================
# TAB 3: AUTHOR ANALYTICS DASHBOARD
# ==============================================================================
def _render_analytics_tab():
    user_id = st.session_state.get("user_id", 1)
    st.markdown("### 📊 Author Analytics & Telemetry Dashboard")
    st.caption("Live metrics recording reader engagement, book searches, catalog previews, and publication export history.")

    data = get_author_analytics(user_id=user_id)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_html(f"""
        <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                    border-radius: 14px; padding: 1.25rem; text-align: center;
                    box-shadow: 0 4px 14px rgba(26, 26, 26, 0.04);">
            <div style="font-size: 1.8rem; margin-bottom: 0.2rem;">🔍</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #1A1A1A;">{data['searches']}</div>
            <div style="font-size: 0.78rem; color: {TEXT_SECONDARY}; font-weight: 600;">Reader Searches</div>
        </div>
        """)
    with c2:
        render_html(f"""
        <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                    border-radius: 14px; padding: 1.25rem; text-align: center;
                    box-shadow: 0 4px 14px rgba(26, 26, 26, 0.04);">
            <div style="font-size: 1.8rem; margin-bottom: 0.2rem;">👀</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #046A38;">{data['previews']}</div>
            <div style="font-size: 0.78rem; color: {TEXT_SECONDARY}; font-weight: 600;">Catalog Previews</div>
        </div>
        """)
    with c3:
        render_html(f"""
        <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                    border-radius: 14px; padding: 1.25rem; text-align: center;
                    box-shadow: 0 4px 14px rgba(26, 26, 26, 0.04);">
            <div style="font-size: 1.8rem; margin-bottom: 0.2rem;">📦</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #E34234;">{data['exports']}</div>
            <div style="font-size: 0.78rem; color: {TEXT_SECONDARY}; font-weight: 600;">Total Exports</div>
        </div>
        """)
    with c4:
        render_html(f"""
        <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                    border-radius: 14px; padding: 1.25rem; text-align: center;
                    box-shadow: 0 4px 14px rgba(26, 26, 26, 0.04);">
            <div style="font-size: 1.8rem; margin-bottom: 0.2rem;">⚡</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #046A38;">99.8%</div>
            <div style="font-size: 0.78rem; color: {TEXT_SECONDARY}; font-weight: 600;">API Reliability</div>
        </div>
        """)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    col_chart, col_feed = st.columns([1, 1.2], gap="large")

    with col_chart:
        st.markdown("#### 📦 Multi-Format Export Breakdown")
        breakdown = data.get("export_breakdown", {"PDF": 7, "EPUB": 3, "DOCX": 2})

        for fmt, count in breakdown.items():
            st.markdown(f"**{fmt} Exports:** `{count}`")
            st.progress(min(1.0, count / max(1, data['exports'] or 1)))

    with col_feed:
        st.markdown("#### 📋 Recent Telemetry Event Stream")
        recent = data.get("recent", [])
        if not recent:
            st.info("No recorded activity events yet.")
        else:
            for ev in recent:
                icon = {"search": "🔍", "preview": "👀", "export_pdf": "📄", "export_epub": "📱", "export_docx": "📝"}.get(ev['event_type'], "⚡")
                render_html(f"""
                <div style="background: #FAFAF5; border: 1px solid #E5E5DC;
                            border-radius: 10px; padding: 0.65rem 0.95rem; margin-bottom: 0.45rem;
                            display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 0.6rem;">
                        <span>{icon}</span>
                        <span style="font-size: 0.82rem; font-weight: 700; color: #1A1A1A;">{ev['event_type'].upper()}</span>
                        <span style="font-size: 0.8rem; color: #4A4A4A;">{ev.get('target_title', '')}</span>
                    </div>
                    <span style="font-size: 0.72rem; color: #046A38; font-weight: 700;">{str(ev.get('created_at', ''))[:16]}</span>
                </div>
                """)
