import requests
import streamlit as st
from urllib.parse import quote
from utils.helpers import call_gemini_with_fallback, get_gemini_api_key


@st.cache_data(ttl=3600, show_spinner=False)
def search_free_books(query, max_results=8):
    """
    Search books across Project Gutenberg (Gutendex API), Internet Archive, and Open Library
    with strict 5-second timeouts and 1-hour Streamlit cache for sub-2s response times.
    Prioritizes direct readable sources over login/captcha gates.
    """
    if not query or not query.strip():
        return []

    results = []
    clean_q = query.strip()
    encoded_q = quote(clean_q)

    # 1. Project Gutenberg Search (Gutendex API - Direct public domain free texts)
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
                    "description": "Public domain literary work available for instant direct reading without login or paywalls.",
                    "download_count": book.get("download_count", 0)
                })
    except Exception:
        pass

    # 2. Internet Archive Open Texts (Direct public domain / open access books)
    try:
        ia_url = f"https://archive.org/advancedsearch.php?q={encoded_q}+AND+mediatype:texts&fl[]=identifier,title,creator,description,year&rows=4&output=json"
        resp_ia = requests.get(ia_url, timeout=5)
        if resp_ia.status_code == 200:
            ia_docs = resp_ia.json().get("response", {}).get("docs", [])
            existing_titles = [r["title"].lower() for r in results]
            for doc in ia_docs:
                title = doc.get("title", "Untitled")
                if title.lower() not in existing_titles:
                    identifier = doc.get("identifier", "")
                    creator = doc.get("creator", "Public Domain Author")
                    if isinstance(creator, list):
                        creator = ", ".join(creator[:2])
                    desc = doc.get("description", "Archived text available on Internet Archive.")
                    if isinstance(desc, list):
                        desc = desc[0] if desc else ""
                    read_url = f"https://archive.org/details/{identifier}"
                    cover_url = f"https://archive.org/services/img/{identifier}"

                    results.append({
                        "title": title,
                        "author": creator,
                        "source": "Internet Archive Open Texts",
                        "cover_url": cover_url,
                        "read_link": read_url,
                        "is_totally_free": True,
                        "genres": "Historical & Academic Archive",
                        "description": desc[:180] + "..." if len(desc) > 180 else desc
                    })
    except Exception:
        pass

    # 3. Open Library Metadata Search
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
                        "description": f"Published {first_year or 'Unknown'}. {'Free digital full text available.' if has_fulltext else 'Indexed in Open Library digital catalog.'}"
                    })
    except Exception:
        pass

    # 4. Fast AI Fallback if zero results
    api_key = get_gemini_api_key()
    if not results and api_key:
        try:
            prompt = f"Provide book info for '{clean_q}': Title, Author, Genre, 2-sentence synopsis."
            success, gemini_resp = call_gemini_with_fallback(api_key, prompt)
            if success and gemini_resp:
                results.append({
                    "title": clean_q.title(),
                    "author": "Identified by Gemini 3.5 Flash-Lite",
                    "source": "Pen2Publish AI Index",
                    "cover_url": None,
                    "read_link": f"https://www.google.com/search?q={encoded_q}+book",
                    "is_totally_free": False,
                    "genres": "Literature / Reference",
                    "description": gemini_resp
                })
        except Exception:
            pass

    return results
