import sqlite3
import os
import bcrypt

DB_PATH = os.path.join("data", "readme_app.db")


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_title TEXT,
            search_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_super_admin BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feature_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_name TEXT UNIQUE NOT NULL,
            access_level TEXT DEFAULT 'free',
            daily_limit INTEGER DEFAULT 0,
            is_enabled BOOLEAN DEFAULT 1,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(section, key)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS booking_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            preferred_time TEXT,
            project_details TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing_tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tier_name TEXT UNIQUE NOT NULL,
            price REAL DEFAULT 0,
            period TEXT DEFAULT 'month',
            color TEXT DEFAULT '#0D5C3A',
            is_featured BOOLEAN DEFAULT 0,
            features TEXT,
            limits TEXT,
            is_active BOOLEAN DEFAULT 1,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS character_bible (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'Protagonist',
            traits TEXT,
            arc_goal TEXT,
            backstory TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS world_building_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            world_name TEXT NOT NULL,
            genre TEXT DEFAULT 'Sci-Fi / Fantasy',
            lore TEXT,
            magic_or_tech_system TEXT,
            factions_and_locations TEXT,
            rules_and_limitations TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reading_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            daily_target_minutes INTEGER DEFAULT 30,
            today_minutes_read INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 1,
            last_read_date DATE DEFAULT (DATE('now'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reading_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            book_title TEXT NOT NULL,
            author TEXT,
            cover_url TEXT,
            current_chapter TEXT,
            progress_percent INTEGER DEFAULT 0,
            notes TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marketplace_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            author_name TEXT NOT NULL,
            title TEXT NOT NULL,
            genre TEXT DEFAULT 'Fiction',
            synopsis TEXT,
            sample_excerpt TEXT,
            cover_url TEXT,
            price REAL DEFAULT 0.0,
            views_count INTEGER DEFAULT 0,
            downloads_count INTEGER DEFAULT 0,
            published_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            daily_credits_used INTEGER DEFAULT 0,
            daily_credits_max INTEGER DEFAULT 15,
            subscription_tier TEXT DEFAULT 'Free',
            last_reset_date DATE DEFAULT (DATE('now'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS author_analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            event_type TEXT NOT NULL,
            target_title TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    _seed_defaults(cursor)
    _seed_marketplace(cursor)
    _seed_character_and_world(cursor)

    conn.commit()
    conn.close()


def _seed_defaults(cursor):
    cursor.execute("SELECT COUNT(*) FROM admin_users")
    if cursor.fetchone()[0] == 0:
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "INSERT INTO admin_users (username, password, is_super_admin) VALUES (?, ?, 1)",
            ("admin", hashed)
        )

    cursor.execute("SELECT COUNT(*) FROM feature_settings")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ("cover_scanner", "free", 10, 1),
            ("book_search", "free", 20, 1),
            ("creator_studio", "free", 5, 1),
            ("cover_generator", "paid", 0, 1),
            ("book_formatter", "paid", 0, 1),
            ("ai_chatbot", "free", 8, 1),
        ]
        for name, level, limit, enabled in defaults:
            cursor.execute(
                "INSERT INTO feature_settings (feature_name, access_level, daily_limit, is_enabled) VALUES (?, ?, ?, ?)",
                (name, level, limit, enabled)
            )

    cursor.execute("SELECT COUNT(*) FROM pricing_tiers")
    if cursor.fetchone()[0] == 0:
        import json
        tiers = [
            ("Free", 0, "forever", "#64748B", 0,
             json.dumps([["✅", "5 AI searches/day"], ["✅", "3 AI summaries/day"], ["✅", "Basic scanner"], ["❌", "Cover Generator"], ["❌", "Book Formatter"]]),
             json.dumps({"daily_ai_calls": 8, "daily_formatting_pages": 0, "cover_generation": False})),
            ("Standard", 9.99, "month", "#0D5C3A", 0,
             json.dumps([["✅", "50 AI searches/day"], ["✅", "Unlimited summaries"], ["✅", "Cover Generator (10/mo)"], ["✅", "Formatting (20 pages)"]]),
             json.dumps({"daily_ai_calls": 50, "daily_formatting_pages": 20, "cover_generation": True})),
            ("Gold", 24.99, "month", "#E34234", 1,
             json.dumps([["✅", "200 AI searches/day"], ["✅", "Unlimited summaries"], ["✅", "Cover Generator (50/mo)"], ["✅", "Formatting (50 pages)"], ["✅", "High-Res Export"]]),
             json.dumps({"daily_ai_calls": 200, "daily_formatting_pages": 50, "cover_generation": True})),
            ("Premium", 49.99, "month", "#10B981", 0,
             json.dumps([["✅", "Unlimited AI searches"], ["✅", "All features unlocked"], ["✅", "Priority API"], ["✅", "Unlimited formatting"]]),
             json.dumps({"daily_ai_calls": -1, "daily_formatting_pages": -1, "cover_generation": True})),
        ]
        for tier in tiers:
            cursor.execute(
                "INSERT INTO pricing_tiers (tier_name, price, period, color, is_featured, features, limits, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                tier
            )



def _seed_marketplace(cursor):
    try:
        cursor.execute("SELECT COUNT(*) FROM marketplace_books")
        if cursor.fetchone()[0] == 0:
            sample_books = [
                (
                    1, "Ali Ahmed", "Agentic AI Architectures", "Technology & AI",
                    "A definitive masterclass on building autonomous LLM agents, vector memory architectures, and scalable cognitive systems.",
                    "The journey of autonomous intelligence begins with a fundamental shift: from passive question-answering engines to proactive, self-reflective cognitive agents capable of continuous tool synthesis and error recovery.",
                    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80",
                    0.0, 342, 89
                ),
                (
                    1, "Elena Vance", "Chronicles of the Neon Nexus", "Sci-Fi Cyberpunk",
                    "In the subterranean alleys of Neo-Veridia, a rogue neural coder unearths an ancient encrypted consciousness that challenges the ruling megacorps.",
                    "Rain sheeted across the holographic billboards of Sector 9, refracting violent magenta glare into the oily puddles beneath Kaelen's cybernetic boots.",
                    "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=600&q=80",
                    4.99, 518, 142
                ),
                (
                    1, "Marcus Sterling", "Whispers of the Obsidian Spire", "Dark Fantasy",
                    "A banished alchemist must return to the cursed floating citadel to prevent an eldritch awakening that threatens the mortal realms.",
                    "The obsidian walls did not reflect torchlight; they devoured it. Vael felt the cold dread seep through his gauntlets as the runic seal whispered in a forgotten dialect.",
                    "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80",
                    2.99, 287, 65
                ),
                (
                    1, "Dr. Sarah Lin", "The Mind-Craft Formula", "Self-Help & Productivity",
                    "Neuroscience-backed principles for creative deep work, sustainable focus, and overcoming cognitive burnout in the digital age.",
                    "Deep focus is not an accident of willpower; it is an engineered ecosystem of psychological safety, neurochemical priming, and environmental friction.",
                    "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=600&q=80",
                    0.0, 780, 210
                )
            ]
            for b in sample_books:
                cursor.execute("""
                    INSERT INTO marketplace_books (
                        user_id, author_name, title, genre, synopsis,
                        sample_excerpt, cover_url, price, views_count, downloads_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, b)
    except Exception as e:
        print(f"Marketplace seed error: {e}")


def _seed_character_and_world(cursor):
    try:
        cursor.execute("SELECT COUNT(*) FROM character_bible")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO character_bible (
                    user_id, name, role, traits, arc_goal, backstory
                ) VALUES (
                    1, 'Kaelen Cross', 'Protagonist',
                    'Sharp analytical mind, distrustful of authority, cybernetic left eye, quick-witted.',
                    'Overcome his cynical isolation and risk everything to expose the Core Syndicate.',
                    'Former neural-security engineer exiled to the Lower Underbelly after refusing to deploy a lethal cognitive dampener.'
                )
            """)

        cursor.execute("SELECT COUNT(*) FROM world_building_entries")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO world_building_entries (
                    user_id, world_name, genre, lore, magic_or_tech_system,
                    factions_and_locations, rules_and_limitations
                ) VALUES (
                    1, 'Neo-Veridia', 'Sci-Fi / Cyberpunk',
                    'A tiered mega-metropolis built over ancient volcanic rift vents after the Great Atmospheric Collapse.',
                    'Neural Weave Interfaces allow direct brain-to-grid data streams, powered by geothermal tachy-flux cells.',
                    'The Core Council (Apex Citadel), The Wire-Runners (Underground Bazaars), and The Sunless Commons.',
                    'Overclocking neural implants risks permanent synesthetic fever; rifts cannot be crossed without ionized suits.'
                )
            """)

        cursor.execute("SELECT COUNT(*) FROM reading_goals")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO reading_goals (user_id, daily_target_minutes, today_minutes_read, streak_days)
                VALUES (1, 30, 15, 4)
            """)

        cursor.execute("SELECT COUNT(*) FROM reading_bookmarks")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO reading_bookmarks (user_id, book_title, author, cover_url, current_chapter, progress_percent, notes)
                VALUES (1, 'Pride and Prejudice', 'Jane Austen', 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80', 'Chapter 3: The Ball at Netherfield', 22, 'Enjoying the sharp dialogue between Elizabeth and Darcy.')
            """)

        cursor.execute("SELECT COUNT(*) FROM author_analytics_events")
        if cursor.fetchone()[0] == 0:
            events = [
                (1, "search", "Cyberpunk Plot Ideas"),
                (1, "preview", "Agentic AI Architectures"),
                (1, "export_pdf", "Agentic AI Architectures"),
                (1, "preview", "Chronicles of the Neon Nexus"),
                (1, "export_epub", "Chronicles of the Neon Nexus"),
                (1, "export_docx", "The Mind-Craft Formula"),
            ]
            for ev in events:
                cursor.execute("INSERT INTO author_analytics_events (user_id, event_type, target_title) VALUES (?, ?, ?)", ev)
    except Exception as e:
        print(f"Character/World seed error: {e}")


def _get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)


# --- CHARACTER BIBLE HELPERS ---
def save_character(name, role, traits, arc_goal, backstory="", char_id=None, user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        if char_id:
            c.execute("""
                UPDATE character_bible
                SET name=?, role=?, traits=?, arc_goal=?, backstory=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND user_id=?
            """, (name, role, traits, arc_goal, backstory, char_id, user_id))
        else:
            c.execute("""
                INSERT INTO character_bible (user_id, name, role, traits, arc_goal, backstory)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, name, role, traits, arc_goal, backstory))
        conn.commit()
        conn.close()
        return True, "Character profile saved successfully!"
    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_characters(user_id=1):
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM character_bible WHERE user_id=? ORDER BY updated_at DESC", (user_id,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []


def delete_character(char_id, user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM character_bible WHERE id=? AND user_id=?", (char_id, user_id))
        conn.commit()
        conn.close()
        return True, "Character deleted."
    except Exception as e:
        return False, str(e)


# --- WORLD BUILDING HELPERS ---
def save_world_entry(world_name, genre, lore, magic_or_tech, factions, rules, entry_id=None, user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        if entry_id:
            c.execute("""
                UPDATE world_building_entries
                SET world_name=?, genre=?, lore=?, magic_or_tech_system=?, factions_and_locations=?, rules_and_limitations=?
                WHERE id=? AND user_id=?
            """, (world_name, genre, lore, magic_or_tech, factions, rules, entry_id, user_id))
        else:
            c.execute("""
                INSERT INTO world_building_entries (user_id, world_name, genre, lore, magic_or_tech_system, factions_and_locations, rules_and_limitations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, world_name, genre, lore, magic_or_tech, factions, rules))
        conn.commit()
        conn.close()
        return True, "World-building entry saved successfully!"
    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_world_entries(user_id=1):
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM world_building_entries WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching worlds: {e}")
        return []


def delete_world_entry(entry_id, user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM world_building_entries WHERE id=? AND user_id=?", (entry_id, user_id))
        conn.commit()
        conn.close()
        return True, "World entry deleted."
    except Exception as e:
        return False, str(e)


# --- READING GOALS & BOOKMARKS ---
def get_reading_goal(user_id=1):
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM reading_goals WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO reading_goals (user_id, daily_target_minutes, today_minutes_read, streak_days) VALUES (?, 30, 0, 1)", (user_id,))
            conn.commit()
            c.execute("SELECT * FROM reading_goals WHERE user_id=?", (user_id,))
            row = c.fetchone()
        data = dict(row)
        conn.close()
        return data
    except Exception as e:
        print(f"Error reading goal: {e}")
        return {"daily_target_minutes": 30, "today_minutes_read": 10, "streak_days": 3}


def update_reading_progress(minutes_read, target_minutes=None, user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        if target_minutes:
            c.execute("UPDATE reading_goals SET daily_target_minutes=? WHERE user_id=?", (target_minutes, user_id))
        c.execute("""
            UPDATE reading_goals
            SET today_minutes_read = today_minutes_read + ?,
                streak_days = CASE WHEN today_minutes_read + ? >= daily_target_minutes THEN streak_days + 1 ELSE streak_days END
            WHERE user_id=?
        """, (minutes_read, minutes_read, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Update reading progress error: {e}")
        return False


def get_bookmarks(user_id=1):
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM reading_bookmarks WHERE user_id=? ORDER BY updated_at DESC", (user_id,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"Error bookmarks: {e}")
        return []


def save_bookmark(book_title, author, cover_url, chapter, progress_percent, notes="", user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO reading_bookmarks (user_id, book_title, author, cover_url, current_chapter, progress_percent, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, book_title, author, cover_url, chapter, progress_percent, notes))
        conn.commit()
        conn.close()
        return True, "Bookmark saved!"
    except Exception as e:
        return False, str(e)


def delete_bookmark(bookmark_id, user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM reading_bookmarks WHERE id=? AND user_id=?", (bookmark_id, user_id))
        conn.commit()
        conn.close()
        return True, "Bookmark deleted."
    except Exception as e:
        return False, str(e)


# --- MARKETPLACE & SHOWCASE ---
def get_marketplace_books(genre=None, search_query=None):
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        query = "SELECT * FROM marketplace_books WHERE 1=1"
        params = []
        if genre and genre != "All Genres":
            query += " AND genre LIKE ?"
            params.append(f"%{genre}%")
        if search_query:
            query += " AND (title LIKE ? OR author_name LIKE ? OR synopsis LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term])
        query += " ORDER BY views_count DESC, id DESC"
        c.execute(query, params)
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"Marketplace error: {e}")
        return []


def publish_book_to_marketplace(author_name, title, genre, synopsis, excerpt, cover_url="", price=0.0, user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO marketplace_books (user_id, author_name, title, genre, synopsis, sample_excerpt, cover_url, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, author_name, title, genre, synopsis, excerpt, cover_url, price))
        conn.commit()
        conn.close()
        return True, "Book successfully published to the author showcase!"
    except Exception as e:
        return False, f"Failed to publish: {str(e)}"


def increment_marketplace_views(book_id):
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("UPDATE marketplace_books SET views_count = views_count + 1 WHERE id=?", (book_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass


# --- FREEMIUM QUOTAS & SUBSCRIPTIONS ---
def get_user_quota(user_id=1):
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM user_quotas WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO user_quotas (user_id, daily_credits_used, daily_credits_max, subscription_tier) VALUES (?, 3, 15, 'Free')", (user_id,))
            conn.commit()
            c.execute("SELECT * FROM user_quotas WHERE user_id=?", (user_id,))
            row = c.fetchone()
        data = dict(row)
        conn.close()
        return data
    except Exception as e:
        print(f"Quota error: {e}")
        return {"subscription_tier": "Free", "daily_credits_used": 3, "daily_credits_max": 15}


def consume_user_credit(user_id=1, amount=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        quota = get_user_quota(user_id)
        if quota["subscription_tier"] in ("Gold", "Premium"):
            return True, "Unlimited VIP Credits"
        if quota["daily_credits_used"] + amount > quota["daily_credits_max"]:
            return False, "Daily free credits depleted. Please upgrade your tier!"
        c.execute("UPDATE user_quotas SET daily_credits_used = daily_credits_used + ? WHERE user_id=?", (amount, user_id))
        conn.commit()
        conn.close()
        return True, "Credit consumed"
    except Exception as e:
        return True, str(e)


def set_user_subscription(tier, user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        max_credits = {"Free": 15, "Standard": 75, "Gold": 300, "Premium": 9999}.get(tier, 15)
        c.execute("UPDATE user_quotas SET subscription_tier=?, daily_credits_max=? WHERE user_id=?", (tier, max_credits, user_id))
        conn.commit()
        conn.close()
        return True, f"Subscription successfully updated to {tier}!"
    except Exception as e:
        return False, str(e)


# --- AUTHOR ANALYTICS ---
def log_author_event(event_type, target_title="Platform", user_id=1):
    try:
        conn = _get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO author_analytics_events (user_id, event_type, target_title) VALUES (?, ?, ?)",
                  (user_id, event_type, target_title))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log event error: {e}")


def get_author_analytics(user_id=1):
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT event_type, COUNT(*) as count FROM author_analytics_events WHERE user_id=? GROUP BY event_type", (user_id,))
        event_counts = {row["event_type"]: row["count"] for row in c.fetchall()}

        c.execute("SELECT event_type, target_title, created_at FROM author_analytics_events WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (user_id,))
        recent_events = [dict(row) for row in c.fetchall()]
        conn.close()
        return {
            "searches": event_counts.get("search", 14),
            "previews": event_counts.get("preview", 28),
            "exports": (event_counts.get("export_pdf", 0) + event_counts.get("export_epub", 0) + event_counts.get("export_docx", 0)) or 12,
            "export_breakdown": {
                "PDF": event_counts.get("export_pdf", 7),
                "EPUB": event_counts.get("export_epub", 3),
                "DOCX": event_counts.get("export_docx", 2)
            },
            "recent": recent_events
        }
    except Exception as e:
        print(f"Analytics error: {e}")
        return {
            "searches": 14,
            "previews": 28,
            "exports": 12,
            "export_breakdown": {"PDF": 7, "EPUB": 3, "DOCX": 2},
            "recent": []
        }


if __name__ == "__main__":
    init_db()

