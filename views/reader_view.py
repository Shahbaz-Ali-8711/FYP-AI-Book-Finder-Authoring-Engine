import streamlit as st
from utils.helpers import init_session_state
from utils.styles import (
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, SECONDARY, ACCENT,
    BORDER, BUTTON_GRADIENT, TEXT_PRIMARY,
    TEXT_SECONDARY, render_html
)
from modules.search_engine import search_free_books
from modules.chatbot_engine import get_book_deep_insights, stream_book_chatbot
from modules.scanner_engine import scan_and_resolve_book


def render_reader_view():
    init_session_state()

    # Warm Ivory & Luxury Emerald Header Banner
    render_html(f"""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                border-radius: 20px; padding: 2rem 2.25rem;
                margin-bottom: 1.75rem;
                box-shadow: 0 10px 30px -10px rgba(26, 26, 26, 0.05);">
        <div style="display: inline-block; background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28);
                    font-size: 0.82rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;
                    padding: 0.25rem 0.75rem; border-radius: 9999px; margin-bottom: 0.5rem;">
            PEN2PUBLISH READER HUB · 3 HIGH-SPEED TOOLS
        </div>
        <div style="font-size: 2.1rem; font-weight: 900; color: #1A1A1A; letter-spacing: -0.02em;">
            📖 AI Book Discovery & Reading Suite
        </div>
        <div style="font-size: 0.95rem; color: #4A4A4A; margin-top: 0.35rem; max-width: 820px; line-height: 1.6;">
            Search 60,000+ free Gutenberg & Open Library books, chat instantaneously with our streaming AI Book Assistant, or scan physical book covers using ultra-fast live camera OCR.
        </div>
    </div>
    """)

    tabs = st.tabs([
        "🔍 Smart Book Search Engine",
        "🤖 Reader AI Book Assistant",
        "📷 Visual Book Cover Scanner"
    ])

    with tabs[0]:
        _render_search_engine_tab()

    with tabs[1]:
        _render_ai_assistant_tab()

    with tabs[2]:
        _render_cover_scanner_tab()


# ==============================================================================
# FEATURE 1: SMART BOOK SEARCH ENGINE (CACHED, FAST & RESPONSIVE)
# ==============================================================================
def _render_search_engine_tab():
    st.markdown("### 🔍 Smart Book Search Engine")
    st.caption("Search across Project Gutenberg and Open Library with instant cover previews, metadata, and direct public domain read/download links.")

    col_q, col_btn = st.columns([4, 1])
    with col_q:
        search_query = st.text_input(
            "Search by Title, Author, Genre, or Keywords:",
            placeholder="e.g., The Odyssey, Sense and Sensibility, Modern Innovation, Machine Learning...",
            key="reader_search_query_input"
        )
    with col_btn:
        st.write("")
        st.write("")
        run_search = st.button("Search Archive", key="btn_run_reader_search", type="primary", use_container_width=True)

    # Preset suggestions
    st.markdown("""
    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.25rem; font-size: 0.82rem;">
        <span style="color: #737373; font-weight: 600;">Popular Discoveries:</span>
        <span style="background: #F5F5ED; padding: 0.15rem 0.5rem; border-radius: 6px; border: 1px solid #E5E5DC; color: #046A38; font-weight: 600;">The Art of War</span>
        <span style="background: #F5F5ED; padding: 0.15rem 0.5rem; border-radius: 6px; border: 1px solid #E5E5DC; color: #046A38; font-weight: 600;">Pride and Prejudice</span>
        <span style="background: #F5F5ED; padding: 0.15rem 0.5rem; border-radius: 6px; border: 1px solid #E5E5DC; color: #046A38; font-weight: 600;">Metamorphosis</span>
        <span style="background: #F5F5ED; padding: 0.15rem 0.5rem; border-radius: 6px; border: 1px solid #E5E5DC; color: #046A38; font-weight: 600;">Meditations</span>
    </div>
    """, unsafe_allow_html=True)

    if run_search and search_query.strip():
        with st.spinner("Searching Gutenberg and Open Library archives..."):
            results = search_free_books(search_query.strip())
            st.session_state["reader_active_search_results"] = results
            st.session_state["reader_last_search_query"] = search_query.strip()

    results = st.session_state.get("reader_active_search_results", [])
    last_q = st.session_state.get("reader_last_search_query", "")

    if results:
        st.markdown(f"#### 📚 Catalog Results for *'{last_q}'* ({len(results)} Found)")
        cols = st.columns(2)

        for idx, book in enumerate(results):
            with cols[idx % 2]:
                title = book.get("title", "Unknown Title")
                author = book.get("author", "Unknown Author")
                source = book.get("source", "Digital Archive")
                cover = book.get("cover_url")
                is_free = book.get("is_totally_free", False)
                read_link = book.get("read_link") or f"https://www.gutenberg.org/ebooks/search/?query={title.replace(' ', '+')}"
                genres = book.get("genres", "Classic Literature")
                desc = book.get("description", "Public domain literary work available for instant exploration.")

                badge_bg = "rgba(4, 106, 56, 0.08)" if is_free else "rgba(227, 66, 52, 0.08)"
                badge_color = "#046A38" if is_free else "#E34234"
                badge_border = "rgba(4, 106, 56, 0.28)" if is_free else "rgba(227, 66, 52, 0.28)"
                badge_text = "100% FREE E-BOOK" if is_free else "INDEXED ENTRY"

                cover_html = f'<img src="{cover}" style="width: 100px; height: 145px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">' if cover else f'<div style="width: 100px; height: 145px; background: #F5F5ED; border: 1.5px dashed #D4D4CA; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 2rem;">📖</div>'

                render_html(f"""
                <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                            border-radius: 16px; padding: 1.35rem; margin-bottom: 1rem;
                            box-shadow: 0 4px 16px rgba(26, 26, 26, 0.04); min-height: 220px;
                            display: flex; gap: 1.25rem;">
                    <div style="flex-shrink: 0;">
                        {cover_html}
                    </div>
                    <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.25rem;">
                                <div style="font-size: 1.15rem; font-weight: 800; color: #1A1A1A; line-height: 1.3;">
                                    {title}
                                </div>
                                <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border};
                                             font-size: 0.68rem; padding: 0.18rem 0.5rem; border-radius: 9999px; font-weight: 800; white-space: nowrap;">
                                    {badge_text}
                                </span>
                            </div>
                            <div style="font-size: 0.88rem; color: #046A38; font-weight: 700; margin-bottom: 0.45rem;">
                                by {author} · <span style="color: #737373; font-weight: 500;">{genres}</span>
                            </div>
                            <div style="font-size: 0.84rem; color: #4A4A4A; line-height: 1.5; margin-bottom: 0.65rem;">
                                {desc}
                            </div>
                            <div style="font-size: 0.76rem; color: #737373;">
                                🏛️ Source: <strong>{source}</strong>
                            </div>
                        </div>
                    </div>
                </div>
                """)

                c_read, c_ai = st.columns(2)
                with c_read:
                    if is_free:
                        st.markdown(f"""
                        <a href="{read_link}" target="_blank" style="background: #046A38; color: #FFFFFF;
                                   text-decoration: none; padding: 0.45rem 0.85rem; border-radius: 8px; font-size: 0.82rem; font-weight: 700;
                                   display: block; text-align: center; box-shadow: 0 4px 12px rgba(4, 106, 56, 0.25);">
                            📖 Read Online Free →
                        </a>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <a href="{read_link}" target="_blank" style="background: #F5F5ED; color: #1A1A1A; border: 1px solid #E5E5DC;
                                   text-decoration: none; padding: 0.45rem 0.85rem; border-radius: 8px; font-size: 0.82rem; font-weight: 700;
                                   display: block; text-align: center;">
                            🌐 Open Library Entry →
                        </a>
                        """, unsafe_allow_html=True)
                with c_ai:
                    if st.button("💬 Consult AI Assistant", key=f"btn_chat_from_search_{idx}", use_container_width=True, type="primary"):
                        st.session_state["selected_book_for_chat"] = title
                        st.session_state["chat_messages"].append({
                            "role": "user",
                            "content": f"Can you provide a full breakdown and executive summary of the book '{title}' by {author}?"
                        })
                        st.session_state["active_reader_tab"] = 1
                        st.success(f"Loaded '{title}' into Reader AI Assistant!")
                        st.rerun()

    elif last_q:
        st.info(f"No direct matches found for '{last_q}'. You can query our streaming AI Assistant to generate full chapter breakdowns and summaries.")


# ==============================================================================
# FEATURE 2: READER AI BOOK ASSISTANT (CONVERSATIONAL CHATBOT WITH STREAMING)
# ==============================================================================
def _render_ai_assistant_tab():
    st.markdown("### 🤖 Reader AI Book Assistant (True Conversational Chatbot)")
    st.caption("Snappy, streaming AI companion for deep summaries, chapter breakdowns, and literary Q&A. Answers casual greetings and complex questions instantaneously.")

    col_focus, col_clear = st.columns([3.5, 1])
    with col_focus:
        active_book = st.session_state.get("selected_book_for_chat", "")
        target_book = st.text_input(
            "Current Book Focus (Optional):",
            value=active_book,
            placeholder="e.g. The Republic, War and Peace, Principles of Economics...",
            key="reader_ai_active_book_fld"
        )
        st.session_state["selected_book_for_chat"] = target_book

    with col_clear:
        st.write("")
        st.write("")
        if st.button("🧹 Clear Chat", key="btn_clear_chat", use_container_width=True):
            st.session_state["chat_messages"] = [
                {"role": "assistant", "content": "👋 Chat reset. Ask me anything about any book or literary topic!"}
            ]
            st.rerun()

    # Instant Deep Analysis Action Buttons
    st.markdown("##### ⚡ Instant Book Breakdown Queries")
    p1, p2, p3, p4, p5 = st.columns(5)

    with p1:
        req_sum = st.button("📋 Executive Summary", key="btn_p1_sum", use_container_width=True)
    with p2:
        req_takeaways = st.button("🔑 Top 5 Takeaways", key="btn_p2_take", use_container_width=True)
    with p3:
        req_chapters = st.button("📖 Chapter Breakdown", key="btn_p3_chap", use_container_width=True)
    with p4:
        req_author = st.button("👤 Author Background", key="btn_p4_auth", use_container_width=True)
    with p5:
        req_themes = st.button("🎭 Themes & Symbolism", key="btn_p5_themes", use_container_width=True)

    triggered_action = None
    if req_sum:
        triggered_action = f"Provide a complete executive summary of '{target_book or 'the book'}'."
    elif req_takeaways:
        triggered_action = f"List the top 5 key takeaways and philosophical lessons from '{target_book or 'the book'}'."
    elif req_chapters:
        triggered_action = f"Provide a chapter-by-chapter breakdown of '{target_book or 'the book'}'."
    elif req_author:
        triggered_action = f"Give the author background and historical context for '{target_book or 'the book'}'."
    elif req_themes:
        triggered_action = f"Analyze the core themes, symbolism, and metaphors of '{target_book or 'the book'}'."

    # If quick action button clicked, add to chat and trigger response
    if triggered_action:
        st.session_state["chat_messages"].append({"role": "user", "content": triggered_action})
        st.rerun()

    st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # Render Chat History using native st.chat_message
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"], avatar="📖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # If the last message is from user, generate streaming assistant response
    if st.session_state["chat_messages"] and st.session_state["chat_messages"][-1]["role"] == "user":
        last_user_prompt = st.session_state["chat_messages"][-1]["content"]
        with st.chat_message("assistant", avatar="📖"):
            stream_gen = stream_book_chatbot(
                target_book.strip(),
                last_user_prompt,
                conversation_history=st.session_state["chat_messages"][:-1]
            )
            full_response = st.write_stream(stream_gen)
            st.session_state["chat_messages"].append({"role": "assistant", "content": full_response})

    # Chat input box
    if user_prompt := st.chat_input("Ask any question about this book, or say hello..."):
        st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
        st.rerun()


# ==============================================================================
# FEATURE 3: VISUAL BOOK COVER SCANNER & IMAGE-TO-PDF FINDER (FAST 2-3 SECONDS)
# ==============================================================================
def _render_cover_scanner_tab():
    st.markdown("### 📷 Visual Book Cover Scanner & Image-to-PDF Finder")
    st.caption("Point your camera directly at any book cover or upload an image. Images are automatically optimized and compressed to ensure instant 2-3 second recognition via Gemini Vision.")

    input_mode = st.radio(
        "Select Image Input Method:",
        ["📸 Live Camera Scanner (Library / Bookstore Mode)", "📁 Image File Uploader"],
        horizontal=True,
        key="reader_scanner_mode_selector"
    )

    image_source = None
    if "Live Camera" in input_mode:
        image_source = st.camera_input("Take a photo of the book cover in front of you:")
    else:
        image_source = st.file_uploader(
            "Upload Book Cover Photo / Screenshot:",
            type=["jpg", "jpeg", "png", "webp"],
            key="reader_cover_file_uploader"
        )

    if image_source is not None:
        c_prev, c_detect = st.columns([1, 1.8], gap="large")

        with c_prev:
            st.image(image_source, caption="Captured Book Cover Image", use_container_width=True)

        with c_detect:
            # Process with Gemini Vision
            cache_key = getattr(image_source, "name", "camera_live") + str(getattr(image_source, "size", 0))
            if st.session_state.get("reader_scanner_cached_file") != cache_key:
                with st.spinner("🤖 Gemini Vision AI reading cover (compressed for ~2s speed)..."):
                    success, detected_label, matches = scan_and_resolve_book(image_source)
                    st.session_state["reader_scanner_cached_file"] = cache_key
                    st.session_state["reader_scanner_success"] = success
                    st.session_state["reader_scanner_label"] = detected_label
                    st.session_state["reader_scanner_matches"] = matches

            success = st.session_state.get("reader_scanner_success", False)
            detected_label = st.session_state.get("reader_scanner_label", "")
            matches = st.session_state.get("reader_scanner_matches", [])

            if success:
                st.markdown(f"""
                <div style="background: rgba(4, 106, 56, 0.08); border: 1.5px solid rgba(4, 106, 56, 0.28);
                            border-radius: 16px; padding: 1.35rem; margin-bottom: 1.25rem;">
                    <div style="font-size: 0.78rem; color: #046A38; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase;">
                        ✓ VISION OCR IDENTIFICATION COMPLETE
                    </div>
                    <div style="font-size: 1.4rem; font-weight: 900; color: #1A1A1A; margin-top: 0.35rem;">
                        {detected_label}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if matches:
                    st.markdown(f"##### 🎯 Matched Digital Publications ({len(matches)} Found):")
                    for m_idx, m_book in enumerate(matches[:3]):
                        m_title = m_book.get("title", "Untitled")
                        m_author = m_book.get("author", "Unknown Author")
                        m_link = m_book.get("read_link")
                        m_is_free = m_book.get("is_totally_free", False)

                        c1, c2 = st.columns([3, 1.2])
                        with c1:
                            st.markdown(f"**{m_title}** by *{m_author}*")
                            st.caption(f"Source: {m_book.get('source')}")
                        with c2:
                            if m_link:
                                st.markdown(f"""
                                <a href="{m_link}" target="_blank" style="background: #046A38; color: #FFFFFF;
                                           text-decoration: none; padding: 0.35rem 0.75rem; border-radius: 6px; font-size: 0.78rem; font-weight: 700;
                                           display: inline-block; text-align: center;">
                                    {'📖 Read Free PDF' if m_is_free else '🌐 View Edition'}
                                </a>
                                """, unsafe_allow_html=True)

                st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1rem 0;'>", unsafe_allow_html=True)
                if st.button(f"💬 Consult AI Assistant About '{detected_label}'", key="btn_chat_from_scan", type="primary", use_container_width=True):
                    st.session_state["selected_book_for_chat"] = detected_label
                    st.session_state["chat_messages"].append({
                        "role": "user",
                        "content": f"I just scanned the book '{detected_label}'. Can you give me an executive overview and its top themes?"
                    })
                    st.session_state["active_reader_tab"] = 1
                    st.success(f"Loaded '{detected_label}' into AI Assistant!")
                    st.rerun()
            else:
                st.error(f"Could not reliably detect book cover: {detected_label}")
