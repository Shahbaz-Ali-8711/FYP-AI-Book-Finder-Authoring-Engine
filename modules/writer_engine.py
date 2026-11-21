import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape
import config.settings as settings
from utils.helpers import call_gemini_with_fallback
from database.db_handler import log_author_event


def _get_api_key():
    return (
        getattr(settings, "GEMINI_API_KEY_CREATOR", None) or
        getattr(settings, "GEMINI_API_KEY", None) or
        os.getenv("GEMINI_API_KEY", "")
    )


def clean_text_for_pdf(text):
    """
    Sanitizes Unicode text for safe rendering in standard PDF fonts without encoding crashes.
    """
    if not text:
        return ""

    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--", "\u2026": "...", "\u00a0": " ",
        "\u2022": "*", "\u2039": "<", "\u203a": ">", "\u00b7": "*",
        "\t": "    ", "\r": ""
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)

    return text.encode("latin-1", "replace").decode("latin-1")


# ==============================================================================
# INTEGRATED AI CO-PILOT HELPERS FOR WRITERS
# ==============================================================================
def ai_copilot_continue_writing(current_text, direction=""):
    """
    Mode 1 Inline Assistant: Seamlessly continues writing from where the author left off.
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "⚠️ Gemini API key is missing. Please check your .env configuration."

    prompt = f"""
    You are a novelist and expert co-author writing directly beside the author.
    Here is the manuscript draft so far:
    \"\"\"{current_text[-3000:]}\"\"\"

    Specific Author Direction:
    {direction or "Continue the narrative naturally with engaging pacing, sensory detail, and dialogue."}

    Instructions:
    1. Continue writing the next 2-4 paragraphs seamlessly from the exact end of the draft.
    2. Maintain tone, voice, and momentum.
    3. Output ONLY the new continuation text so the author can directly append it. No meta comments.
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    if success:
        log_author_event("search", "AI Continue Writing")
    return success, result


def ai_copilot_expand_scene(scene_text, user_goal):
    """
    Expands an author's scene draft with rich sensory descriptions and emotional pacing.
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "⚠️ Gemini API key is missing."

    prompt = f"""
    You are a master literary editor.
    The writer is working on this excerpt:
    \"\"\"{scene_text[:3000]}\"\"\"

    Goal: {user_goal or "Deepen sensory pacing and character thoughts."}

    Expand this scene with rich sensory details, character interiority, and vivid prose. Provide only the expanded text in clean Markdown.
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    return success, result


def ai_copilot_polish_prose(draft_text, style_tone="Modern Literary"):
    """
    Polishes an excerpt for rhythm, diction, and grammatical elegance.
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "⚠️ Gemini API key missing."

    prompt = f"""
    Refine and polish the following excerpt into a **{style_tone}** tone:
    \"\"\"{draft_text[:3000]}\"\"\"

    Eliminate filler, enhance rhythm and cadence, and output the polished excerpt cleanly.
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    return success, result


def ai_copilot_generate_twist(story_context):
    """
    Synthesizes unexpected, foreshadowed plot twists.
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "⚠️ Gemini API key missing."

    prompt = f"""
    Based on this story context:
    \"\"\"{story_context[:3000]}\"\"\"

    Synthesize 3 distinct, actionable, and foreshadowed plot twists with clues to plant earlier.
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    return success, result


def ai_copilot_draft_blurb(title, genre, manuscript_sample):
    """
    Generates a high-converting back cover jacket blurb.
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "⚠️ Gemini API key missing."

    prompt = f"""
    Draft a high-converting back-cover jacket blurb for:
    Title: {title}
    Genre: {genre}
    Manuscript Context:
    \"\"\"{manuscript_sample[:3000]}\"\"\"

    Provide:
    1. A bold, punchy headline hook.
    2. A 2-paragraph premise raising central conflict and stakes.
    3. An emotional closing reader tagline.
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    return success, result


# ==============================================================================
# MODE 2: 5 CURATED COLOR PALETTES & 5 DESIGN TEMPLATES
# ==============================================================================
COLOR_PALETTES = {
    "Warm Ivory & Emerald": {
        "cover_bg": (250, 250, 245),
        "is_dark": False,
        "primary": (4, 106, 56),        # Emerald Green
        "secondary": (15, 82, 87),      # Deep Teal
        "accent": (227, 66, 52),        # Vermilion
        "frame_border": (4, 106, 56),
        "badge_bg": (240, 245, 240),
        "body_text": (26, 26, 26),
    },
    "Royal Navy & Gold": {
        "cover_bg": (10, 25, 47),        # Dark Navy
        "is_dark": True,
        "primary": (30, 58, 138),       # Royal Blue
        "secondary": (30, 64, 175),
        "accent": (217, 119, 6),        # Rich Gold
        "frame_border": (217, 119, 6),
        "badge_bg": (30, 41, 59),
        "body_text": (26, 26, 26),
    },
    "Midnight & Crimson": {
        "cover_bg": (24, 24, 27),        # Deep Midnight
        "is_dark": True,
        "primary": (153, 27, 27),       # Crimson
        "secondary": (39, 39, 42),
        "accent": (220, 38, 38),        # Bright Red
        "frame_border": (220, 38, 38),
        "badge_bg": (39, 39, 42),
        "body_text": (26, 26, 26),
    },
    "Charcoal & Teal": {
        "cover_bg": (30, 41, 59),        # Charcoal
        "is_dark": True,
        "primary": (13, 148, 136),      # Teal
        "secondary": (51, 65, 85),
        "accent": (20, 184, 166),       # Cyan Accent
        "frame_border": (13, 148, 136),
        "badge_bg": (51, 65, 85),
        "body_text": (26, 26, 26),
    },
    "Classic Monochrome": {
        "cover_bg": (248, 250, 252),
        "is_dark": False,
        "primary": (17, 24, 39),        # Charcoal Black
        "secondary": (75, 85, 99),
        "accent": (107, 114, 128),      # Slate Gray
        "frame_border": (17, 24, 39),
        "badge_bg": (243, 244, 246),
        "body_text": (17, 24, 39),
    }
}

LAYOUT_TEMPLATES = {
    "Luxury Editorial": {
        "font": "Helvetica",
        "description": "Prestigious literary aesthetic with wide margins, roman numeral chapter headings, and refined proportion.",
        "chapter_prefix": "BOOK CHAPTER",
        "ornament": "✦  ✦  ✦"
    },
    "Modern Tech/Business": {
        "font": "Helvetica",
        "description": "Bold modern corporate layout with structured callout lines, clean section dividers, and high readability.",
        "chapter_prefix": "MODULE",
        "ornament": "━ ━ ━ ━"
    },
    "Classic Literary Fiction": {
        "font": "Helvetica",
        "description": "Timeless fiction design with centered title pages, elegant chapter banners, and standard book margins.",
        "chapter_prefix": "CHAPTER",
        "ornament": "—  §  —"
    },
    "Academic Monograph": {
        "font": "Helvetica",
        "description": "Formal scholarly layout with numbered hierarchical divisions, structured citations, and rigorous formatting.",
        "chapter_prefix": "SECTION",
        "ornament": "•  •  •"
    },
    "Creative Minimalist": {
        "font": "Helvetica",
        "description": "Understated contemporary layout with spacious margins, clean typography, and distraction-free styling.",
        "chapter_prefix": "CHAPTER",
        "ornament": "· · ·"
    }
}


def generate_full_publish_book_pdf(
    title, subtitle, author, template_style, raw_text,
    palette_name="Warm Ivory & Emerald",
    blurb_summary="An inspiring and thought-provoking publication exploring human potential and ideas.",
    copyright_year="2026", publisher_name="Pen2Publish AI Global Press"
):
    """
    Compiles complete manuscripts (50 to 500+ pages) into a commercial-grade published book:
    1. Graphical Front Cover Page
    2. Title & Half-Title Page
    3. Copyright & Dedication Page
    4. Auto-Generated Table of Contents (TOC) with dot leaders
    5. Paginated Chapters with running headers/footers
    6. Styled Back Cover with Blurb and Barcode Box
    """
    try:
        from fpdf import FPDF

        palette = COLOR_PALETTES.get(palette_name, COLOR_PALETTES["Warm Ivory & Emerald"])
        layout = LAYOUT_TEMPLATES.get(template_style, LAYOUT_TEMPLATES["Luxury Editorial"])

        c_bg = palette["cover_bg"]
        is_dark = palette["is_dark"]
        p_r, p_g, p_b = palette["primary"]
        a_r, a_g, a_b = palette["accent"]
        body_r, body_g, body_b = palette["body_text"]

        clean_title = clean_text_for_pdf(title or "Untitled Publication")
        clean_sub = clean_text_for_pdf(subtitle or "A Comprehensive Study and Narrative")
        clean_auth = clean_text_for_pdf(author or "Autonomous Author")
        clean_blurb = clean_text_for_pdf(blurb_summary or "Explore deep ideas, stories, and frameworks.")
        clean_pub = clean_text_for_pdf(publisher_name or "Pen2Publish AI Press")
        ornament = layout.get("ornament", "✦ ✦ ✦")

        class PublishedLuxuryPDF(FPDF):
            def __init__(self):
                super().__init__(format="A4", unit="mm")
                self.set_auto_page_break(auto=True, margin=22)

            def header(self):
                # Only on chapter pages (page 4 and beyond, not back cover)
                if self.page_no() >= 4 and not getattr(self, "is_back_cover", False):
                    self.set_font("Helvetica", "I", 8.5)
                    self.set_text_color(120, 120, 120)
                    self.cell(0, 6, f"{clean_title}   |   {clean_auth}", align="R")
                    self.ln(8)

            def footer(self):
                if self.page_no() >= 4 and not getattr(self, "is_back_cover", False):
                    self.set_y(-15)
                    self.set_font("Helvetica", "", 9)
                    self.set_text_color(120, 120, 120)
                    self.cell(0, 10, f"- {self.page_no()} -", align="C")

        pdf = PublishedLuxuryPDF()

        # ======================================================================
        # 1. GRAPHICAL FRONT COVER PAGE
        # ======================================================================
        pdf.add_page()

        # Fill full cover background
        pdf.set_fill_color(c_bg[0], c_bg[1], c_bg[2])
        pdf.rect(0, 0, 210, 297, style="F")

        # Decorative double frame
        frame_r, frame_g, frame_b = palette["frame_border"]
        pdf.set_draw_color(frame_r, frame_g, frame_b)
        pdf.set_line_width(1.8)
        pdf.rect(12, 12, 186, 273)
        pdf.set_line_width(0.6)
        pdf.rect(14.5, 14.5, 181, 268)

        # Top Category Badge Pill
        pdf.ln(25)
        pdf.set_fill_color(palette["badge_bg"][0], palette["badge_bg"][1], palette["badge_bg"][2])
        badge_text = f"  *  {template_style.upper()} EDITION  *  "
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(a_r, a_g, a_b)
        pdf.cell(0, 7, badge_text, align="C")
        pdf.ln(30)

        # Book Title
        cover_title_color = (255, 255, 255) if is_dark else (p_r, p_g, p_b)
        pdf.set_font("Helvetica", "B", 27)
        pdf.set_text_color(cover_title_color[0], cover_title_color[1], cover_title_color[2])
        pdf.multi_cell(0, 12, clean_title, align="C")
        pdf.ln(6)

        # Subtitle
        if clean_sub:
            sub_color = (220, 220, 225) if is_dark else (80, 80, 80)
            pdf.set_font("Helvetica", "I", 13)
            pdf.set_text_color(sub_color[0], sub_color[1], sub_color[2])
            pdf.multi_cell(0, 7.5, clean_sub, align="C")
            pdf.ln(18)
        else:
            pdf.ln(18)

        # Center Divider Geometry
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(a_r, a_g, a_b)
        pdf.cell(0, 6, ornament, align="C")
        pdf.ln(22)

        # Author Badge
        author_color = (250, 250, 250) if is_dark else (20, 20, 20)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(author_color[0], author_color[1], author_color[2])
        pdf.cell(0, 8, f"BY  {clean_auth.upper()}", align="C")
        pdf.ln(65)

        # Publisher Mark
        pub_color = (180, 180, 190) if is_dark else (115, 115, 115)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(pub_color[0], pub_color[1], pub_color[2])
        pdf.cell(0, 5, f"{clean_pub}  *  EST. {copyright_year}", align="C")

        # ======================================================================
        # 2. TITLE PAGE & COPYRIGHT PAGE
        # ======================================================================
        pdf.add_page()
        pdf.ln(45)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(p_r, p_g, p_b)
        pdf.multi_cell(0, 10, clean_title, align="C")
        pdf.ln(5)

        pdf.set_font("Helvetica", "I", 12)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 6, f"by {clean_auth}", align="C")
        pdf.ln(65)

        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(110, 110, 110)
        pdf.cell(0, 5, f"Published by {clean_pub}", align="C")
        pdf.ln(5)
        pdf.cell(0, 5, f"Copyright (c) {copyright_year} by {clean_auth}. All rights reserved.", align="C")
        pdf.ln(5)
        pdf.cell(0, 5, f"Format: {template_style}  |  Palette: {palette_name}", align="C")
        pdf.ln(5)
        pdf.cell(0, 5, "Cataloged & Published via Pen2Publish AI Engine.", align="C")
        pdf.ln(35)

        pdf.set_font("Helvetica", "I", 9.5)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 6, '"Dedicated to dedicated authors, curious readers, and the boundless potential of human imagination."', align="C")

        # ======================================================================
        # 3. AUTO-GENERATED TABLE OF CONTENTS (TOC)
        # ======================================================================
        raw_lines = raw_text.split("\n")
        chapters_data = []
        current_ch_title = None
        current_ch_lines = []

        for line in raw_lines:
            s_clean = clean_text_for_pdf(line.strip())
            if not s_clean:
                continue

            is_ch = (
                s_clean.upper().startswith("CHAPTER") or
                s_clean.startswith("# ") or
                s_clean.upper().startswith("PART ") or
                s_clean.upper().startswith("MODULE") or
                s_clean.upper().startswith("ACT ")
            )
            if is_ch:
                if current_ch_title:
                    chapters_data.append((current_ch_title, current_ch_lines))
                    current_ch_lines = []
                current_ch_title = s_clean.lstrip("# ").strip()
            else:
                if not current_ch_title:
                    current_ch_title = f"{layout.get('chapter_prefix', 'CHAPTER')} 1: Opening Discourse"
                current_ch_lines.append(s_clean)

        if current_ch_title:
            chapters_data.append((current_ch_title, current_ch_lines))

        if not chapters_data:
            chapters_data = [(f"{layout.get('chapter_prefix', 'CHAPTER')} 1: The Manuscript", [clean_text_for_pdf(l.strip()) for l in raw_lines if l.strip()])]

        pdf.add_page()
        pdf.ln(15)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(p_r, p_g, p_b)
        pdf.cell(0, 10, "TABLE OF CONTENTS", align="C")
        pdf.ln(14)

        pdf.set_font("Helvetica", "", 10.5)
        for idx, (ch_name, _) in enumerate(chapters_data, 1):
            pdf.set_text_color(body_r, body_g, body_b)
            # Dot leaders
            col_w = 140
            ch_str = f"{idx}. {ch_name[:50]}"
            pdf.cell(col_w, 7, ch_str, align="L")
            pdf.set_text_color(130, 130, 130)
            pdf.cell(0, 7, f"Chapter {idx}", align="R")
            pdf.ln(6.5)

        # ======================================================================
        # 4. FORMATTED CHAPTERS
        # ======================================================================
        prefix_tag = layout.get("chapter_prefix", "CHAPTER")
        for idx, (ch_name, ch_paragraphs) in enumerate(chapters_data, 1):
            pdf.add_page()
            pdf.ln(15)

            # Styled Chapter Header
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(a_r, a_g, a_b)
            pdf.cell(0, 6, f"-- {prefix_tag} {idx} --", align="C")
            pdf.ln(6)

            pdf.set_font("Helvetica", "B", 19)
            pdf.set_text_color(p_r, p_g, p_b)
            pdf.multi_cell(0, 9.5, ch_name, align="C")
            pdf.ln(8)

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(a_r, a_g, a_b)
            pdf.cell(0, 5, ornament, align="C")
            pdf.ln(14)

            # Body Paragraphs
            pdf.set_font("Helvetica", "", 10.5)
            pdf.set_text_color(body_r, body_g, body_b)

            for p in ch_paragraphs:
                if p.startswith("## ") or p.startswith("### "):
                    pdf.ln(4)
                    pdf.set_font("Helvetica", "B", 12.5)
                    pdf.set_text_color(p_r, p_g, p_b)
                    pdf.multi_cell(0, 7, p.lstrip("# ").strip())
                    pdf.set_font("Helvetica", "", 10.5)
                    pdf.set_text_color(body_r, body_g, body_b)
                    pdf.ln(2.5)
                elif p.startswith("* ") or p.startswith("- ") or p.startswith("• "):
                    clean_b = p.lstrip("*-• ").strip()
                    pdf.multi_cell(0, 6, f"   *  {clean_b}")
                    pdf.ln(1.5)
                else:
                    pdf.multi_cell(0, 6.2, f"    {p}")
                    pdf.ln(2.5)

        # ======================================================================
        # 5. STYLED BACK COVER PAGE
        # ======================================================================
        pdf.is_back_cover = True
        pdf.add_page()

        # Fill back cover background
        pdf.set_fill_color(c_bg[0], c_bg[1], c_bg[2])
        pdf.rect(0, 0, 210, 297, style="F")

        # Matching border frame
        pdf.set_draw_color(frame_r, frame_g, frame_b)
        pdf.set_line_width(1.8)
        pdf.rect(12, 12, 186, 273)
        pdf.set_line_width(0.6)
        pdf.rect(14.5, 14.5, 181, 268)

        back_hdr_color = (255, 255, 255) if is_dark else (p_r, p_g, p_b)
        pdf.ln(30)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(back_hdr_color[0], back_hdr_color[1], back_hdr_color[2])
        pdf.cell(0, 8, "ABOUT THE BOOK", align="C")
        pdf.ln(12)

        back_body_color = (225, 225, 230) if is_dark else (40, 40, 40)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(back_body_color[0], back_body_color[1], back_body_color[2])
        pdf.set_left_margin(25)
        pdf.set_right_margin(25)
        pdf.multi_cell(160, 6.2, clean_blurb, align="L")
        pdf.ln(20)

        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(back_hdr_color[0], back_hdr_color[1], back_hdr_color[2])
        pdf.cell(0, 6, f"AUTHOR PROFILE: {clean_auth.upper()}", align="C")
        pdf.ln(8)

        pdf.set_font("Helvetica", "I", 9.5)
        sub_bio_color = (200, 200, 210) if is_dark else (75, 75, 75)
        pdf.set_text_color(sub_bio_color[0], sub_bio_color[1], sub_bio_color[2])
        pdf.multi_cell(160, 5.5, f"{clean_auth} is a published creator authoring with Pen2Publish AI. This work represents a complete synthesis of vision, design, and ideas.", align="C")
        pdf.ln(45)

        # Barcode & ISBN Box
        barcode_border = (100, 100, 100) if is_dark else (180, 180, 180)
        pdf.set_draw_color(barcode_border[0], barcode_border[1], barcode_border[2])
        pdf.rect(80, 235, 50, 20)
        pdf.set_y(241)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(0, 4, "[ OFFICIAL EDITION ISBN ]", align="C")
        pdf.set_y(246)
        pdf.cell(0, 4, f"ISBN-2026-P2P-{abs(hash(clean_title)) % 1000000}", align="C")

        out_buffer = io.BytesIO()
        pdf.output(out_buffer)
        log_author_event("export_pdf", clean_title)
        return out_buffer.getvalue(), None

    except Exception as e:
        return None, f"Full Book PDF Compilation failed: {str(e)}"


# ==============================================================================
# STANDARD EXPORTERS (EPUB, DOCX)
# ==============================================================================
def export_book_to_epub(title, author, content_text):
    """Compiles content into standard IDPF OEBPS EPUB publication."""
    try:
        epub_buf = io.BytesIO()
        lines = content_text.split("\n")
        chapters = []
        current_title = "Prologue"
        current_paras = []

        for line in lines:
            s = line.strip()
            if s.startswith("# ") or s.upper().startswith("CHAPTER") or s.upper().startswith("ACT ") or s.upper().startswith("MODULE"):
                if current_paras:
                    chapters.append((current_title, current_paras))
                    current_paras = []
                current_title = s.lstrip("# ")
            elif s:
                current_paras.append(s)
        if current_paras:
            chapters.append((current_title, current_paras))

        with zipfile.ZipFile(epub_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)

            container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
            zf.writestr("META-INF/container.xml", container_xml)

            css = """
            body { font-family: sans-serif; line-height: 1.6; margin: 5%; color: #1A1A1A; background-color: #FAFAF5; }
            h1 { color: #046A38; text-align: center; border-bottom: 2px solid #046A38; padding-bottom: 0.3em; }
            h2 { color: #E34234; }
            p { margin-bottom: 1em; text-indent: 1.2em; }
            .cover-title { font-size: 2.2em; text-align: center; margin-top: 25%; font-weight: bold; color: #046A38; }
            .cover-author { font-size: 1.2em; text-align: center; color: #E34234; }
            """
            zf.writestr("OEBPS/stylesheet.css", css)

            manifest_items = []
            spine_items = []

            title_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{xml_escape(title)}</title><link rel="stylesheet" type="text/css" href="stylesheet.css"/></head>
<body>
  <div class="cover-title">{xml_escape(title)}</div>
  <div class="cover-author">by {xml_escape(author)}</div>
</body>
</html>"""
            zf.writestr("OEBPS/title.xhtml", title_html)
            manifest_items.append('<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append('<itemref idref="title"/>')

            for idx, (ch_title, paras) in enumerate(chapters, 1):
                paras_html = "\n".join([f"<p>{xml_escape(p)}</p>" for p in paras])
                ch_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{xml_escape(ch_title)}</title><link rel="stylesheet" type="text/css" href="stylesheet.css"/></head>
<body>
  <h1>{xml_escape(ch_title)}</h1>
  {paras_html}
</body>
</html>"""
                fname = f"chapter_{idx}.xhtml"
                zf.writestr(f"OEBPS/{fname}", ch_html)
                manifest_items.append(f'<item id="ch_{idx}" href="{fname}" media-type="application/xhtml+xml"/>')
                spine_items.append(f'<itemref idref="ch_{idx}"/>')

            content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{xml_escape(title)}</dc:title>
    <dc:creator>{xml_escape(author)}</dc:creator>
    <dc:language>en</dc:language>
    <dc:publisher>Pen2Publish AI</dc:publisher>
    <dc:identifier id="BookID">urn:uuid:p2p-{abs(hash(title))}</dc:identifier>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="stylesheet.css" media-type="text/css"/>
    {"".join(manifest_items)}
  </manifest>
  <spine toc="ncx">
    {"".join(spine_items)}
  </spine>
</package>"""
            zf.writestr("OEBPS/content.opf", content_opf)

            nav_points = []
            for idx, (ch_title, _) in enumerate(chapters, 1):
                nav_points.append(f"""
    <navPoint id="nav_{idx}" playOrder="{idx}">
      <navLabel><text>{xml_escape(ch_title)}</text></navLabel>
      <content src="chapter_{idx}.xhtml"/>
    </navPoint>""")

            toc_ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:p2p-{abs(hash(title))}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{xml_escape(title)}</text></docTitle>
  <navMap>
    {"".join(nav_points)}
  </navMap>
</ncx>"""
            zf.writestr("OEBPS/toc.ncx", toc_ncx)

        log_author_event("export_epub", title)
        return epub_buf.getvalue(), None
    except Exception as e:
        return None, f"EPUB export failed: {str(e)}"


def export_book_to_docx(title, author, content_text):
    """Compiles chapters into Microsoft Word (.docx) package with zero external dependencies."""
    try:
        docx_buf = io.BytesIO()
        lines = content_text.split("\n")

        body_xml_parts = []
        body_xml_parts.append(f"""
        <w:p>
          <w:pPr><w:jc w:val="center"/><w:spacing w:before="720" w:after="240"/></w:pPr>
          <w:r><w:rPr><w:b/><w:sz w:val="56"/><w:color w:val="046A38"/></w:rPr><w:t>{xml_escape(title)}</w:t></w:r>
        </w:p>
        <w:p>
          <w:pPr><w:jc w:val="center"/><w:spacing w:after="720"/></w:pPr>
          <w:r><w:rPr><w:i/><w:sz w:val="28"/><w:color w:val="E34234"/></w:rPr><w:t>by {xml_escape(author)}</w:t></w:r>
        </w:p>
        """)

        for line in lines:
            s = line.strip()
            if not s:
                continue
            if s.startswith("# ") or s.upper().startswith("CHAPTER") or s.upper().startswith("ACT ") or s.upper().startswith("MODULE"):
                body_xml_parts.append(f"""
                <w:p>
                  <w:pPr>
                    <w:pStyle w:val="Heading1"/>
                    <w:pageBreakBefore/>
                    <w:spacing w:before="480" w:after="240"/>
                  </w:pPr>
                  <w:r><w:rPr><w:b/><w:sz w:val="36"/><w:color w:val="046A38"/></w:rPr><w:t>{xml_escape(s.lstrip("# "))}</w:t></w:r>
                </w:p>
                """)
            elif s.startswith("## ") or s.startswith("### "):
                body_xml_parts.append(f"""
                <w:p>
                  <w:pPr><w:pStyle w:val="Heading2"/><w:spacing w:before="240" w:after="120"/></w:pPr>
                  <w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="E34234"/></w:rPr><w:t>{xml_escape(s.lstrip("# "))}</w:t></w:r>
                </w:p>
                """)
            else:
                body_xml_parts.append(f"""
                <w:p>
                  <w:pPr><w:spacing w:line="360" w:lineRule="auto" w:after="180"/></w:pPr>
                  <w:r><w:rPr><w:sz w:val="24"/><w:color w:val="1A1A1A"/></w:rPr><w:t>{xml_escape(s)}</w:t></w:r>
                </w:p>
                """)

        doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {"".join(body_xml_parts)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""

        content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

        rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

        with zipfile.ZipFile(docx_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", content_types_xml)
            zf.writestr("_rels/.rels", rels_xml)
            zf.writestr("word/document.xml", doc_xml)

        log_author_event("export_docx", title)
        return docx_buf.getvalue(), None
    except Exception as e:
        return None, f"DOCX export failed: {str(e)}"
