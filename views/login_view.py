"""
views/login_view.py
===================
Compatibility wrapper delegating to modular `views/auth_view.py`.
"""

from views.auth_view import render_auth_page, render_author_auth, render_admin_auth


def render_login_page():
    """Delegates to the modular authentication portal."""
    render_auth_page()
