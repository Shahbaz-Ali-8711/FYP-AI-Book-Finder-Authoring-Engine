import io
import re
from utils.helpers import call_gemini_with_fallback
from config.settings import GEMINI_API_KEY


def extract_text_from_upload(uploaded_file):
    if uploaded_file is None:
        return "", "No file provided."

    file_type = uploaded_file.type
    file_name = getattr(uploaded_file, "name", "unknown")

    try:
        if "pdf" in file_type or file_name.lower().endswith(".pdf"):
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"
                return text.strip(), None
            except ImportError:
                return "", "PyPDF2 not installed. Run: pip install PyPDF2"
        else:
            raw = uploaded_file.getvalue()
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    return raw.decode(encoding).strip(), None
                except UnicodeDecodeError:
                    continue
            return "", "Could not decode file."
    except Exception as e:
        return "", f"Error reading file: {str(e)}"


def structure_into_chapters(raw_text):
    if not GEMINI_API_KEY:
        return raw_text, "⚠️ Gemini API Key missing — returning raw text."

    if len(raw_text) < 200:
        return raw_text, "Text too short for structuring."

    prompt = f"""
    You are a professional book formatter. Structure the following raw text into clean, well-organized chapters.

    Rules:
    1. Identify natural chapter breaks and add "CHAPTER X: Title" headers
    2. Add proper paragraph breaks
    3. Remove duplicate whitespace
    4. Add a "TABLE OF CONTENTS" at the top
    5. Keep all original content — do NOT summarize or remove text
    6. Output in clean markdown format

    Raw Text:
    ---
    {raw_text[:15000]}
    ---
    """

    success, result = call_gemini_with_fallback(GEMINI_API_KEY, prompt)
    if success:
        return result, None
    return raw_text, result


def generate_formatted_pdf(title, author, structured_text):
    try:
        from fpdf import FPDF

        pdf = FPDF(format="A4")
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 28)
        pdf.multi_cell(0, 12, title, align="C")
        pdf.ln(10)

        pdf.set_font("Helvetica", "", 14)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 8, f"by {author}", align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(20)

        lines = structured_text.split("\n")
        for line in lines:
            stripped = line.strip()
            if not stripped:
                pdf.ln(5)
                continue

            if stripped.startswith("CHAPTER") or stripped.startswith("Chapter"):
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 20)
                pdf.set_text_color(99, 102, 241)
                pdf.multi_cell(0, 10, stripped, align="C")
                pdf.set_text_color(0, 0, 0)
                pdf.ln(10)
            elif stripped.startswith("TABLE OF CONTENTS"):
                pdf.set_font("Helvetica", "B", 16)
                pdf.set_text_color(99, 102, 241)
                pdf.multi_cell(0, 8, stripped, align="C")
                pdf.set_text_color(0, 0, 0)
                pdf.ln(5)
            elif stripped.startswith("#"):
                clean = stripped.lstrip("# ").strip()
                pdf.set_font("Helvetica", "B", 14)
                pdf.multi_cell(0, 7, clean)
                pdf.ln(3)
            elif stripped.startswith("- ") or stripped.startswith("* "):
                clean = stripped.lstrip("-* ").strip()
                pdf.set_font("Helvetica", "", 11)
                pdf.multi_cell(0, 6, f"  • {clean}")
            else:
                pdf.set_font("Helvetica", "", 11)
                pdf.multi_cell(0, 6, stripped)

        output = io.BytesIO()
        pdf.output(output)
        return output.getvalue(), None

    except ImportError:
        return None, "fpdf2 not installed. Run: pip install fpdf2"
    except Exception as e:
        return None, f"PDF generation error: {str(e)}"


def estimate_pages(text):
    words = len(text.split())
    return max(1, words // 300)