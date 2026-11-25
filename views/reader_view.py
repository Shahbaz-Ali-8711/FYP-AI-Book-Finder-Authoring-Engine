import streamlit as st
import re
from utils.helpers import (
    init_session_state, get_gemini_api_key, scroll_to_top
)
from utils.styles import render_html
from database.db_handler import (
    get_saved_library_items, save_library_item, delete_saved_library_item
)
from modules.search_engine import search_free_books
from modules.chatbot_engine import (
    get_book_deep_insights, stream_book_chatbot,
    explain_or_translate_passage, generate_citations,
    synthesize_speech_audio, extract_document_content,
    stream_document_rag_chat
)
from modules.scanner_engine import scan_and_resolve_book


def render_reader_view():
    init_session_state()

    # Warm Ivory & Luxury Emerald Header Banner
    render_html("""
    <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                border-radius: 20px; padding: 2rem 2.25rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 10px 30px -10px rgba(26, 26, 26, 0.05);">
        <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.6rem; flex-wrap: wrap;">
            <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28);
                        font-size: 0.76rem; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase;
                        padding: 0.22rem 0.7rem; border-radius: 9999px;">
                HYBRID MULTI-MODEL AI ROUTER
            </span>
            <span style="background: rgba(227, 66, 52, 0.08); color: #E34234; border: 1px solid rgba(227, 66, 52, 0.28);
                        font-size: 0.76rem; font-weight: 800; padding: 0.22rem 0.7rem; border-radius: 9999px;">
                ⚡ Groq LPU (Sub-Second Chat & Citations)
            </span>
            <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28);
                        font-size: 0.76rem; font-weight: 800; padding: 0.22rem 0.7rem; border-radius: 9999px;">
                👁️ Gemini 3.5 Flash-Lite (Vision OCR & 1M Doc RAG)
            </span>
        </div>
        <div style="font-size: 2.1rem; font-weight: 900; color: #1A1A1A; letter-spacing: -0.02em;">
            📖 AI Book Discovery & Research Suite
        </div>
        <div style="font-size: 0.95rem; color: #4A4A4A; margin-top: 0.35rem; max-width: 820px; line-height: 1.6;">
            Search 60,000+ public domain works, chat with uploaded research PDFs using grounded citations, consult our bilingual assistant (English ↔ Urdu), or analyze physical covers with multimodal vision OCR.
        </div>
    </div>
    """)

    _render_bookshelf_drawer()

    tabs = st.tabs([
        "🔍 Smart Book Search Engine",
        "🤖 Reader AI Book Assistant & Doc RAG",
        "📷 Visual Book Cover Scanner"
    ])

    with tabs[0]:
        _render_search_engine_tab()

    with tabs[1]:
        _render_ai_assistant_tab()

    with tabs[2]:
        _render_cover_scanner_tab()


# ==============================================================================
# PERSONAL BOOKSHELF DRAWER
# ==============================================================================
def _render_bookshelf_drawer():
    with st.expander("📚 My Personal Bookshelf & Saved Vault", expanded=False):
        items = get_saved_library_items(user_id=1)
        if not items:
            st.caption("No bookmarked books or citations yet. Click '🔖 Bookmark' or '📑 Cite This Book' on any book result to save it to your vault.")
        else:
            st.markdown(f"##### 🗄️ Saved Research Items ({len(items)})")
            for it in items:
                c1, c2 = st.columns([4.2, 1])
                with c1:
                    i_type = it.get("item_type", "book")
                    icon = "📖" if i_type == "book" else ("📑" if i_type == "citation" else "📝")
                    st.markdown(f"**{icon} {it.get('title')}** — *{it.get('subtitle_or_author', '')}*")
                    if it.get("content_or_notes"):
                        st.caption(f"{it.get('content_or_notes')[:200]}")
                with c2:
                    if st.button("🗑️ Remove", key=f"del_shelf_item_{it.get('id')}", use_container_width=True):
                        delete_saved_library_item(it.get("id"), user_id=1)
                        st.rerun()
                st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 0.4rem 0;'>", unsafe_allow_html=True)


# ==============================================================================
# AUDIO NARRATION HELPER (GTTS + BROWSER WEB SPEECH FALLBACK)
# ==============================================================================
def _render_audio_player(text, label="🔊 Listen to Summary / Audio Brief"):
    col_a, col_b = st.columns([1.5, 2])
    with col_a:
        play_audio = st.button(label, key=f"btn_audio_{abs(hash(text[:50]))}", use_container_width=True)

    if play_audio:
        with st.spinner("Synthesizing audio narration..."):
            audio_bytes, err = synthesize_speech_audio(text[:800])
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
            else:
                safe_text = re.sub(r'[\r\n\'"]+', ' ', text[:400])
                st.markdown(f"""
                <div style="margin-top: 0.5rem;">
                    <button onclick="window.speechSynthesis.cancel(); var u = new SpeechSynthesisUtterance('{safe_text}'); window.speechSynthesis.speak(u);"
                            style="background: #046A38; color: #FFFFFF; border: none; padding: 0.45rem 1rem;
                                   border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 0.85rem;">
                        🔊 Play via Browser Audio
                    </button>
                    <span style="font-size: 0.78rem; color: #737373; margin-left: 0.5rem;">(Native Web Speech API Fallback)</span>
                </div>
                """, unsafe_allow_html=True)


# ==============================================================================
# CITATION EXPANDER (APA 7th, MLA 9th, IEEE)
# ==============================================================================
def _render_citation_expander(title, author, card_idx):
    with st.expander(f"📑 Cite This Book: {title[:30]}...", expanded=False):
        cites = generate_citations(title, author)
        render_html("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 0.8rem; font-weight: 700; color: #1A1A1A;">Academic Formats</span>
            <span style="background: rgba(227, 66, 52, 0.08); color: #E34234; border: 1px solid rgba(227, 66, 52, 0.28); font-size: 0.68rem; font-weight: 800; padding: 0.15rem 0.55rem; border-radius: 9999px;">
                ⚡ Groq LPU (openai/gpt-oss-20b)
            </span>
        </div>
        """)
        t_apa, t_mla, t_ieee = st.tabs(["APA 7th", "MLA 9th", "IEEE"])
        with t_apa:
            st.code(cites["apa"], language="text")
        with t_mla:
            st.code(cites["mla"], language="text")
        with t_ieee:
            st.code(cites["ieee"], language="text")

        st.markdown(f"""
        <div style="background: #F5F5ED; border-left: 3.5px solid #046A38; padding: 0.65rem 0.95rem; border-radius: 6px; font-style: italic; font-size: 0.85rem; margin-top: 0.5rem;">
            {cites["quote_card"]}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔖 Bookmark Citation to Bookshelf", key=f"btn_cite_card_shelf_{card_idx}", use_container_width=True):
            save_library_item(title=title, item_type="citation", subtitle_or_author=author, content_or_notes=cites["apa"])
            st.success(f"Saved citation for '{title}' to Bookshelf!")


# ==============================================================================
# SPLIT-SCREEN "SMART READER" VIEW
# ==============================================================================
def _render_split_screen_reader(book):
    title = book.get("title", "Selected Book")
    author = book.get("author", "Unknown Author")
    desc = book.get("description", "A classic work of literature exploring ideas and narrative.")
    read_link = book.get("read_link") or f"https://www.gutenberg.org/ebooks/search/?query={title.replace(' ', '+')}"

    st.markdown(f"""
    <div style="background: #FAFAF5; border: 2px solid #046A38; border-radius: 16px; padding: 1.25rem; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="background: #046A38; color: #FFFFFF; font-size: 0.72rem; font-weight: 800; padding: 0.2rem 0.6rem; border-radius: 9999px;">
                    SPLIT-SCREEN SMART READER MODE
                </span>
                <span style="font-size: 1.3rem; font-weight: 900; color: #1A1A1A; margin-left: 0.5rem;">{title}</span>
                <span style="font-size: 0.9rem; color: #737373; margin-left: 0.4rem;">by {author}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_close, _ = st.columns([1.5, 4])
    with c_close:
        if st.button("✖️ Exit Split-Screen Reader", key=f"btn_close_smart_reader_{abs(hash(title))}", use_container_width=True):
            st.session_state["smart_reader_active_book"] = None
            st.rerun()

    col_left, col_right = st.columns([1.1, 1], gap="large")

    sample_excerpt = (
        f"{title}\n\n"
        f"Chapter 1: The Principle of Ideas\n\n"
        f"{desc}\n\n"
        "In the quiet hours before dawn, when the thoughts of the world are suspended, the author sets down the primary observations. "
        "Every discipline begins not with certainty, but with curious inquiry. To understand the momentum of human history requires "
        "one to examine the small, deliberate choices that precede great transformations. Knowledge preserved in the written word "
        "remains the singular bridge across generations, defying the decay of time and opening vistas of contemplation for those "
        "who follow after."
    )

    with col_left:
        st.markdown("#### 📖 Reading Pane")
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC; border-radius: 12px;
                    padding: 1.5rem; max-height: 480px; overflow-y: auto; font-size: 0.95rem; line-height: 1.8; color: #1A1A1A;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.03);">
            {sample_excerpt.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        _render_audio_player(sample_excerpt, label="🔊 Listen to Excerpt Aloud")

        st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1rem 0;'>", unsafe_allow_html=True)
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if st.button("🔖 Bookmark to Bookshelf", key=f"btn_shelf_add_{abs(hash(title))}", use_container_width=True):
                cites = generate_citations(title, author)
                save_library_item(title=title, item_type="book", subtitle_or_author=author, content_or_notes=cites["apa"])
                st.success("Added to Bookshelf!")
        with b_col2:
            st.markdown(f"""
            <a href="{read_link}" target="_blank" style="background: #046A38; color: #FFFFFF;
                       text-decoration: none; padding: 0.45rem 0.75rem; border-radius: 8px; font-size: 0.82rem; font-weight: 700;
                       display: block; text-align: center;">
                🌐 Open Direct Archive Source →
            </a>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown("#### 🤖 Contextual AI Assistant")
        st.caption("Paste or select any passage below to get instant subtext explanation or English ↔ Urdu translation.")

        target_passage = st.text_area(
            "Passage to Analyze or Translate:",
            value=sample_excerpt[:350],
            height=130,
            key=f"split_passage_{abs(hash(title))}"
        )

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            act_exp = st.button("💡 Explain Subtext", key=f"act_exp_{abs(hash(title))}", use_container_width=True)
        with b2:
            act_urdu = st.button("🇵🇰 To Urdu (اردو)", key=f"act_urdu_{abs(hash(title))}", use_container_width=True)
        with b3:
            act_eng = st.button("🇬🇧 To English", key=f"act_eng_{abs(hash(title))}", use_container_width=True)
        with b4:
            act_simp = st.button("✨ Simplify", key=f"act_simp_{abs(hash(title))}", use_container_width=True)

        mode_choice = None
        if act_exp:
            mode_choice = "explain"
        elif act_urdu:
            mode_choice = "urdu"
        elif act_eng:
            mode_choice = "english"
        elif act_simp:
            mode_choice = "simplify"

        if mode_choice and target_passage.strip():
            with st.spinner("AI Assistant analyzing passage..."):
                succ, resp = explain_or_translate_passage(target_passage.strip(), mode_choice)
                if succ:
                    st.session_state[f"last_split_ai_result_{abs(hash(title))}"] = (resp, mode_choice)
                else:
                    st.error(resp)

        last_ai_data = st.session_state.get(f"last_split_ai_result_{abs(hash(title))}")
        if last_ai_data:
            res_text, res_mode = last_ai_data
            is_urdu_out = (res_mode == "urdu" or bool(re.search(r'[\u0600-\u06FF]', res_text)))
            align_style = "direction: rtl; text-align: right; font-family: 'Jameel Noori Nastaleeq', 'Noto Nastaliq Urdu', serif;" if is_urdu_out else "text-align: left;"

            st.markdown(f"""
            <div style="background: rgba(4, 106, 56, 0.05); border: 1.5px solid rgba(4, 106, 56, 0.25);
                        border-radius: 12px; padding: 1.25rem; margin-top: 1rem; {align_style}">
                <div style="font-size: 0.76rem; color: #046A38; font-weight: 800; text-transform: uppercase; margin-bottom: 0.4rem;">
                    ✓ AI ANALYSIS ({res_mode.upper()})
                </div>
                <div style="font-size: 0.94rem; color: #1A1A1A; line-height: 1.7;">
                    {res_text.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            _render_audio_player(res_text, label="🔊 Listen to Analysis")


# ==============================================================================
# FEATURE 1: SMART BOOK SEARCH ENGINE
# ==============================================================================
def _render_search_engine_tab():
    st.markdown("### 🔍 Smart Book Search Engine")
    st.caption("Direct public domain access across Project Gutenberg & Internet Archive without Captcha gates, with 1-click preview and citation generator.")

    active_smart_book = st.session_state.get("smart_reader_active_book")
    if active_smart_book:
        _render_split_screen_reader(active_smart_book)
        st.markdown("<hr style='border: none; border-top: 2px solid #E5E5DC; margin: 2rem 0;'>", unsafe_allow_html=True)

    col_q, col_btn = st.columns([4, 1])
    with col_q:
        search_query = st.text_input(
            "Search 60,000+ Titles by Title, Author, or Keywords:",
            placeholder="e.g., The Odyssey, Pride and Prejudice, Principles of Economics, Autonomous Systems...",
            key="reader_search_query_input"
        )
    with col_btn:
        st.write("")
        st.write("")
        run_search = st.button("Search Archive", key="btn_run_reader_search", type="primary", use_container_width=True)

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
        with st.spinner("Searching Gutenberg & Internet Archive..."):
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

                cover_html = f'<img src="{cover}" style="width: 100px; height: 145px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">' if cover else '<div style="width: 100px; height: 145px; background: #F5F5ED; border: 1.5px dashed #D4D4CA; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 2rem;">📖</div>'

                render_html(f"""
                <div style="background: #FFFFFF; border: 1.5px solid #E5E5DC;
                            border-radius: 16px; padding: 1.35rem; margin-bottom: 0.75rem;
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
                                {desc[:140]}...
                            </div>
                            <div style="font-size: 0.76rem; color: #737373;">
                                🏛️ Source: <strong>{source}</strong>
                            </div>
                        </div>
                    </div>
                </div>
                """)

                c_read, c_smart, c_ai = st.columns(3)
                with c_read:
                    st.markdown(f"""
                    <a href="{read_link}" target="_blank" style="background: #046A38; color: #FFFFFF;
                               text-decoration: none; padding: 0.45rem 0.5rem; border-radius: 8px; font-size: 0.78rem; font-weight: 700;
                               display: block; text-align: center; box-shadow: 0 4px 12px rgba(4, 106, 56, 0.25);">
                        📖 Direct Read →
                    </a>
                    """, unsafe_allow_html=True)

                with c_smart:
                    if st.button("👓 Smart Reader", key=f"btn_split_read_{idx}", use_container_width=True):
                        st.session_state["smart_reader_active_book"] = book
                        st.rerun()

                with c_ai:
                    if st.button("💬 Send to AI", key=f"btn_chat_from_search_{idx}", use_container_width=True, type="primary"):
                        st.session_state["selected_book_for_chat"] = title
                        st.session_state["chat_messages"].append({
                            "role": "user",
                            "content": f"Can you provide a full breakdown and executive summary of the book '{title}' by {author}?"
                        })
                        st.session_state["active_reader_tab"] = 1
                        st.success(f"Loaded '{title}' into Reader AI Assistant!")
                        scroll_to_top()
                        st.rerun()

                # One-Click Academic Citation Generator (APA 7th, MLA 9th, IEEE)
                _render_citation_expander(title, author, idx)

    elif last_q:
        st.info(f"No direct matches found for '{last_q}'. You can query our streaming AI Assistant to generate full chapter breakdowns and summaries.")


# ==============================================================================
# FEATURE 2: READER AI BOOK ASSISTANT & RAG DOCUMENT Q&A
# ==============================================================================
def _render_ai_assistant_tab():
    st.markdown("### 🤖 Reader AI Assistant & Grounded Document Q&A")
    render_html("""
    <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.85rem; flex-wrap: wrap;">
        <span style="background: rgba(227, 66, 52, 0.08); color: #E34234; border: 1px solid rgba(227, 66, 52, 0.28); font-size: 0.72rem; font-weight: 800; padding: 0.18rem 0.6rem; border-radius: 9999px;">
            ⚡ Conversational Chat: Groq LPU (openai/gpt-oss-120b)
        </span>
        <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28); font-size: 0.72rem; font-weight: 800; padding: 0.18rem 0.6rem; border-radius: 9999px;">
            📖 1M Doc RAG & Urdu: Gemini 3.5 Flash-Lite
        </span>
    </div>
    """)
    st.caption("Chat with uploaded research papers with grounded page citations, or explore any published book in English or Urdu.")

    assistant_mode = st.radio(
        "Select Assistant Functionality:",
        ["📄 RAG: Chat with Your Document (PDF / DOCX / TXT)", "📖 Conversational Book Scholar (English / Urdu)"],
        horizontal=True,
        key="reader_assistant_mode_choice"
    )

    # --------------------------------------------------------------------------
    # SUB-MODE 1: RAG CHAT WITH UPLOADED DOCUMENT
    # --------------------------------------------------------------------------
    if "RAG" in assistant_mode:
        st.markdown("##### 📄 Grounded Document Q&A (Anti-Hallucination with Page Citations)")
        st.caption("Upload research papers, book chapters, or reports. Answers cite exact [Page X] or [Section Y] sources.")

        doc_file = st.file_uploader(
            "Upload Research Document (.pdf, .docx, .txt):",
            type=["pdf", "docx", "txt", "md"],
            key="rag_doc_uploader"
        )

        if doc_file is not None:
            doc_key = doc_file.name + str(doc_file.size)
            if st.session_state.get("rag_cached_doc_id") != doc_key:
                with st.spinner(f"Extracting and indexing {doc_file.name}..."):
                    ok, text_content, chunks = extract_document_content(doc_file)
                    if ok:
                        st.session_state["rag_document_text"] = text_content
                        st.session_state["rag_document_name"] = doc_file.name
                        st.session_state["rag_document_chunks"] = chunks
                        st.session_state["rag_cached_doc_id"] = doc_key
                        st.success(f"Indexed {len(chunks)} pages/sections from {doc_file.name}!")
                    else:
                        st.error(text_content)

        indexed_doc = st.session_state.get("rag_document_text", "")
        indexed_name = st.session_state.get("rag_document_name", "")

        if indexed_doc:
            st.markdown(f"""
            <div style="background: rgba(4, 106, 56, 0.05); border: 1.5px solid rgba(4, 106, 56, 0.25); border-radius: 12px; padding: 0.85rem 1.25rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>📄 Active Document:</strong> {indexed_name} <span style="color: #737373;">({len(indexed_doc.split()):,} words indexed)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            rag_col1, rag_col2 = st.columns([3.5, 1.2])
            with rag_col1:
                rag_query = st.text_input(
                    "Ask a question grounded in this document:",
                    placeholder="e.g., What are the core methodology findings? What limitations are noted on page 4?",
                    key="rag_user_query_input"
                )
            with rag_col2:
                st.write("")
                st.write("")
                btn_ask_rag = st.button("Ask Document →", key="btn_ask_rag_submit", type="primary", use_container_width=True)

            if btn_ask_rag and rag_query.strip():
                st.markdown(f"**Question:** {rag_query}")
                with st.chat_message("assistant", avatar="📄"):
                    stream_ans = stream_document_rag_chat(indexed_name, indexed_doc, rag_query)
                    ans_text = st.write_stream(stream_ans)

                st.session_state["last_rag_notes"] = f"Document: {indexed_name}\nQuestion: {rag_query}\nAnswer: {ans_text}"

            # Cross-Module Integration: Send Notes to Writer Studio
            if st.session_state.get("last_rag_notes"):
                st.write("")
                if st.button("📤 Send Research Notes to Writer Studio", key="btn_send_rag_notes_to_writer", type="secondary"):
                    existing_text = st.session_state.get("mode1_editor_text", "")
                    note_block = f"\n\n--- RESEARCH NOTES ({indexed_name}) ---\n" + st.session_state["last_rag_notes"]
                    st.session_state["mode1_editor_text"] = existing_text + note_block
                    st.session_state["research_notes_for_writer"] = st.session_state["last_rag_notes"]
                    st.session_state["nav_page"] = "creator"
                    st.success("Notes loaded into Writer Studio! Redirecting...")
                    scroll_to_top()
                    st.rerun()

        else:
            st.info("Upload a .pdf, .docx, or .txt file above to begin grounded document Q&A.")

    # --------------------------------------------------------------------------
    # SUB-MODE 2: CONVERSATIONAL BOOK SCHOLAR (BILINGUAL)
    # --------------------------------------------------------------------------
    else:
        col_focus, col_lang, col_clear = st.columns([2.5, 1.8, 1])
        with col_focus:
            active_book = st.session_state.get("selected_book_for_chat", "")
            target_book = st.text_input(
                "Current Book Focus (Optional):",
                value=active_book,
                placeholder="e.g. The Republic, War and Peace, Principles of Autonomous Systems...",
                key="reader_ai_active_book_fld"
            )
            st.session_state["selected_book_for_chat"] = target_book

        with col_lang:
            selected_lang_label = st.radio(
                "Language / زبان:",
                ["English (Default)", "اردو (Urdu)"],
                horizontal=True,
                key="reader_ai_chat_lang_toggle"
            )
            active_language = "Urdu" if "Urdu" in selected_lang_label else "English"

        with col_clear:
            st.write("")
            st.write("")
            if st.button("🧹 Clear Chat", key="btn_clear_chat", use_container_width=True):
                st.session_state["chat_messages"] = [
                    {"role": "assistant", "content": "👋 Chat reset. Ask me anything about any book in English or Urdu!"}
                ]
                st.rerun()

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

        if triggered_action:
            st.session_state["chat_messages"].append({"role": "user", "content": triggered_action})
            st.rerun()

        st.markdown("<hr style='border: none; border-top: 1.5px solid #E5E5DC; margin: 1.25rem 0;'>", unsafe_allow_html=True)

        for msg in st.session_state["chat_messages"]:
            with st.chat_message(msg["role"], avatar="📖" if msg["role"] == "assistant" else "👤"):
                is_urdu_msg = bool(re.search(r'[\u0600-\u06FF]', msg["content"]))
                if is_urdu_msg:
                    st.markdown(f"""
                    <div style="direction: rtl; text-align: right; font-family: 'Jameel Noori Nastaleeq', 'Noto Nastaliq Urdu', serif; font-size: 1.05rem; line-height: 1.8;">
                        {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(msg["content"])

        if st.session_state["chat_messages"] and st.session_state["chat_messages"][-1]["role"] == "user":
            last_user_prompt = st.session_state["chat_messages"][-1]["content"]
            with st.chat_message("assistant", avatar="📖"):
                stream_gen = stream_book_chatbot(
                    target_book.strip(),
                    last_user_prompt,
                    conversation_history=st.session_state["chat_messages"][:-1],
                    language=active_language
                )
                full_response = st.write_stream(stream_gen)
                st.session_state["chat_messages"].append({"role": "assistant", "content": full_response})

                if full_response and len(full_response.strip()) > 20:
                    _render_audio_player(full_response, label="🔊 Listen to AI Response")

        input_placeholder = "اس کتاب کے بارے میں کوئی بھی سوال پوچھیں..." if active_language == "Urdu" else "Ask any question about this book, or request a chapter summary..."
        if user_prompt := st.chat_input(input_placeholder):
            st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
            st.rerun()


# ==============================================================================
# FEATURE 3: VISUAL BOOK COVER SCANNER & MULTIMODAL VISION OCR
# ==============================================================================
def _render_cover_scanner_tab():
    st.markdown("### 📷 Visual Book Cover Scanner (Multimodal Vision OCR)")
    render_html("""
    <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.85rem;">
        <span style="background: rgba(4, 106, 56, 0.08); color: #046A38; border: 1px solid rgba(4, 106, 56, 0.28); font-size: 0.72rem; font-weight: 800; padding: 0.18rem 0.6rem; border-radius: 9999px;">
            👁️ Multimodal Vision OCR: Gemini 3.5 Flash-Lite
        </span>
    </div>
    """)
    st.caption("Analyzes book cover photos to extract Title, Author, Genre, Themes, Synopsis, and Recommendations in under 2 seconds.")

    input_mode = st.radio(
        "Select Cover Image Input Method:",
        ["📁 Upload Book Cover Photo (Primary / Fast)", "📸 Live Camera Scanner (Webcam)"],
        horizontal=True,
        key="reader_scanner_mode_selector"
    )

    image_source = None
    if "Live Camera" in input_mode:
        st.info("ℹ️ Please grant your browser camera permissions when prompted.")
        image_source = st.camera_input("Take a photo of the book cover in front of you:")
    else:
        image_source = st.file_uploader(
            "Upload Book Cover Photo / Screenshot (JPG, PNG, WEBP):",
            type=["jpg", "jpeg", "png", "webp"],
            key="reader_cover_file_uploader"
        )

    if image_source is not None:
        c_prev, c_detect = st.columns([1, 1.8], gap="large")

        with c_prev:
            st.image(image_source, caption="Captured Book Cover Image", use_container_width=True)

        with c_detect:
            cache_key = getattr(image_source, "name", "camera_live") + str(getattr(image_source, "size", 0))
            if st.session_state.get("reader_scanner_cached_file") != cache_key:
                with st.spinner("🤖 Gemini 3.5 Flash-Lite multimodal vision reading cover..."):
                    success, detected_label, matches, details = scan_and_resolve_book(image_source)
                    st.session_state["reader_scanner_cached_file"] = cache_key
                    st.session_state["reader_scanner_success"] = success
                    st.session_state["reader_scanner_label"] = detected_label
                    st.session_state["reader_scanner_matches"] = matches
                    st.session_state["reader_scanner_details"] = details

            success = st.session_state.get("reader_scanner_success", False)
            detected_label = st.session_state.get("reader_scanner_label", "")
            matches = st.session_state.get("reader_scanner_matches", [])
            details = st.session_state.get("reader_scanner_details") or {}

            if success:
                st.markdown(f"""
                <div style="background: rgba(4, 106, 56, 0.08); border: 1.5px solid rgba(4, 106, 56, 0.28);
                            border-radius: 16px; padding: 1.35rem; margin-bottom: 1.25rem;">
                    <div style="font-size: 0.76rem; color: #046A38; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase;">
                        ✓ VISION OCR IDENTIFICATION COMPLETE · GEMINI 3.5 FLASH-LITE
                    </div>
                    <div style="font-size: 1.45rem; font-weight: 900; color: #1A1A1A; margin-top: 0.35rem;">
                        {details.get('title', detected_label)}
                    </div>
                    <div style="font-size: 0.92rem; color: #046A38; font-weight: 700; margin-top: 0.2rem;">
                        by {details.get('author', 'Unknown Author')} · <span style="color: #737373;">{details.get('genre', 'General Literature')}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #333333; line-height: 1.6; margin-top: 0.65rem;">
                        <strong>Synopsis:</strong> {details.get('synopsis', '')}
                    </div>
                    <div style="font-size: 0.84rem; color: #4A4A4A; margin-top: 0.45rem;">
                        <strong>Key Themes:</strong> {details.get('themes', '')}
                    </div>
                    <div style="font-size: 0.84rem; color: #737373; margin-top: 0.35rem;">
                        <strong>Recommended Next Reads:</strong> {details.get('recommendations', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Copyable Academic Citations for Scanned Book
                _render_citation_expander(details.get('title', detected_label), details.get('author', 'Unknown Author'), 999)

                if matches:
                    st.markdown(f"##### 🎯 Matched Digital Copies & Archives ({len(matches)} Found):")
                    for m_idx, m_book in enumerate(matches[:3]):
                        m_title = m_book.get("title", "Untitled")
                        m_author = m_book.get("author", "Unknown Author")
                        m_link = m_book.get("read_link")
                        m_is_free = m_book.get("is_totally_free", False)

                        c1, c2, c3 = st.columns([2.5, 1.2, 1.2])
                        with c1:
                            st.markdown(f"**{m_title}** by *{m_author}*")
                            st.caption(f"Source: {m_book.get('source')}")
                        with c2:
                            if m_link:
                                st.markdown(f"""
                                <a href="{m_link}" target="_blank" style="background: #046A38; color: #FFFFFF;
                                           text-decoration: none; padding: 0.35rem 0.65rem; border-radius: 6px; font-size: 0.76rem; font-weight: 700;
                                           display: inline-block; text-align: center;">
                                    {'📖 Direct Read' if m_is_free else '🌐 View Edition'}
                                </a>
                                """, unsafe_allow_html=True)
                        with c3:
                            if st.button("👓 Smart Reader", key=f"btn_scan_split_{m_idx}", use_container_width=True):
                                st.session_state["smart_reader_active_book"] = m_book
                                st.session_state["active_reader_tab"] = 0
                                st.rerun()

                st.markdown("<hr style='border: none; border-top: 1px dashed #E5E5DC; margin: 1rem 0;'>", unsafe_allow_html=True)
                if st.button(f"💬 Consult AI Assistant About '{detected_label}'", key="btn_chat_from_scan", type="primary", use_container_width=True):
                    st.session_state["selected_book_for_chat"] = detected_label
                    st.session_state["chat_messages"].append({
                        "role": "user",
                        "content": f"I just scanned the book '{detected_label}'. Can you give me an executive overview and its top themes?"
                    })
                    st.session_state["active_reader_tab"] = 1
                    st.success(f"Loaded '{detected_label}' into AI Assistant!")
                    scroll_to_top()
                    st.rerun()
            else:
                st.error(f"Could not reliably detect book cover: {detected_label}")
