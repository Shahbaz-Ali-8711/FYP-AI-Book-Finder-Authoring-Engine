import requests
import streamlit as st
from urllib.parse import quote
from config.settings import GEMINI_API_KEY
from utils.helpers import call_gemini_with_fallback


@st.cache_data(ttl=3600, show_spinner=False)
def search_free_books(query, max_results=8):
    """
    Search books across Project Gutenberg and Open Library with strict 5-second timeouts
    and 1-hour Streamlit cache for instant response times under 2 seconds.
    """
    if not query or not query.strip():
        return []

    results = []
    clean_q = query.strip()
    encoded_q = quote(clean_q)

    # 1. Project Gutenberg Search (strict 5-second timeout)
    try:
        gutenberg_url = f"https://gutendex.com/books/?search={encoded_q}"
        resp = requests.get(gutenberg_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            for book in data.get("results", [])[:max_results]:
                title = book.get("title", "Unknown Title")
                authors = ", ".join([a.get("name", "") for a in book.get("authors", [])]) or "Unknown Author"
                formats = book.get("formats", {})
                read_url = (
                    formats.get("text/html") or
                    formats.get("application/pdf") or
                    formats.get("text/plain; charset=utf-8") or
                    formats.get("text/plain; charset=us-ascii") or
                    f"https://www.gutenberg.org/ebooks/{book.get('id', '')}"
                )
                cover_url = formats.get("image/jpeg")
                subjects = book.get("subjects", [])
                genres = [s.split(" -- ")[0] for s in subjects[:2]] if subjects else ["Classic Literature"]

                results.append({
                    "title": title,
                    "author": authors,
                    "source": "Project Gutenberg Archive",
                    "cover_url": cover_url,
                    "read_link": read_url,
                    "is_totally_free": True,
                    "genres": ", ".join(genres),
                    "description": "Public domain masterpiece available for instant free reading and offline download.",
                    "download_count": book.get("download_count", 0)
                })
    except Exception:
        pass

    # 2. Open Library Search (strict 5-second timeout)
    try:
        ol_url = f"https://openlibrary.org/search.json?q={encoded_q}&limit={max_results}"
        resp_ol = requests.get(ol_url, timeout=5)
        if resp_ol.status_code == 200:
            data_ol = resp_ol.json()
            docs = data_ol.get("docs", [])

            existing_titles = [r["title"].lower() for r in results]
            for doc in docs[:max_results]:
                title = doc.get("title", "Untitled")
                if title.lower() not in existing_titles:
                    author_names = doc.get("author_name", [])
                    author = ", ".join(author_names[:2]) if author_names else "Unknown Author"
                    cover_i = doc.get("cover_i")
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg" if cover_i else None
                    first_year = doc.get("first_publish_year")
                    has_fulltext = doc.get("has_fulltext", False)
                    key = doc.get("key", "")
                    read_link = f"https://openlibrary.org{key}" if key else f"https://openlibrary.org/search?q={encoded_q}"

                    results.append({
                        "title": title,
                        "author": author,
                        "source": "Open Library Catalog",
                        "cover_url": cover_url,
                        "read_link": read_link,
                        "is_totally_free": bool(has_fulltext),
                        "first_publish_year": first_year,
                        "genres": ", ".join(doc.get("subject", [])[:2]) if doc.get("subject") else "General Interest",
                        "description": f"Published {first_year or 'Unknown'}. {'Free digital full text available on Open Library.' if has_fulltext else 'Book index and borrowing available via Open Library archive.'}"
                    })
    except Exception:
        pass

    # 3. Fast AI Fallback if zero results
    if not results and GEMINI_API_KEY:
        try:
            prompt = f"Provide book info for '{clean_q}': Title, Author, Genre, 2-sentence synopsis."
            success, gemini_resp = call_gemini_with_fallback(GEMINI_API_KEY, prompt)
            if success and gemini_resp:
                results.append({
                    "title": clean_q.title(),
                    "author": "Identified by Gemini AI",
                    "source": "Pen2Publish AI Index",
                    "cover_url": None,
                    "read_link": f"https://www.gutenberg.org/ebooks/search/?query={encoded_q}",
                    "is_totally_free": False,
                    "genres": "Literature & Knowledge",
                    "description": gemini_resp.strip()[:300] + "..."
                })
        except Exception:
            pass

    return results
