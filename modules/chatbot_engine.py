import os
import io
import re
import json
from utils.ai_router import (
    route_ai_completion, route_ai_stream, render_ai_badge, get_last_ai_badge,
    get_groq_api_key, get_gemini_api_key
)

CASUAL_GREETINGS = {
    "hi": "Hello! I am your Pen2Publish AI Literary Scholar. Powered by our Hybrid AI Engine (Groq LPU & Gemini Multimodal). Ask me anything about any book, chapter summaries, character arcs, or literary history!",
    "hello": "Hello! Welcome to the Reader AI Assistant. Ask me anything about any book, literary concepts, or chapter breakdowns. Which title is on your mind?",
    "hey": "Hey there! I am your AI Literary Companion. Tell me which book or research paper you're reading!",
    "how are you": "I am operating at peak analytical precision! Ready to summarize manuscripts, analyze themes, or discuss literature with you. What shall we explore today?",
    "how are you?": "I am operating at peak analytical precision! Ready to summarize manuscripts, analyze themes, or discuss literature with you. What shall we explore today?",
    "who are you": "I am the Pen2Publish AI Scholar — your dedicated literary intelligence engine powered by Groq LPU and Gemini Multimodal.",
    "who are you?": "I am the Pen2Publish AI Scholar — your dedicated literary intelligence engine powered by Groq LPU and Gemini Multimodal.",
    "what can you do": "I can summarize any book, provide grounded Q&A on your uploaded PDFs, extract key takeaways, generate academic citations, and translate passages English ↔ Urdu!",
    "what can you do?": "I can summarize any book, provide grounded Q&A on your uploaded PDFs, extract key takeaways, generate academic citations, and translate passages English ↔ Urdu!"
}

URDU_GREETINGS = {
    "hi": "السلام علیکم! میں آپ کا ادبی معاون ہوں۔ میں کتب کے خلاصے، ابواب کا تجزیہ اور تشریح پیش کر سکتا ہوں۔ آپ کس کتاب کے بارے میں بات کرنا چاہتے ہیں؟",
    "hello": "السلام علیکم! پین ٹو پبلش کے ادبی معاون میں خوش آمدید۔ آپ کسی بھی کتاب، مصنف یا موضوع کے متعلق سوال پوچھ سکتے ہیں۔",
    "kya hal hai": "الحمدللہ، میں کتابوں کے تجزئیے اور ادبی رہنمائی کے لیے تیار ہوں۔ آپ آج کس کتاب کا مطالعہ کر رہے ہیں؟",
    "kia hal hai": "الحمدللہ، میں کتابوں کے تجزئیے اور ادبی رہنمائی کے لیے تیار ہوں۔ آپ آج کس کتاب کا مطالعہ کر رہے ہیں؟",
    "assalam o alaikum": "وعلیکم السلام! فرمائیے، میں آپ کے مطالعہ اور تحقیق میں کس طرح مدد کر سکتا ہوں؟",
    "salam": "وعلیکم السلام! پین ٹو پبلش کے کتب خانے میں خوش آمدید۔ آپ کا کیا سوال ہے؟"
}


def is_casual_greeting(user_text, language="english"):
    clean = user_text.strip().lower()
    if language.lower() == "urdu":
        return URDU_GREETINGS.get(clean) or CASUAL_GREETINGS.get(clean)
    return CASUAL_GREETINGS.get(clean)


# ==============================================================================
# RAG DOCUMENT EXTRACTION & GROUNDED Q&A ENGINE
# ==============================================================================
def extract_document_content(uploaded_file):
    """
    Extracts text and page-indexed chunks from PDF, DOCX, or TXT/MD files.
    Returns: (success, full_text, chunks)
    """
    if uploaded_file is None:
        return False, "", []

    filename = getattr(uploaded_file, "name", "document.txt").lower()
    chunks = []
    full_text = ""

    try:
        if filename.endswith(".pdf"):
            import pypdf
            reader = pypdf.PdfReader(uploaded_file)
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    full_text += f"\n\n[Page {page_num}]\n" + page_text
                    chunks.append({"page": page_num, "text": page_text.strip()})

        elif filename.endswith(".docx"):
            import docx
            doc = docx.Document(uploaded_file)
            section_num = 1
            cur_section_text = []
            for p in doc.paragraphs:
                p_text = p.text.strip()
                if not p_text:
                    continue
                if p.style.name.startswith("Heading"):
                    if cur_section_text:
                        sec_str = "\n".join(cur_section_text)
                        full_text += f"\n\n[Section {section_num}]\n" + sec_str
                        chunks.append({"page": section_num, "text": sec_str})
                        section_num += 1
                        cur_section_text = [p_text]
                    else:
                        cur_section_text.append(p_text)
                else:
                    cur_section_text.append(p_text)

            if cur_section_text:
                sec_str = "\n".join(cur_section_text)
                full_text += f"\n\n[Section {section_num}]\n" + sec_str
                chunks.append({"page": section_num, "text": sec_str})

        else:
            # Plain text / markdown
            if hasattr(uploaded_file, "getvalue"):
                raw_bytes = uploaded_file.getvalue()
            else:
                raw_bytes = uploaded_file.read()
            text = raw_bytes.decode("utf-8", errors="replace")
            full_text = text
            chunks.append({"page": 1, "text": text[:3000]})

        if not full_text.strip():
            return False, "Uploaded file appears to be empty or unreadable.", []

        return True, full_text, chunks

    except Exception as e:
        return False, f"Error processing file: {str(e)}", []


def stream_document_rag_chat(user_question, doc_text, conversation_history=None, doc_name="Manuscript"):
    """
    RAG Chatbot: Grounded exclusively on uploaded document with explicit [Page X] citations.
    Routes to Gemini 3.5 Flash-Lite if doc is large (>15,000 chars) or Urdu; routes to Groq for fast chat otherwise.
    """
    doc_len = len(doc_text)
    is_urdu = bool(re.search(r'[\u0600-\u06FF]', user_question + doc_text[:500]))
    task = "rag_large_doc" if doc_len > 15000 else "chat"

    history_str = ""
    if conversation_history:
        for msg in conversation_history[-3:]:
            role = "Researcher" if msg.get("role") == "user" else "AI Scholar"
            history_str += f"{role}: {msg.get('content', '')}\n"

    # Context window: allow up to 45,000 chars (Gemini handles 1M tokens easily)
    clipped_doc = doc_text[:45000]

    prompt = f"""
    You are a rigorous research scholar analyzing the uploaded document: "{doc_name}".
    
    CRITICAL GROUNDING RULES:
    1. Answer the question based ONLY on the provided document text below.
    2. Whenever citing facts, arguments, or statistics, explicitly state the page or section citation (e.g. "[Page 3]" or "[Section 2]").
    3. If the answer is not contained in the text, state clearly: "This detail is not addressed in the provided document." Do NOT hallucinate.

    DOCUMENT TEXT EXCERPTS:
    \"\"\"{clipped_doc}\"\"\"

    Recent Conversation:
    {history_str}

    Question:
    "{user_question}"
    """

    for chunk in route_ai_stream(prompt, task=task, context_length=doc_len, is_urdu=is_urdu):
        yield chunk


# ==============================================================================
# CONVERSATIONAL BOOK CHATBOT (BILINGUAL)
# ==============================================================================
def stream_book_chatbot(book_context, user_question, conversation_history=None, language="english"):
    """
    Streams conversational assistant responses word-by-word with bilingual English/Urdu support.
    Routes English Q&A to Groq LPU (openai/gpt-oss-120b) and Urdu to Gemini 3.5 Flash-Lite.
    """
    instant_reply = is_casual_greeting(user_question, language)
    if instant_reply:
        yield instant_reply
        return

    history_str = ""
    if conversation_history:
        for msg in conversation_history[-4:]:
            role = "Reader" if msg.get("role") == "user" else "AI Assistant"
            history_str += f"{role}: {msg.get('content', '')}\n"

    is_urdu = (language.lower() == "urdu") or bool(re.search(r'[\u0600-\u06FF]', user_question))

    if is_urdu:
        context_clause = f"قارئین اس کتاب کے بارے میں پوچھ رہے ہیں: '{book_context}'." if book_context and book_context.strip() else "قارئین ایک عمومی ادبی یا کتابی سوال پوچھ رہے ہیں۔"
        lang_instruction = "IMPORTANT: You MUST reply entirely in natural, fluent, and elegant URDU (اردو) script. Do not reply in English."
    else:
        context_clause = f"The reader is inquiring about the book: '{book_context}'." if book_context and book_context.strip() else "The reader is asking a general literary or authoring question."
        lang_instruction = "Reply in crisp, articulate English with high literary accuracy."

    prompt = f"""
    You are the "Pen2Publish AI Literary Scholar" — powered by our Hybrid Multi-Model AI Router.
    {context_clause}
    {lang_instruction}

    Recent dialogue:
    {history_str}

    Reader's Question:
    "{user_question}"

    Instructions:
    1. Respond with clarity, directness, and literary authority.
    2. If inquiring about a book, provide chapter-by-chapter insights, core themes, and key takeaways.
    3. Use clean markdown formatting with bold headings and bullet points.
    """

    for chunk in route_ai_stream(prompt, task="chat", is_urdu=is_urdu):
        yield chunk


def get_book_deep_insights(book_title, query_type="summary", language="english"):
    """
    Generates fast structured literary insights for any book in English or Urdu.
    Routes to Groq for English summaries and Gemini for Urdu insights.
    """
    clean_title = book_title.strip() if book_title else "the selected book"
    is_urdu = (language.lower() == "urdu")

    if is_urdu:
        prompts = {
            "summary": f"کتاب '{clean_title}' کا جامع، پُراثر ادبی خلاصہ اردو (اردو رسم الخط) میں پیش کریں۔ اہم نکات، مرکزی پلاٹ، اور کرداروں کے بنیادی تصادم کو بیان کریں۔",
            "key_takeaways": f"کتاب '{clean_title}' سے حاصل ہونے والے 5 اہم ترین اسباق اور فکری نکات اردو میں درج کریں۔",
            "chapter_breakdown": f"کتاب '{clean_title}' کا باب وار (Chapter-by-Chapter) فکری اور ادبی تجزیہ اردو میں لکھیں۔",
            "author_context": f"کتاب '{clean_title}' کے مصنف کا سوانحی پس منظر، تاریخی دور اور ادبی اثرات اردو میں بیان کریں۔",
            "themes_symbolism": f"کتاب '{clean_title}' کی بنیادی علامت نگاری، استعارے اور گہرے فلسفیانہ موضوعات کا تجزیہ اردو میں پیش کریں۔"
        }
    else:
        prompts = {
            "summary": f"""
            Provide a concise, high-resolution literary summary for "{clean_title}":
            1. **Executive Hook & Premise** (2-3 sentences)
            2. **Major Narrative Phases** (Inciting Incident, Midpoint, Climax, Resolution)
            3. **Central Conflict & Stakes**
            4. **Target Audience & Enduring Value**
            Format with crisp Markdown and clean bullets.
            """,
            "key_takeaways": f"""
            Synthesize the Top 5 most profound key takeaways and philosophical lessons from "{clean_title}".
            Provide:
            - **Core Axiom:** (Bold sentence)
            - **Meaning in Text:** (How it manifests)
            - **Practical Modern Application:** (How the reader applies it)
            """,
            "chapter_breakdown": f"""
            Provide a structured, chapter-by-chapter (or act-by-act) narrative arc breakdown of "{clean_title}".
            Detail key turning points, character decisions, and thematic escalation.
            """,
            "author_context": f"""
            Provide historical, biographical, and literary context for the author of "{clean_title}".
            Explain the era, philosophical movements, and cultural atmosphere that inspired the work.
            """,
            "themes_symbolism": f"""
            Deconstruct the core thematic architecture, recurring motifs, and literary symbolism in "{clean_title}".
            Explain what the primary symbols represent and their psychological or philosophical resonance.
            """
        }

    prompt = prompts.get(query_type, prompts["summary"])
    success, result, meta = route_ai_completion(prompt, task="summary", is_urdu=is_urdu)
    return result if success else f"Error: {result}"


def explain_or_translate_passage(passage_text, book_context="", action="explain"):
    """
    Passage deep-dive or translation (English <-> Urdu).
    Routes Urdu translations to Gemini, English analysis to Groq.
    """
    clean_text = passage_text.strip()[:4000]
    is_urdu = (action == "translate_to_urdu")

    if action == "translate_to_urdu":
        prompt = f"""
        Translate the following passage into natural, elegant, literary URDU (اردو رسم الخط):
        \"\"\"{clean_text}\"\"\"
        Output ONLY the translated Urdu text. Maintain emotional tone and rhythm.
        """
    elif action == "translate_to_english":
        prompt = f"""
        Translate the following passage into fluent, natural literary English:
        \"\"\"{clean_text}\"\"\"
        Output ONLY the translated English text.
        """
    elif action == "summarize":
        prompt = f"""
        Provide a 2-3 sentence executive distillation of this passage from '{book_context or 'the book'}':
        \"\"\"{clean_text}\"\"\"
        """
    else:
        prompt = f"""
        Analyze this passage from '{book_context or 'the book'}':
        \"\"\"{clean_text}\"\"\"
        Explain:
        1. **Core Meaning & Subtext:** What is really happening beneath the surface?
        2. **Literary Devices / Word Choice:** Notable rhetorical or stylistic choices.
        3. **Key Insight:** The takeaway for the reader.
        Keep it concise and clear.
        """

    success, result, meta = route_ai_completion(prompt, task="chat", is_urdu=is_urdu)
    return result if success else f"Error: {result}"


# ==============================================================================
# CITATION GENERATION (ROUTED TO GROQ openai/gpt-oss-20b)
# ==============================================================================
def generate_citations(title, author="Unknown", year="2026", publisher="Digital Public Archive"):
    """
    Generates academic citations in APA 7th, MLA 9th, and IEEE format.
    Routed to Groq (openai/gpt-oss-20b) for sub-second precision, falling back to deterministic base.
    """
    clean_t = title.strip()
    clean_a = author.strip()
    clean_y = str(year).strip() or "2026"
    clean_p = publisher.strip()

    parts = clean_a.split()
    if len(parts) >= 2:
        apa_author = f"{parts[-1]}, {' '.join([p[0] + '.' for p in parts[:-1]])}"
        mla_author = f"{parts[-1]}, {' '.join(parts[:-1])}"
        ieee_author = f"{parts[0][0]}. {parts[-1]}"
    else:
        apa_author = clean_a
        mla_author = clean_a
        ieee_author = clean_a

    apa = f"{apa_author} ({clean_y}). {clean_t}. {clean_p}."
    mla = f"{mla_author}. {clean_t}. {clean_p}, {clean_y}."
    ieee = f"[1] {ieee_author}, \"{clean_t},\" {clean_p}, {clean_y}."
    quote_card = f'"{clean_t}" — {clean_a} ({clean_y}). Preserved and cataloged via Pen2Publish AI Index.'

    # Groq-powered academic citation synthesis
    prompt = f"""Format authentic academic citations (APA 7th, MLA 9th, IEEE) and a 1-sentence scholarly annotation for:
    Title: {clean_t}
    Author: {clean_a}
    Year: {clean_y}
    Output ONLY valid JSON with keys: "apa", "mla", "ieee", "annotation". Do not include Markdown code blocks."""

    ok, res, meta = route_ai_completion(prompt, task="citations", preferred_engine="groq_light")
    if ok and res:
        try:
            clean_json = re.sub(r'```json\s*|\s*```', '', res).strip()
            parsed = json.loads(clean_json)
            if parsed.get("apa"): apa = parsed["apa"]
            if parsed.get("mla"): mla = parsed["mla"]
            if parsed.get("ieee"): ieee = parsed["ieee"]
            if parsed.get("annotation"):
                quote_card = f'"{clean_t}" — {clean_a} ({clean_y}). {parsed["annotation"]}'
        except Exception:
            pass

    return {
        "apa": apa,
        "mla": mla,
        "ieee": ieee,
        "quote_card": quote_card,
        "title": clean_t,
        "author": clean_a,
        "year": clean_y,
        "badge": meta.get("model", "openai/gpt-oss-20b")
    }


def synthesize_speech_audio(text, lang="en"):
    """
    Synthesize audio using gTTS with graceful fallback.
    Returns: (bytes, error_str)
    """
    if not text or not text.strip():
        return None, "Empty text provided."

    try:
        from gtts import gTTS
        clean_text = text.strip()[:1000]
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.getvalue(), None
    except Exception as e:
        return None, str(e)
