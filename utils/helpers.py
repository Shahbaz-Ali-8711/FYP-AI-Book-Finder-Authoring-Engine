import time
import random
from google import genai

# Fast direct models for instant response (prioritizing 2.5-flash and 2.0-flash)
FAST_MODELS = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']


def call_gemini_with_fallback(api_key, contents):
    """
    Fast direct Gemini call with zero heavy blocking backoff sleeps.
    Returns in 1-2 seconds.
    """
    if not api_key:
        return False, "⚠️ Gemini API Key missing! Check .env file."

    client = genai.Client(api_key=api_key)

    for model_name in FAST_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            if response and response.text:
                return True, response.text.strip()
        except Exception:
            # Immediately try next fast model without sleeping
            continue

    return False, "⚠️ The AI service is momentarily busy. Please retry in a moment."


def stream_gemini_response(api_key, contents):
    """
    Fast streaming generator that yields text chunks immediately for st.write_stream.
    Renders word-by-word instantly like ChatGPT with zero waiting time.
    """
    if not api_key:
        yield "⚠️ Gemini API key missing. Please verify your GEMINI_API_KEY in .env."
        return

    client = genai.Client(api_key=api_key)

    for model_name in FAST_MODELS:
        try:
            stream = client.models.generate_content_stream(
                model=model_name,
                contents=contents
            )
            yielded = False
            for chunk in stream:
                if chunk.text:
                    yielded = True
                    yield chunk.text
            if yielded:
                return
        except Exception:
            continue

    yield "⚠️ The AI service is temporarily unavailable. Please retry in a moment."


def init_session_state():
    """
    Safely initialize all required Streamlit session state keys.
    Prevents StreamlitWidgetAlreadyInstantiatedError and key collisions.
    """
    import streamlit as st

    defaults = {
        "logged_in": False,
        "user_id": 1,
        "username": "Author",
        "user_role": "user",
        "is_admin": False,
        "admin_bypass": False,
        "show_login": False,
        "nav_page": "landing",
        "nav_section": "home",
        "selected_book_for_chat": "",
        "chat_messages": [
            {"role": "assistant", "content": "👋 Hello! I am your Pen2Publish AI Literary Scholar. Ask me anything about any book, chapter summaries, character arcs, or literary history!"}
        ],
        "writer_plot_twists": None,
        "writer_dialogue_result": None,
        "writer_world_result": None,
        "writer_toc_result": None,
        "writer_blurb_result": None,
        "reader_vibe_results": [],
        "reader_match_results": [],
        "reader_cover_results": [],
        "summary_result": "",
        "active_character_id": None,
        "active_world_id": None,
        "active_reader_tab": 0,
        "active_creator_tab": 0,
        "active_platform_tab": 0,
        "user_subscription_tier": "Free",
        "daily_credits_used": 0,
        "daily_credits_max": 15,
        "creator_quick_book_result": None,
        "reading_quote_card": None,
        "reader_active_search_results": [],
        "reader_last_search_query": "",
        "reader_ai_active_analysis": None,
        "reader_ai_analysis_title": "",
        "reader_scanner_cached_file": "",
        "reader_scanner_success": False,
        "reader_scanner_label": "",
        "reader_scanner_matches": [],
        # Mode 1 CapCut-style State
        "mode1_canvas_mode": "template",  # 'blank' or 'template'
        "mode1_selected_template": "modern",
        "mode1_editor_text": "",
        "mode1_font_family": "Modern Sans-Serif",
        "mode1_font_size": 16,
        "mode1_alignment": "Left",
        # Mode 2 Full Book Generator State
        "m2_selected_palette": "Warm Ivory & Emerald",
        "m2_selected_template": "Luxury Editorial",
        "mode2_raw_manuscript": "",
        "mode2_compiled_pdf": None,
        "mode2_compiled_title": "",
        "m2_blurb_content": "",
        "book_title_state": "The Architecture of Tomorrow",
        "book_genre_state": "Non-Fiction",
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
