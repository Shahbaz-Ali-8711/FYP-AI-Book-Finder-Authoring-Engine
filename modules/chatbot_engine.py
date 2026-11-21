import os
from config.settings import GEMINI_API_KEY
from utils.helpers import call_gemini_with_fallback, stream_gemini_response

CASUAL_GREETINGS = {
    "hi": "Hello! I am your Pen2Publish AI Literary Scholar. Whether you need deep book summaries, chapter analyses, or author history, I am ready. What book or question would you like to explore?",
    "hello": "Hello! Welcome to the Reader AI Assistant. Ask me anything about any book, literary concepts, or chapter breakdowns. Which title is on your mind?",
    "hey": "Hey there! I am your AI Literary Companion. Tell me which book you're reading or researching!",
    "how are you": "I am operating at peak analytical precision! Ready to summarize manuscripts, analyze themes, or discuss literature with you. What shall we explore today?",
    "how are you?": "I am operating at peak analytical precision! Ready to summarize manuscripts, analyze themes, or discuss literature with you. What shall we explore today?",
    "who are you": "I am the Pen2Publish AI Scholar — your dedicated literary intelligence engine. I can provide complete book breakdowns, key takeaways, chapter-by-chapter summaries, and literary criticism.",
    "who are you?": "I am the Pen2Publish AI Scholar — your dedicated literary intelligence engine. I can provide complete book breakdowns, key takeaways, chapter-by-chapter summaries, and literary criticism.",
    "what can you do": "I can summarize any book, provide chapter-by-chapter breakdowns, highlight key takeaways, explain character motives, provide author biographies, and answer any literary questions!",
    "what can you do?": "I can summarize any book, provide chapter-by-chapter breakdowns, highlight key takeaways, explain character motives, provide author biographies, and answer any literary questions!"
}


def is_casual_greeting(user_text):
    """Checks if a user message is a simple casual greeting."""
    clean = user_text.strip().lower()
    return CASUAL_GREETINGS.get(clean)


def stream_book_chatbot(book_context, user_question, conversation_history=None):
    """
    Streams conversational assistant responses word-by-word.
    Handles instant casual greetings in 0.01 seconds, or streams literary insights via Gemini.
    """
    # 1. Instant response for simple casual greetings
    instant_reply = is_casual_greeting(user_question)
    if instant_reply:
        yield instant_reply
        return

    if not GEMINI_API_KEY:
        yield "⚠️ Gemini API key is missing. Please configure GEMINI_API_KEY in your .env file."
        return

    history_str = ""
    if conversation_history:
        for msg in conversation_history[-4:]:
            role = "Reader" if msg.get("role") == "user" else "AI Assistant"
            history_str += f"{role}: {msg.get('content', '')}\n"

    context_clause = f"The reader is inquiring about the book: '{book_context}'." if book_context and book_context.strip() else "The reader is asking a general literary or authoring question."

    prompt = f"""
    You are the "Pen2Publish AI Literary Scholar" — a fast, brilliant literary critic and bibliophile.
    {context_clause}

    Recent dialogue:
    {history_str}

    Reader's Question:
    "{user_question}"

    Instructions:
    1. Respond with clarity, directness, and literary authority.
    2. If inquiring about a paid/modern book, provide chapter-by-chapter insights and key takeaways so they receive complete value.
    3. Use clean markdown headings and bullet points where helpful. Keep the response brisk and engaging.
    """

    for chunk in stream_gemini_response(GEMINI_API_KEY, prompt):
        yield chunk


def get_book_deep_insights(book_title, query_type="summary"):
    """
    Generates fast structured literary insights for any book.
    """
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API Key missing! Check .env file."

    clean_title = book_title.strip() if book_title else "the selected book"

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
        Generate a structured Chapter-by-Chapter (or Act-by-Act) breakdown of "{clean_title}".
        For each major section provide:
        - **Chapter Title & Scope**
        - **Key Events & Character Choices**
        - **Core Takeaway or Turning Point**
        """,
        "author_context": f"""
        Provide an author biography and historical context for "{clean_title}":
        1. **Author Background & Major Publications**
        2. **Historical Era & Societal Climate**
        3. **Key Philosophies & Influences**
        4. **Literary Legacy**
        """,
        "themes_symbolism": f"""
        Analyze the hidden symbolism and foundational themes of "{clean_title}":
        1. **Core Themes** (Mortality, Justice, Ambition, etc.)
        2. **Symbolic Objects & Recurring Motifs**
        3. **Philosophical Questions Posed to the Reader**
        """
    }

    prompt = prompts.get(query_type, f"Provide a complete scholarly overview of '{clean_title}'.")
    success, result = call_gemini_with_fallback(GEMINI_API_KEY, prompt)
    return result if success else f"Could not generate insights: {result}"
