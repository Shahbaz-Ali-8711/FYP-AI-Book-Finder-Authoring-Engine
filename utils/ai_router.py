import os
import io
import re
import time
from typing import Generator, Tuple, Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Provider Model Definitions
GROQ_TEXT_MODEL = "openai/gpt-oss-120b"
GROQ_LIGHT_MODEL = "openai/gpt-oss-20b"
GROQ_TEXT_FALLBACKS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
GROQ_LIGHT_FALLBACKS = ["openai/gpt-oss-20b", "llama-3.1-8b-instant"]

GEMINI_FAST_MODEL = "gemini-3.5-flash-lite"
GEMINI_PRO_MODEL = "gemini-3.8-flash"
GEMINI_FALLBACKS = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.0-flash"]


# ==============================================================================
# KEY RESOLUTION & CLIENT INITIALIZATION
# ==============================================================================
def get_groq_api_key() -> str:
    """
    Retrieves GROQ_API_KEY from st.secrets first (Cloud), then os.getenv (.env).
    """
    key = ""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    if not key:
        key = os.getenv("GROQ_API_KEY", "")

    return (key or "").strip().strip('"').strip("'")


def get_gemini_api_key() -> str:
    """
    Retrieves GEMINI_API_KEY from st.secrets first (Cloud), then os.getenv (.env).
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


def is_groq_available() -> bool:
    return bool(get_groq_api_key())


def is_gemini_available() -> bool:
    return bool(get_gemini_api_key())


def get_groq_client():
    key = get_groq_api_key()
    if not key:
        return None
    try:
        import groq
        return groq.Groq(api_key=key)
    except Exception:
        return None


def get_gemini_client():
    key = get_gemini_api_key()
    if not key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=key)
    except Exception:
        return None


# ==============================================================================
# UI BADGE HELPERS
# ==============================================================================
def render_ai_badge(provider: str, model: str = "", task: str = "") -> str:
    """
    Generates an elegant HTML badge matching Warm Ivory, Emerald Green, and Vermilion palette.
    """
    prov_lower = (provider or "").lower()

    if "groq" in prov_lower:
        display_name = f"⚡ Powered by Groq LPU ({model or GROQ_TEXT_MODEL})"
        bg = "rgba(227, 66, 52, 0.08)"
        color = "#E34234"
        border = "rgba(227, 66, 52, 0.28)"
    elif "gemini" in prov_lower:
        if "3.8" in model or task in ("outline", "full_book", "blurb"):
            display_name = f"✨ Powered by Gemini 3.8 Flash ({model or GEMINI_PRO_MODEL})"
        elif task == "vision":
            display_name = f"👁️ Powered by Gemini Multimodal ({model or GEMINI_FAST_MODEL})"
        elif task in ("rag_large_doc", "doc_chat"):
            display_name = f"📖 Powered by Gemini 1M Context ({model or GEMINI_FAST_MODEL})"
        else:
            display_name = f"✨ Powered by Gemini ({model or GEMINI_FAST_MODEL})"
        bg = "rgba(4, 106, 56, 0.08)"
        color = "#046A38"
        border = "rgba(4, 106, 56, 0.28)"
    else:
        display_name = f"🤖 AI Engine ({model})"
        bg = "#F5F5ED"
        color = "#1A1A1A"
        border = "#E5E5DC"

    return f"""<span style="display: inline-flex; align-items: center; gap: 0.35rem; background: {bg}; color: {color}; border: 1px solid {border}; font-size: 0.74rem; font-weight: 800; padding: 0.22rem 0.7rem; border-radius: 9999px; letter-spacing: 0.02em;">{display_name}</span>"""


def set_last_ai_badge(provider: str, model: str = "", task: str = ""):
    try:
        import streamlit as st
        st.session_state["last_ai_router_provider"] = provider
        st.session_state["last_ai_router_model"] = model
        st.session_state["last_ai_router_task"] = task
        st.session_state["last_ai_router_badge"] = render_ai_badge(provider, model, task)
    except Exception:
        pass


def get_last_ai_badge() -> str:
    try:
        import streamlit as st
        return st.session_state.get("last_ai_router_badge", render_ai_badge("groq", GROQ_TEXT_MODEL))
    except Exception:
        return render_ai_badge("groq", GROQ_TEXT_MODEL)


# ==============================================================================
# ROUTING DECISION MATRIX
# ==============================================================================
def decide_primary_engine(
    task: str = "chat",
    context_length: int = 0,
    is_urdu: bool = False,
    preferred_engine: str = "auto"
) -> Tuple[str, str]:
    """
    Evaluates master routing rules and returns (provider, model_name).
    """
    # Rule 1: Vision OCR ALWAYS to Gemini Multimodal
    if task == "vision":
        return ("gemini", GEMINI_FAST_MODEL)

    # Rule 2: Full Book Outlines & Long-context compilation to Gemini 3.8 Flash
    if task in ("outline", "full_book", "blurb") or preferred_engine == "gemini_pro":
        if is_gemini_available() or not is_groq_available():
            return ("gemini", GEMINI_PRO_MODEL)
        return ("groq", GROQ_TEXT_MODEL)

    # Rule 3: Large documents (>15,000 chars) or Urdu to Gemini for 1M context and superior Urdu
    if is_urdu or context_length > 15000 or task in ("rag_large_doc", "doc_chat_large"):
        if is_gemini_available() or not is_groq_available():
            return ("gemini", GEMINI_FAST_MODEL)
        return ("groq", GROQ_TEXT_MODEL)

    # Rule 4: Academic Citations to Groq Light (openai/gpt-oss-20b)
    if task == "citations" or preferred_engine == "groq_light":
        if is_groq_available() or not is_gemini_available():
            return ("groq", GROQ_LIGHT_MODEL)
        return ("gemini", GEMINI_FAST_MODEL)

    # Rule 5: Standard Conversational Chat, Fast Co-Pilot, Quick Summaries to Groq (openai/gpt-oss-120b)
    if task in ("chat", "copilot_fast", "summary", "quick_qa"):
        if is_groq_available() or not is_gemini_available():
            return ("groq", GROQ_TEXT_MODEL)
        return ("gemini", GEMINI_FAST_MODEL)

    # Default fallback routing
    if is_groq_available():
        return ("groq", GROQ_TEXT_MODEL)
    return ("gemini", GEMINI_FAST_MODEL)


# ==============================================================================
# LOW-LEVEL PROVIDER EXECUTION WITH INTERNAL FALLBACKS
# ==============================================================================
def _call_groq(prompt: str, model_candidate: str, system_prompt: str = "") -> Tuple[bool, str, str]:
    """
    Executes a prompt on Groq with automated model candidate iteration.
    Returns: (success, result_text, used_model)
    """
    client = get_groq_client()
    if not client:
        return False, "Groq client unavailable (missing GROQ_API_KEY)", ""

    candidates = [model_candidate]
    if "20b" in model_candidate:
        candidates.extend([m for m in GROQ_LIGHT_FALLBACKS if m not in candidates])
    else:
        candidates.extend([m for m in GROQ_TEXT_FALLBACKS if m not in candidates])

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    last_err = ""
    for m in candidates:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                timeout=15.0
            )
            if resp and resp.choices and resp.choices[0].message:
                out = (resp.choices[0].message.content or "").strip()
                if out:
                    return True, out, m
        except Exception as e:
            last_err = str(e)
            # If rate limited (429) or token limit, don't waste time on other groq models; abort to Gemini
            if "429" in last_err or "rate_limit" in last_err.lower() or "quota" in last_err.lower():
                break
            continue

    return False, f"Groq execution failed: {last_err}", ""


def _call_gemini(prompt: Any, model_candidate: str) -> Tuple[bool, str, str]:
    """
    Executes a prompt on Gemini using google-genai SDK.
    Returns: (success, result_text, used_model)
    """
    client = get_gemini_client()
    if not client:
        return False, "Gemini client unavailable (missing GEMINI_API_KEY)", ""

    candidates = [model_candidate]
    for m in GEMINI_FALLBACKS:
        if m not in candidates:
            candidates.append(m)

    last_err = ""
    for m in candidates:
        try:
            resp = client.models.generate_content(
                model=m,
                contents=prompt
            )
            if resp and resp.text:
                return True, resp.text.strip(), m
        except Exception as e:
            last_err = str(e)
            continue

    return False, f"Gemini execution failed: {last_err}", ""


# ==============================================================================
# UNIFIED COMPLETION ROUTER (CROSS-PROVIDER AUTOMATIC FALLBACK)
# ==============================================================================
def route_ai_completion(
    prompt: Any,
    task: str = "chat",
    context_length: int = 0,
    is_urdu: bool = False,
    preferred_engine: str = "auto",
    system_prompt: str = ""
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes an AI completion request across Groq and Gemini with automatic
    cross-provider fallback on rate limits or errors.
    Returns: (success: bool, text_response: str, metadata: dict)
    """
    primary_provider, target_model = decide_primary_engine(task, context_length, is_urdu, preferred_engine)

    # 1. Vision must always be handled by Gemini
    if task == "vision":
        ok, res, used_model = _call_gemini(prompt, GEMINI_FAST_MODEL)
        set_last_ai_badge("gemini", used_model or GEMINI_FAST_MODEL, "vision")
        return ok, res, {"provider": "gemini", "model": used_model or GEMINI_FAST_MODEL, "task": "vision"}

    # 2. If Groq is primary
    if primary_provider == "groq":
        ok, res, used_model = _call_groq(str(prompt), target_model, system_prompt)
        if ok:
            set_last_ai_badge("groq", used_model, task)
            return True, res, {"provider": "groq", "model": used_model, "task": task}

        # Seamless Cross-Provider Fallback to Gemini
        gemini_model = GEMINI_PRO_MODEL if task in ("outline", "full_book", "blurb") else GEMINI_FAST_MODEL
        ok_g, res_g, used_g = _call_gemini(prompt, gemini_model)
        if ok_g:
            set_last_ai_badge("gemini", used_g, task)
            return True, res_g, {"provider": "gemini", "model": used_g, "task": task, "fallback": True}

        return False, "⚠️ All AI providers are momentarily busy. Please retry in a few seconds.", {}

    # 3. If Gemini is primary
    else:
        ok, res, used_model = _call_gemini(prompt, target_model)
        if ok:
            set_last_ai_badge("gemini", used_model, task)
            return True, res, {"provider": "gemini", "model": used_model, "task": task}

        # Seamless Cross-Provider Fallback to Groq (if text prompt)
        if isinstance(prompt, str):
            ok_gr, res_gr, used_gr = _call_groq(prompt, GROQ_TEXT_MODEL, system_prompt)
            if ok_gr:
                set_last_ai_badge("groq", used_gr, task)
                return True, res_gr, {"provider": "groq", "model": used_gr, "task": task, "fallback": True}

        return False, "⚠️ AI service temporarily unavailable. Please retry shortly.", {}


# ==============================================================================
# UNIFIED STREAMING ROUTER (CROSS-PROVIDER AUTOMATIC FALLBACK)
# ==============================================================================
def route_ai_stream(
    prompt: str,
    task: str = "chat",
    context_length: int = 0,
    is_urdu: bool = False,
    preferred_engine: str = "auto",
    system_prompt: str = ""
) -> Generator[str, None, None]:
    """
    Streams AI tokens word-by-word for st.write_stream across Groq and Gemini.
    """
    primary_provider, target_model = decide_primary_engine(task, context_length, is_urdu, preferred_engine)

    groq_client = get_groq_client()
    gemini_client = get_gemini_client()

    # Strategy A: Try Groq Streaming first if selected or available
    if primary_provider == "groq" and groq_client:
        candidates = [target_model]
        candidates.extend([m for m in GROQ_TEXT_FALLBACKS if m not in candidates])

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream_started = False
        for m in candidates:
            try:
                stream = groq_client.chat.completions.create(
                    model=m,
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=4096,
                    timeout=12.0
                )
                for chunk in stream:
                    if chunk and chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta.content or ""
                        if delta:
                            if not stream_started:
                                stream_started = True
                                set_last_ai_badge("groq", m, task)
                            yield delta
                if stream_started:
                    return
            except Exception as e:
                err_s = str(e).lower()
                if "429" in err_s or "quota" in err_s:
                    break
                continue

    # Strategy B: Gemini Streaming (Primary or Cross-Provider Fallback)
    if gemini_client:
        g_candidates = [target_model if primary_provider == "gemini" else GEMINI_FAST_MODEL]
        for m in GEMINI_FALLBACKS:
            if m not in g_candidates:
                g_candidates.append(m)

        for gm in g_candidates:
            try:
                g_stream = gemini_client.models.generate_content_stream(
                    model=gm,
                    contents=prompt
                )
                gemini_started = False
                for g_chunk in g_stream:
                    if g_chunk and g_chunk.text:
                        if not gemini_started:
                            gemini_started = True
                            set_last_ai_badge("gemini", gm, task)
                        yield g_chunk.text
                if gemini_started:
                    return
            except Exception:
                continue

    # Strategy C: If streaming was not supported, attempt standard non-streaming completion as fallback
    ok, res, meta = route_ai_completion(prompt, task, context_length, is_urdu, preferred_engine, system_prompt)
    if ok and res:
        yield res
    else:
        yield "⚠️ The AI service is momentarily busy. Please retry in a few seconds."


# ==============================================================================
# VISION MULTIMODAL ROUTER (GEMINI ONLY)
# ==============================================================================
def route_ai_vision(image_input: Any, prompt: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Dedicated Multimodal Vision pipeline routed exclusively to Gemini 3.5 Flash-Lite.
    """
    client = get_gemini_client()
    if not client:
        return False, "⚠️ Gemini API key is missing for Multimodal Vision OCR.", {}

    return route_ai_completion([prompt, image_input], task="vision")
