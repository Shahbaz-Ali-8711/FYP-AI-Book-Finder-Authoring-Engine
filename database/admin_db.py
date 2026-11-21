import sqlite3
import os
import json
import bcrypt

DB_PATH = os.path.join("data", "readme_app.db")


def _get_conn():
    return sqlite3.connect(DB_PATH)


def login_admin(username, password):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, is_super_admin FROM admin_users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        if result and bcrypt.checkpw(password.encode('utf-8'), result[1].encode('utf-8')):
            return True, {"id": result[0], "is_super_admin": result[2]}
        return False, "Invalid admin credentials!"
    except Exception as e:
        return False, f"Error: {e}"


def create_admin_user(username, password, is_super=False):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO admin_users (username, password, is_super_admin) VALUES (?, ?, ?)",
                       (username, hashed, 1 if is_super else 0))
        conn.commit()
        conn.close()
        return True, "Admin user created!"
    except sqlite3.IntegrityError:
        return False, "Admin username already exists!"
    except Exception as e:
        return False, f"Error: {e}"


def get_all_admin_users():
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, is_super_admin, created_at FROM admin_users ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def get_feature_settings():
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT feature_name, access_level, daily_limit, is_enabled FROM feature_settings ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [{"feature_name": r[0], "access_level": r[1], "daily_limit": r[2], "is_enabled": bool(r[3])} for r in rows]
    except Exception:
        return []


def update_feature_setting(feature_name, access_level, daily_limit, is_enabled):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE feature_settings SET access_level=?, daily_limit=?, is_enabled=?, updated_at=CURRENT_TIMESTAMP WHERE feature_name=?",
            (access_level, daily_limit, 1 if is_enabled else 0, feature_name)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_cms_content(section=None):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        if section:
            cursor.execute("SELECT key, value FROM cms_content WHERE section=?", (section,))
            rows = cursor.fetchall()
            conn.close()
            return {r[0]: r[1] for r in rows}
        else:
            cursor.execute("SELECT section, key, value FROM cms_content ORDER BY section, key")
            rows = cursor.fetchall()
            conn.close()
            return [{"section": r[0], "key": r[1], "value": r[2]} for r in rows]
    except Exception:
        return {} if section else []


def set_cms_content(section, key, value):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cms_content (section, key, value, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(section, key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
            (section, key, value)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def delete_cms_content(section, key):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cms_content WHERE section=? AND key=?", (section, key))
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_pricing_tiers():
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT tier_name, price, period, color, is_featured, features, limits, is_active FROM pricing_tiers WHERE is_active=1 ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        result = {}
        for r in rows:
            result[r[0]] = {
                "price": r[1],
                "period": r[2],
                "color": r[3],
                "featured": bool(r[4]),
                "features": json.loads(r[5]) if r[5] else [],
                "limits": json.loads(r[6]) if r[6] else {},
            }
        return result
    except Exception:
        return {}


def get_all_pricing_tiers():
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, tier_name, price, period, color, is_featured, is_active FROM pricing_tiers ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def update_pricing_tier(tier_name, price, period, color, is_featured, features_json, limits_json):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE pricing_tiers SET price=?, period=?, color=?, is_featured=?, features=?, limits=?, updated_at=CURRENT_TIMESTAMP WHERE tier_name=?",
            (price, period, color, 1 if is_featured else 0, features_json, limits_json, tier_name)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def add_pricing_tier(tier_name, price, period, color, is_featured, features_json, limits_json):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pricing_tiers (tier_name, price, period, color, is_featured, features, limits, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
            (tier_name, price, period, color, 1 if is_featured else 0, features_json, limits_json)
        )
        conn.commit()
        conn.close()
        return True, "Tier added!"
    except sqlite3.IntegrityError:
        return False, "Tier name already exists!"
    except Exception as e:
        return False, f"Error: {e}"


def delete_pricing_tier(tier_name):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE pricing_tiers SET is_active=0 WHERE tier_name=?", (tier_name,))
        conn.commit()
        conn.close()
    except Exception:
        pass


def add_booking_lead(name, email, preferred_time, project_details):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO booking_leads (name, email, preferred_time, project_details) VALUES (?, ?, ?, ?)",
            (name, email, preferred_time, project_details)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_booking_leads(status_filter="all"):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        if status_filter == "all":
            cursor.execute("SELECT id, name, email, preferred_time, project_details, status, created_at FROM booking_leads ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT id, name, email, preferred_time, project_details, status, created_at FROM booking_leads WHERE status=? ORDER BY created_at DESC", (status_filter,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def update_lead_status(lead_id, status):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE booking_leads SET status=? WHERE id=?", (status, lead_id))
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_user_stats():
    defaults = {"total_users": 0, "total_leads": 0, "pending_leads": 0, "contacted_leads": 0, "total_searches": 0, "total_admins": 0}
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        for key, query in [
            ("total_users", "SELECT COUNT(*) FROM users"),
            ("total_leads", "SELECT COUNT(*) FROM booking_leads"),
            ("pending_leads", "SELECT COUNT(*) FROM booking_leads WHERE status='pending'"),
            ("contacted_leads", "SELECT COUNT(*) FROM booking_leads WHERE status='contacted'"),
            ("total_searches", "SELECT COUNT(*) FROM search_history"),
            ("total_admins", "SELECT COUNT(*) FROM admin_users"),
        ]:
            try:
                cursor.execute(query)
                defaults[key] = cursor.fetchone()[0]
            except Exception:
                pass
        conn.close()
        return defaults
    except Exception:
        return defaults


def get_all_users():
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY id")
        except sqlite3.OperationalError:
            cursor.execute("SELECT id, username, email, NULL FROM users ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def clear_temp_files():
    try:
        import shutil
        temp_dir = os.path.join("data", "temp_captures")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
            return True
        return False
    except Exception:
        return False


def delete_user(user_id):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM search_history WHERE user_id=?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass
