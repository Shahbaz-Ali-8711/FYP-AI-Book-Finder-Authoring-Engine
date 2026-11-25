import io
import re
from PIL import Image
from utils.ai_router import route_ai_completion, render_ai_badge, get_gemini_api_key
from modules.search_engine import search_free_books


def extract_book_details_from_image(image_input):
    """
    Multimodal Vision extraction using Gemini 3.5 Flash-Lite:
    Extracts Book Title, Author, Genre, Key Themes, Synopsis, and Recommendations.
    Pre-compresses image to 600px max width and 75% quality for sub-2s speed.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return False, "⚠️ Gemini API Key missing! Check .env or Streamlit Secrets.", {}

    try:
        if hasattr(image_input, "getvalue"):
            image_bytes = image_input.getvalue()
        elif hasattr(image_input, "read"):
            image_bytes = image_input.read()
        else:
            image_bytes = image_input

        image = Image.open(io.BytesIO(image_bytes))

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        max_dimension = 600
        if image.width > max_dimension or image.height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        compressed_buffer = io.BytesIO()
        image.save(compressed_buffer, format="JPEG", quality=75, optimize=True)
        compressed_buffer.seek(0)
        fast_image = Image.open(compressed_buffer)

        prompt = """
        Examine this book cover photo carefully.
        Extract the following structured details:
        TITLE: [Exact Book Title]
        AUTHOR: [Author Name]
        GENRE: [Primary Literary Genre]
        THEMES: [2-3 Core Themes separated by commas]
        SYNOPSIS: [Concise 2-sentence summary of this book's premise]
        RECOMMENDATIONS: [3 similar acclaimed books separated by commas]

        Format each on a single line starting with the field name. Do not include conversational greetings.
        """

        success, result, meta = route_ai_completion([prompt, fast_image], task="vision")
        if not success or not result:
            return False, result or "Could not analyze image.", {}

        clean_res = result.strip()
        details = {
            "title": "Unknown Title",
            "author": "Unknown Author",
            "genre": "Literature",
            "themes": "Human Nature, Discovery",
            "synopsis": "A notable literary work exploring fundamental ideas.",
            "recommendations": "Classic Works"
        }

        t_m = re.search(r"TITLE:\s*(.+)", clean_res, re.IGNORECASE)
        a_m = re.search(r"AUTHOR:\s*(.+)", clean_res, re.IGNORECASE)
        g_m = re.search(r"GENRE:\s*(.+)", clean_res, re.IGNORECASE)
        th_m = re.search(r"THEMES:\s*(.+)", clean_res, re.IGNORECASE)
        s_m = re.search(r"SYNOPSIS:\s*(.+)", clean_res, re.IGNORECASE)
        r_m = re.search(r"RECOMMENDATIONS:\s*(.+)", clean_res, re.IGNORECASE)

        if t_m:
            details["title"] = t_m.group(1).strip()
        if a_m:
            details["author"] = a_m.group(1).strip()
        if g_m:
            details["genre"] = g_m.group(1).strip()
        if th_m:
            details["themes"] = th_m.group(1).strip()
        if s_m:
            details["synopsis"] = s_m.group(1).strip()
        if r_m:
            details["recommendations"] = r_m.group(1).strip()

        label = f"{details['title']} by {details['author']}"
        return True, label, details

    except Exception as e:
        return False, f"Vision OCR Error: {str(e)}", {}


def scan_and_resolve_book(image_input):
    """
    Full pipeline: compresses image, extracts complete structured details via Gemini 3.5 Flash-Lite,
    and searches Project Gutenberg & Open Library archives for digital copies.
    """
    success, label, details = extract_book_details_from_image(image_input)
    if not success:
        return False, label, [], {}

    search_query = details.get("title") or label.split(" by ")[0].strip()
    matches = search_free_books(search_query)

    return True, label, matches, details
