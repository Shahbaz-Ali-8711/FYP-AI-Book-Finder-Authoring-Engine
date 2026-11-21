PRICING_TIERS = {
    "Free": {
        "price": 0,
        "period": "forever",
        "color": "#718096",
        "features": [
            ("✅", "5 AI searches per day"),
            ("✅", "3 AI summaries per day"),
            ("✅", "Basic book scanner"),
            ("✅", "Community support"),
            ("❌", "Cover Page Generator"),
            ("❌", "Book Formatting Engine"),
            ("❌", "Priority API access"),
        ],
        "limits": {
            "daily_ai_calls": 8,
            "daily_formatting_pages": 0,
            "cover_generation": False,
            "high_res_export": False,
        },
    },
    "Standard": {
        "price": 9.99,
        "period": "month",
        "color": "#0D5C3A",  # Deep Forest Emerald
        "features": [
            ("✅", "50 AI searches per day"),
            ("✅", "Unlimited AI summaries"),
            ("✅", "Advanced book scanner"),
            ("✅", "Cover Page Generator (10/mo)"),
            ("✅", "Book Formatting (up to 20 pages)"),
            ("❌", "High-Res Cover Export"),
            ("❌", "Priority API access"),
        ],
        "limits": {
            "daily_ai_calls": 50,
            "daily_formatting_pages": 20,
            "cover_generation": True,
            "high_res_export": False,
        },
    },
    "Gold": {
        "price": 24.99,
        "period": "month",
        "color": "#E34234",  # Vermilion Featured
        "featured": True,
        "features": [
            ("✅", "200 AI searches per day"),
            ("✅", "Unlimited AI summaries"),
            ("✅", "Advanced book scanner"),
            ("✅", "Cover Page Generator (50/mo)"),
            ("✅", "Book Formatting (up to 50 pages)"),
            ("✅", "High-Res Cover Export"),
            ("❌", "Priority API access"),
        ],
        "limits": {
            "daily_ai_calls": 200,
            "daily_formatting_pages": 50,
            "cover_generation": True,
            "high_res_export": True,
        },
    },
    "Premium": {
        "price": 49.99,
        "period": "month",
        "color": "#10B981",  # Vibrant Emerald
        "features": [
            ("✅", "Unlimited AI searches"),
            ("✅", "Unlimited AI summaries"),
            ("✅", "Advanced book scanner"),
            ("✅", "Unlimited Cover Generation"),
            ("✅", "Unlimited Book Formatting"),
            ("✅", "High-Res Cover Export"),
            ("✅", "Priority API access"),
        ],
        "limits": {
            "daily_ai_calls": -1,
            "daily_formatting_pages": -1,
            "cover_generation": True,
            "high_res_export": True,
        },
    },
}


def _check_admin_bypass():
    try:
        import streamlit as st
        return st.session_state.get("admin_bypass", False)
    except Exception:
        return False


def get_user_tier():
    return "Free"


def get_tier_limits(tier_name=None):
    if _check_admin_bypass():
        return {"daily_ai_calls": -1, "daily_formatting_pages": -1, "cover_generation": True, "high_res_export": True}
    if tier_name is None:
        tier_name = get_user_tier()
    return PRICING_TIERS.get(tier_name, PRICING_TIERS["Free"])["limits"]


def check_quota(feature, usage_count=0):
    if _check_admin_bypass():
        return True, "Unlimited (Admin Bypass)"
    limits = get_tier_limits()
    if feature == "ai_call":
        max_calls = limits["daily_ai_calls"]
        if max_calls == -1:
            return True, "Unlimited"
        return usage_count < max_calls, f"{usage_count}/{max_calls}"
    elif feature == "formatting":
        max_pages = limits["daily_formatting_pages"]
        if max_pages == -1:
            return True, "Unlimited"
        if max_pages == 0:
            return False, "Not available on Free tier"
        return usage_count < max_pages, f"{usage_count}/{max_pages}"
    elif feature == "cover_gen":
        return limits["cover_generation"], "Available" if limits["cover_generation"] else "Upgrade required"
    return True, ""
