import os
import json
import requests
from urllib.parse import quote
import config.settings as settings
from utils.helpers import call_gemini_with_fallback
from database.db_handler import (
    get_reading_goal, update_reading_progress,
    get_bookmarks, save_bookmark, delete_bookmark,
    log_author_event
)

def _get_api_key():
    return (
        getattr(settings, "GEMINI_API_KEY_CREATOR", None) or
        getattr(settings, "GEMINI_API_KEY", None) or
        os.getenv("GEMINI_API_KEY", "")
    )


# ==============================================================================
# 1. VIBE & MOOD-BASED BOOK SEARCH
# ==============================================================================
CURATED_VIBES_DB = [
    {
        "title": "Frankenstein",
        "author": "Mary Shelley",
        "vibe": "Dark gothic existential dread, stormy isolation, obsessive ambition",
        "genre": "Gothic Horror / Sci-Fi",
        "cover_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=400&q=80",
        "read_link": "https://www.gutenberg.org/ebooks/84",
        "atmosphere": "Cold Alpine glaciers, stormy laboratories, visceral grief"
    },
    {
        "title": "The Picture of Dorian Gray",
        "author": "Oscar Wilde",
        "vibe": "Decadent aestheticism, psychological corruption, hedonistic suspense",
        "genre": "Philosophical Gothic",
        "cover_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80",
        "read_link": "https://www.gutenberg.org/ebooks/174",
        "atmosphere": "Opulent Victorian salons, opium dens, sinister oil portraits"
    },
    {
        "title": "The Adventures of Sherlock Holmes",
        "author": "Arthur Conan Doyle",
        "vibe": "Foggy gaslit London mystery, razor-sharp deduction, eccentric friendship",
        "genre": "Victorian Detective Mystery",
        "cover_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=400&q=80",
        "read_link": "https://www.gutenberg.org/ebooks/1661",
        "atmosphere": "Rain-slicked cobblestones, violin music at 221B Baker St"
    },
    {
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "vibe": "Witty social banter, slow-burn romantic tension, countryside comfort",
        "genre": "Regency Romance",
        "cover_url": "https://images.unsplash.com/photo-1476275466078-4007374efbbe?auto=format&fit=crop&w=400&q=80",
        "read_link": "https://www.gutenberg.org/ebooks/1342",
        "atmosphere": "English ballroom candlelight, muddy hem walks, biting satirical letters"
    },
    {
        "title": "Dracula",
        "author": "Bram Stoker",
        "vibe": "Eerie supernatural terror, crumbling Transylvanian castles, epistolary chills",
        "genre": "Vampiric Horror",
        "cover_url": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?auto=format&fit=crop&w=400&q=80",
        "read_link": "https://www.gutenberg.org/ebooks/345",
        "atmosphere": "Howling wolves in the Carpathians, hypnotic mist, creeping shadows"
    },
    {
        "title": "The Time Machine",
        "author": "H.G. Wells",
        "vibe": "Philosophical sci-fi melancholy, distant future ruins, cosmic loneliness",
        "genre": "Classic Sci-Fi",
        "cover_url": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=400&q=80",
        "read_link": "https://www.gutenberg.org/ebooks/35",
        "atmosphere": "Overgrown decaying paradises, subterranean Morlock machinery"
    }
]


def search_by_vibe(vibe_prompt):
    """
    Analyzes emotional atmosphere in natural language and recommends fitting literary titles.
    """
    api_key = _get_api_key()
    if not api_key:
        # Fallback to local curated vibe matcher
        matches = []
        words = vibe_prompt.lower().split()
        for b in CURATED_VIBES_DB:
            score = sum(1 for w in words if w in b["vibe"].lower() or w in b["atmosphere"].lower() or w in b["genre"].lower())
            if score > 0 or len(matches) < 3:
                matches.append(b)
        return True, matches[:4]

    prompt = f"""
    You are a literary vibe curator. A reader is searching for books by describing an emotional atmosphere, feeling, or mood:
    \"{vibe_prompt}\"

    Suggest 4 books (public domain classics or widely known titles) that encapsulate this exact vibe.
    Return JSON ONLY with the exact schema:
    [
      {{
        "title": "Book Title",
        "author": "Author Name",
        "genre": "Genre",
        "vibe_match_reason": "2 sentences explaining why this matches the requested mood",
        "atmosphere_keywords": ["keyword1", "keyword2", "keyword3"],
        "recommended_pairing": "e.g., Rainstorm, herbal tea, lo-fi cello",
        "read_url": "https://www.gutenberg.org/ebooks/search/?query=Book+Title"
      }}
    ]
    Do not output markdown code blocks, just raw JSON.
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    if success:
        try:
            clean = result.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
            for item in data:
                item["read_link"] = item.get("read_url", f"https://www.gutenberg.org/ebooks/search/?query={quote(item['title'])}")
                item["cover_url"] = "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80"
            log_author_event("search", f"Vibe: {vibe_prompt[:30]}")
            return True, data
        except Exception:
            pass

    # Fallback to curated
    return True, CURATED_VIBES_DB[:4]


# ==============================================================================
# 2. AI-POWERED BOOK MATCHMAKER
# ==============================================================================
def matchmake_books(favorite_genres, favorite_authors, preferred_pacing, theme_preference):
    """
    Generates 3 highly personalized book recommendations with reading hooks.
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "⚠️ Gemini API key missing."

    prompt = f"""
    You are an elite personal literary concierge. Match the reader with EXACTLY 3 remarkable books based on these preferences:
    - Favorite Genres: {', '.join(favorite_genres) if isinstance(favorite_genres, list) else favorite_genres}
    - Favorite Authors: {favorite_authors}
    - Preferred Pacing: {preferred_pacing}
    - Key Themes / Tropes: {theme_preference}

    For each of the 3 books, output clean markdown formatted as:
    ### 🎯 Match 1: [Book Title] by [Author]
    - **Genre & Archetype:** [e.g., Cyber-Noir Thriller]
    - **The Hook:** [One captivating sentence that pulls the reader in]
    - **Why This Matches Your Taste:** [Explain specifically connecting to their genres and authors]
    - **Best Reading Setting:** [e.g., Late-night coffee shop, rainy weekend afternoon]
    - **Estimated Immersion Time:** [e.g., 4-6 hours]

    ### 🎯 Match 2: ...
    ### 🎯 Match 3: ...
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    if success:
        log_author_event("preview", "AI Matchmaker")
    return success, result


# ==============================================================================
# 3. VISUAL BOOK COVER FINDER
# ==============================================================================
def search_by_cover_description(cover_description):
    """
    Searches for books by user descriptions of visual cover art.
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "⚠️ Gemini API key missing."

    prompt = f"""
    You are a visual book investigator. A user remembers a book cover but forgotten the title.
    They described the cover art as:
    \"{cover_description}\"

    Identify the 3 most likely candidate books matching this cover aesthetic, color palette, or iconic visual motifs.
    
    Format each candidate cleanly as:
    ### 🎨 Candidate [Number]: [Book Title] by [Author]
    - **Known Editions & Cover Art:** Describe the specific edition, colors, typography, and imagery.
    - **Plot Premise:** 2 sentences summarizing the book.
    - **Visual Confidence Score:** e.g., 95% Match
    - **Direct Gutenberg / Library Search:** [Search Link](https://www.gutenberg.org/ebooks/search/?query=[EncodedTitle])
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    if success:
        log_author_event("search", "Visual Cover Search")
    return success, result


# ==============================================================================
# 4. IN-BOOK AI COMPANION ("ASK-THE-BOOK")
# ==============================================================================
def ask_the_book(book_title, author, user_query, chapter_context=""):
    """
    Contextual literary chat companion for deep inquiries, character motives, and recaps.
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "⚠️ Gemini API key missing."

    context_prompt = f"\nRelevant Chapter / Excerpt Context:\n\"\"\"{chapter_context[:4000]}\"\"\"\n" if chapter_context else ""

    prompt = f"""
    You are the In-Book AI Companion for \"{book_title}\" by {author}.
    You possess deep, scholarly knowledge of every chapter, character arc, historical context, symbolism, and philosophical subtext of this work.
    {context_prompt}
    The reader asks:
    \"{user_query}\"

    Respond as an insightful, engaging literary guide.
    - Directly answer their question with specific textual references.
    - Explain character motivations, underlying themes, or scene breakdowns.
    - Keep spoilers for future chapters shielded unless explicitly asked.
    - Tone: Welcoming, articulate, and deeply literary.
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    return success, result


# ==============================================================================
# 5. SMART CHAPTER SUMMARIZER (1-MINUTE TAKEAWAY)
# ==============================================================================
def summarize_chapter(chapter_text, book_title="Selected Book"):
    """
    Generates a 1-minute key takeaway summary for long chapters.
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "⚠️ Gemini API key missing."

    prompt = f"""
    You are a speed-reading analyst. Generate a **1-Minute Executive Takeaway** of the following chapter from \"{book_title}\".

    Chapter Text:
    \"\"\"{chapter_text[:8000]}\"\"\"

    Output format:
    ### ⏱️ 60-Second TL;DR
    [A punchy 3-sentence summary of the chapter's core progression]

    ### 🔑 Key Plot Shifts & Revelations
    • **Shift 1:** [What changed in the stakes or relationships]
    • **Shift 2:** [What action or discovery took place]
    • **Shift 3:** [The closing cliffhanger or lingering tension]

    ### 👥 Character Decisions & Motives
    • [Bullet points on key character choices]

    ### 💬 Memorable Line / Takeaway
    > "[A poignant quote or thematic sentence from this scene]"
    """
    success, result = call_gemini_with_fallback(api_key, prompt)
    return success, result


# ==============================================================================
# 6. INTERACTIVE AI TEXT-TO-SPEECH (TTS) NARRATOR HELPER
# ==============================================================================
def get_browser_tts_component(text_to_read, title="Audio Excerpt"):
    """
    Generates a high-performance HTML5 Web Speech Synthesis API audio player.
    Styled with Modern Clean White UI and Royal Blue accents.
    """
    safe_text = json.dumps(text_to_read[:2000])  # Escaped JSON string
    html = f"""
    <div style="background: #FFFFFF;
                border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 1.25rem 1.5rem;
                color: #0F172A; font-family: 'Plus Jakarta Sans', sans-serif; box-shadow: 0 8px 24px -6px rgba(15, 23, 42, 0.08);
                margin-top: 0.75rem; margin-bottom: 1.25rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.85rem;">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
                <span style="font-size: 1.4rem;">🎙️</span>
                <span style="font-weight: 700; font-size: 1rem; color: #0F172A;">AI Literary Narrator</span>
                <span style="background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE;
                             font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 9999px; font-weight: 700;">ACTIVE</span>
            </div>
            <div id="tts-status" style="font-size: 0.8rem; color: #64748B; font-weight: 600;">Ready to Narrate</div>
        </div>

        <div style="display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap;">
            <button id="tts-play-btn" onclick="startSpeech()" style="background: linear-gradient(135deg, #2563EB, #1D4ED8);
                     border: none; color: #FFFFFF; padding: 0.5rem 1.25rem; border-radius: 10px; font-weight: 700;
                     cursor: pointer; display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);">
                ▶ Play Narration
            </button>
            <button id="tts-pause-btn" onclick="pauseSpeech()" style="background: #F8FAFC;
                     border: 1px solid #CBD5E1; color: #0F172A; padding: 0.5rem 1rem;
                     border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 0.85rem;">
                ⏸ Pause
            </button>
            <button id="tts-stop-btn" onclick="stopSpeech()" style="background: #F8FAFC;
                     border: 1px solid #CBD5E1; color: #64748B; padding: 0.5rem 1rem;
                     border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 0.85rem;">
                ⏹ Stop
            </button>

            <div style="display: flex; align-items: center; gap: 0.4rem; margin-left: auto;">
                <span style="font-size: 0.78rem; color: #64748B; font-weight: 600;">Speed:</span>
                <select id="tts-rate" onchange="updateRate()" style="background: #FFFFFF; color: #0F172A;
                        border: 1.5px solid #CBD5E1; border-radius: 8px; padding: 0.35rem 0.6rem; font-size: 0.8rem;">
                    <option value="0.85">0.85x (Atmospheric)</option>
                    <option value="1.0" selected>1.0x (Natural)</option>
                    <option value="1.15">1.15x (Brisk)</option>
                    <option value="1.3">1.3x (Fast)</option>
                </select>
            </div>
        </div>

        <div style="margin-top: 0.85rem; background: #F8FAFC; border-radius: 8px; padding: 0.6rem 0.85rem;
                    font-size: 0.82rem; color: #334155; max-height: 90px; overflow-y: auto; font-style: italic; line-height: 1.5; border: 1px solid #E2E8F0;">
            \"{text_to_read[:320]}...\"
        </div>
    </div>

    <script>
        let utterance = null;
        let isSpeaking = false;
        const textContent = {safe_text};

        function startSpeech() {{
            if ('speechSynthesis' in window) {{
                if (window.speechSynthesis.paused) {{
                    window.speechSynthesis.resume();
                    document.getElementById('tts-status').innerText = 'Narrating...';
                    return;
                }}
                window.speechSynthesis.cancel();
                utterance = new SpeechSynthesisUtterance(textContent);
                const rateSelect = document.getElementById('tts-rate');
                utterance.rate = parseFloat(rateSelect.value) || 1.0;
                utterance.pitch = 1.0;

                utterance.onstart = () => {{
                    document.getElementById('tts-status').innerText = 'Narrating aloud... 🔊';
                }};
                utterance.onend = () => {{
                    document.getElementById('tts-status').innerText = 'Narration Complete ✅';
                }};
                utterance.onerror = () => {{
                    document.getElementById('tts-status').innerText = 'Audio playback ended';
                }};

                window.speechSynthesis.speak(utterance);
            }} else {{
                document.getElementById('tts-status').innerText = 'Web Speech not supported in this browser';
            }}
        }}

        function pauseSpeech() {{
            if ('speechSynthesis' in window && window.speechSynthesis.speaking) {{
                window.speechSynthesis.pause();
                document.getElementById('tts-status').innerText = 'Narration Paused ⏸';
            }}
        }}

        function stopSpeech() {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                document.getElementById('tts-status').innerText = 'Stopped ⏹';
            }}
        }}

        function updateRate() {{
            if ('speechSynthesis' in window && window.speechSynthesis.speaking) {{
                startSpeech();
            }}
        }}
    </script>
    """
    return html
