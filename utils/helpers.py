import os
import time
import re
from google import genai
from utils.ai_router import (
    get_groq_api_key, get_gemini_api_key, get_groq_client, get_gemini_client,
    is_groq_available, is_gemini_available,
    route_ai_completion, route_ai_stream, route_ai_vision,
    render_ai_badge, get_last_ai_badge, set_last_ai_badge,
    GROQ_TEXT_MODEL, GROQ_LIGHT_MODEL, GEMINI_FAST_MODEL, GEMINI_PRO_MODEL
)

# Primary fast model standardized to gemini-3.5-flash-lite with fallback to gemini-3.8-flash
PRIMARY_MODEL = GEMINI_FAST_MODEL
FAST_MODELS = [GEMINI_FAST_MODEL, GEMINI_PRO_MODEL, 'gemini-2.0-flash']


def get_gemini_api_key():
    """
    Centralized loader: checks st.secrets first (Streamlit Cloud),
    then falls back to os.getenv (local .env).
    """
    key = ""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    if not key:
        key = os.getenv("GEMINI_API_KEY", "")

    return (key or "").strip().strip('"').strip("'")


def get_gemini_client():
    """
    Returns an authenticated google-genai Client or None if key is absent.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def call_gemini_with_fallback(api_key, contents):
    """
    Fast direct Gemini call with official google-genai SDK.
    Iterates across gemini-3.5-flash-lite -> gemini-3.8-flash.
    Safely catches 429 quota, timeouts, and network drops without raw UI tracebacks.
    """
    effective_key = api_key or get_gemini_api_key()
    if not effective_key:
        return False, "⚠️ Gemini API Key missing! Please set GEMINI_API_KEY in your .env or Streamlit Secrets."

    try:
        client = genai.Client(api_key=effective_key)
    except Exception as e:
        return False, f"⚠️ Unable to initialize Gemini Client: {str(e)}"

    last_error = ""
    for model_name in FAST_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            if response and response.text:
                return True, response.text.strip()
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                last_error = "Rate limit reached. Trying backup model..."
            elif "timeout" in err_str or "timed out" in err_str:
                last_error = "Network timeout. Trying backup model..."
            else:
                last_error = str(e)
            continue

    if "rate limit" in last_error.lower() or "quota" in last_error.lower():
        return False, "⚠️ AI quota temporarily exceeded. Please wait a few seconds and retry."
    elif "timeout" in last_error.lower():
        return False, "⚠️ Network connection timed out. Please check your internet connection."
    else:
        return False, "⚠️ The AI service is momentarily busy. Please retry in a few seconds."


def stream_gemini_response(api_key, contents):
    """
    Fast streaming generator for st.write_stream using gemini-3.5-flash-lite.
    Renders responses word-by-word with zero turn latency.
    """
    effective_key = api_key or get_gemini_api_key()
    if not effective_key:
        yield "⚠️ Gemini API key missing. Please verify your GEMINI_API_KEY in .env or Streamlit Secrets."
        return

    try:
        client = genai.Client(api_key=effective_key)
    except Exception as e:
        yield f"⚠️ Client initialization error: {str(e)}"
        return

    for model_name in FAST_MODELS:
        try:
            stream = client.models.generate_content_stream(
                model=model_name,
                contents=contents
            )
            yielded = False
            for chunk in stream:
                if chunk and chunk.text:
                    yielded = True
                    yield chunk.text
            if yielded:
                return
        except Exception:
            continue

    yield "⚠️ The AI scholar is momentarily resting. Please try again in a moment."


def scroll_to_top():
    """
    Injects a lightweight JavaScript snippet to scroll the main Streamlit container to (0, 0)
    on page or view transitions.
    """
    import streamlit as st
    import streamlit.components.v1 as components
    components.html("""
    <script>
        try {
            const mainSection = window.parent.document.querySelector('section.main');
            if (mainSection) {
                mainSection.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        } catch (e) {
            window.scrollTo(0, 0);
        }
    </script>
    """, height=0)


def init_session_state():
    """
    Safely initialize all required Streamlit session state keys.
    Prevents key collisions and widget duplication errors.
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
        "writer_mode": "Mode 1: Interactive Book Editor & Design Studio",
        "selected_book_for_chat": "",
        "chat_messages": [
            {"role": "assistant", "content": "👋 Hello! I am your Pen2Publish AI Literary Scholar (powered by Gemini 3.5 Flash-Lite). Ask me anything about any book, upload research papers to chat, or explore chapter breakdowns!"}
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
        "reader_scanner_details": None,
        # RAG Chat with Document State
        "rag_document_text": "",
        "rag_document_name": "",
        "rag_document_chunks": [],
        # Mode 1 CapCut-style State
        "mode1_canvas_mode": "template",
        "mode1_selected_template": "modern",
        "mode1_editor_text": "",
        "mode1_font_family": "Modern Sans-Serif",
        "mode1_font_size": 16,
        "mode1_alignment": "Left",
        # Controlled AI Co-Pilot Parameters
        "copilot_action_type": "Continue Writing",
        "copilot_tone": "Academic",
        "copilot_word_length": "Medium (400 words)",
        # Cross-Module State
        "research_notes_for_writer": "",
        # Mode 2 Full Book Generator State
        "m2_selected_palette": "Warm Ivory & Emerald",
        "m2_selected_template": "Luxury Editorial",
        "mode2_raw_manuscript": "",
        "mode2_compiled_pdf": None,
        "mode2_compiled_title": "",
        "m2_blurb_content": "",
        "m2_generated_cover_art": None,
        "book_title_state": "The Architecture of Tomorrow",
        "book_genre_state": "Non-Fiction",
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
