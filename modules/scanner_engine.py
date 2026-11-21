import io
import re
from PIL import Image
from config.settings import GEMINI_API_KEY
from utils.helpers import call_gemini_with_fallback
from modules.search_engine import search_free_books


def extract_text_from_image(image_input):
    """
    Extracts the exact Book Title and Author Name from a camera capture or uploaded image
    using Gemini Vision. Pre-compresses the image to max width 600px and JPEG quality 75%
    for lightning-fast 2-3 second execution.
    """
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API Key missing! Check .env file."

    try:
        if hasattr(image_input, "getvalue"):
            image_bytes = image_input.getvalue()
        elif hasattr(image_input, "read"):
            image_bytes = image_input.read()
        else:
            image_bytes = image_input

        image = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA/P to RGB
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        # ULTRA-FAST PRE-PROCESSING: Resize to max width 600px & Compress to 75% JPEG
        max_dimension = 600
        if image.width > max_dimension or image.height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        compressed_buffer = io.BytesIO()
        image.save(compressed_buffer, format="JPEG", quality=75, optimize=True)
        compressed_buffer.seek(0)
        fast_image = Image.open(compressed_buffer)

        prompt = """
        Examine this book cover image.
        Extract ONLY:
        TITLE: [Exact Book Title]
        AUTHOR: [Author Name]
        
        Keep it brief and exact. No conversational intro.
        """

        success, result = call_gemini_with_fallback(GEMINI_API_KEY, [prompt, fast_image])
        if success and result:
            clean_res = result.strip()
            title_match = re.search(r"TITLE:\s*(.+)", clean_res, re.IGNORECASE)
            author_match = re.search(r"AUTHOR:\s*(.+)", clean_res, re.IGNORECASE)

            if title_match and author_match:
                title = title_match.group(1).strip()
                author = author_match.group(1).strip()
                return f"{title} by {author}"
            elif title_match:
                return title_match.group(1).strip()
            else:
                return clean_res.replace("TITLE:", "").replace("AUTHOR:", "").strip()
        else:
            return f"Error: {result}"

    except Exception as e:
        return f"Error analyzing image: {str(e)}"


def scan_and_resolve_book(image_input):
    """
    Full pipeline: compresses image, extracts title/author in ~2s,
    and queries cached Gutenberg + Open Library for instant digital reading links.
    """
    detected_text = extract_text_from_image(image_input)
    if not detected_text or detected_text.startswith("Error") or detected_text.startswith("⚠️"):
        return False, detected_text, []

    search_query = detected_text.split(" by ")[0].strip() if " by " in detected_text else detected_text
    matches = search_free_books(search_query)

    return True, detected_text, matches
