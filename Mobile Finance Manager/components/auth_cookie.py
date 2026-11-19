import json
import streamlit as st
import streamlit.components.v1 as components

REMEMBER_COOKIE_NAME = "wealthflow_remember_token"
REMEMBER_MAX_AGE = 30 * 24 * 3600  # 30 days in seconds


def get_persisted_token(cookies_manager=None) -> str | None:
    """Retrieve persisted session token across native Streamlit HTTP request headers and cookie manager."""
    # 1. Native frame-1 HTTP cookie from request headers (synchronous, zero delay on F5/refresh)
    if hasattr(st, "context") and hasattr(st.context, "cookies"):
        try:
            tok = st.context.cookies.get(REMEMBER_COOKIE_NAME)
            if tok and isinstance(tok, str) and len(tok.strip()) > 10:
                return tok.strip()
        except Exception:
            pass

    # 2. Encrypted / scm cookie manager fallback
    if cookies_manager is not None:
        try:
            if getattr(cookies_manager, "ready", lambda: True)():
                tok = cookies_manager.get(REMEMBER_COOKIE_NAME)
                if tok and isinstance(tok, str) and len(tok.strip()) > 10:
                    return tok.strip()
        except Exception:
            pass

    return None


def inject_save_token_script(token: str):
    """Directly persist session token into document.cookie and localStorage across parent & top frames."""
    tok_json = json.dumps(token)
    components.html(
        f"""
        <script>
        (function() {{
            const tok = {tok_json};
            const maxAge = {REMEMBER_MAX_AGE};
            const cookieStr = "{REMEMBER_COOKIE_NAME}=" + encodeURIComponent(tok) + "; path=/; max-age=" + maxAge + "; SameSite=Lax;";
            try {{ document.cookie = cookieStr; }} catch(e){{}}
            try {{ if (window.parent && window.parent.document) window.parent.document.cookie = cookieStr; }} catch(e){{}}
            try {{ if (window.top && window.top.document) window.top.document.cookie = cookieStr; }} catch(e){{}}
            try {{ window.localStorage.setItem('{REMEMBER_COOKIE_NAME}', tok); }} catch(e){{}}
            try {{ if (window.parent && window.parent.localStorage) window.parent.localStorage.setItem('{REMEMBER_COOKIE_NAME}', tok); }} catch(e){{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def inject_clear_token_script():
    """Wipe session token from document.cookie and localStorage across all frames on logout."""
    components.html(
        f"""
        <script>
        (function() {{
            const delStr = "{REMEMBER_COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax;";
            try {{ document.cookie = delStr; }} catch(e){{}}
            try {{ if (window.parent && window.parent.document) window.parent.document.cookie = delStr; }} catch(e){{}}
            try {{ if (window.top && window.top.document) window.top.document.cookie = delStr; }} catch(e){{}}
            try {{ window.localStorage.removeItem('{REMEMBER_COOKIE_NAME}'); }} catch(e){{}}
            try {{ if (window.parent && window.parent.localStorage) window.parent.localStorage.removeItem('{REMEMBER_COOKIE_NAME}'); }} catch(e){{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )
