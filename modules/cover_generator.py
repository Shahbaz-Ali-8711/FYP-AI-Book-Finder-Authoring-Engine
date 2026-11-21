from google import genai
from config.settings import GEMINI_API_KEY
from utils.helpers import call_gemini_with_fallback

IMAGEN_MODELS = ['imagen-3.0-generate-002', 'imagen-3.0-fast-generate-001']


def generate_cover_prompt(book_title, genre, visual_description):
    if not GEMINI_API_KEY:
        return None, "⚠️ Gemini API Key missing! Check .env file."

    prompt = f"""
    You are a professional book cover art director.
    Create a detailed, vivid image generation prompt for a book cover.

    Book Title: {book_title}
    Genre: {genre}
    Visual Description: {visual_description}

    Requirements:
    - High-resolution book cover design
    - Professional typography placement
    - Genre-appropriate color palette
    - Compelling visual composition
    - No text rendering in the image (we will add title separately)

    Output only the image generation prompt, nothing else.
    """

    success, result = call_gemini_with_fallback(GEMINI_API_KEY, prompt)
    if success:
        return result.strip(), None
    return None, result


def generate_cover_image(book_title, genre, visual_description):
    if not GEMINI_API_KEY:
        return None, "⚠️ Gemini API Key missing! Check .env file."

    image_prompt, error = generate_cover_prompt(book_title, genre, visual_description)
    if error:
        return None, error

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        for model_name in IMAGEN_MODELS:
            try:
                response = client.models.generate_images(
                    model=model_name,
                    prompt=image_prompt,
                    config=genai.types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="2:3",
                    ),
                )
                if response and response.generated_images:
                    image_bytes = response.generated_images[0].image.image_bytes
                    return image_bytes, None
            except Exception:
                continue

        return None, f"⚠️ Image generation models are currently unavailable. Here's the AI-generated cover prompt you can use in any image tool:\n\n```\n{image_prompt}\n```"

    except Exception as e:
        return None, f"⚠️ Cover generation error: {str(e)}\n\nAI Prompt for manual use:\n```\n{image_prompt}\n```"