import os
import config.settings as settings
from utils.helpers import call_gemini_with_fallback

def compose_and_research_book(prompt_text, mode="research"):
    api_key = getattr(settings, "GEMINI_API_KEY_CREATOR", None) or getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "⚠️ Gemini API Key missing! Check .env or settings file."

    if mode == "research":
        system_prompt = "You are an expert literary research assistant. Help the writer organize facts, outlines, and ideas."
    elif mode == "compose":
        system_prompt = "You are a professional book editor and formatter. Convert raw notes into structured book chapters with proper titles and headings."
    elif mode == "title_cover":
        system_prompt = "Suggest 5 catchy book titles, a subtitle, and a detailed cover art description based on the provided story summary."
    else:
        system_prompt = "You are a helpful writing assistant."

    full_prompt = f"{system_prompt}\n\nWriter Input:\n{prompt_text}"

    success, result = call_gemini_with_fallback(api_key, full_prompt)
    return result
