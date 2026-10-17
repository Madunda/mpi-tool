
from __future__ import annotations

import hashlib
import hmac
import secrets

import psycopg
import streamlit as st


VALID_ROLES = {"admin", "analyst", "viewer"}


def _database_url() -> str:
    try:
        return str(st.secrets["database"]["url"])
    except Exception as error:
        raise RuntimeError(
            "Database URL is missing from Streamlit secrets."
        ) from error


def _get_connection():
    return psycopg.connect(
        _database_url(),
        connect_timeout=10,
    )


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()

    return f"pbkdf2_sha256$200000${salt}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt, digest = stored.split("$", 3)

        if algorithm != "pbkdf2_sha256":
            return False

        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(rounds),
        ).hex()

        return hmac.compare_digest(calculated, digest)

    except (ValueError, TypeError, AttributeError):
        return False


def load_users() -> dict:
    query = """
        SELECT username, password_hash, role, enabled, full_name
        FROM public.mpi_users
        ORDER BY username
    """

    with _get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return {
        username: {
            "password": password_hash,
            "role": user_role,
            "enabled": enabled,
            "name": full_name,
        }
        for username, password_hash, user_role, enabled, full_name in rows
    }


def save_users(users: dict) -> None:
    if not isinstance(users, dict) or not users:
        raise ValueError(
            "The user collection is empty or invalid. "
            "No database changes were made."
        )

    records = []

    for username, record in users.items():
        username = str(username).strip()

        if not username or not isinstance(record, dict):
            raise ValueError("Invalid username or user record.")

        password_hash = record.get("password", "")
        user_role = record.get("role", "")
        full_name = str(record.get("name") or username)
        enabled = bool(record.get("enabled", True))

        if not str(password_hash).startswith("pbkdf2_sha256$"):
            raise ValueError(
                f"Invalid password hash for user '{username}'."
            )

        if user_role not in VALID_ROLES:
            raise ValueError(f"Invalid role for user '{username}'.")

        records.append(
            (username, password_hash, user_role, enabled, full_name)
        )

    upsert_query = """
        INSERT INTO public.mpi_users
            (username, password_hash, role, enabled, full_name)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (username) DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            role = EXCLUDED.role,
            enabled = EXCLUDED.enabled,
            full_name = EXCLUDED.full_name,
            updated_at = NOW()
    """

    usernames = [record[0] for record in records]

    with _get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(upsert_query, records)

            cursor.execute(
                """
                DELETE FROM public.mpi_users
                WHERE NOT (username = ANY(%s))
                """,
                (usernames,),
            )


def authenticate(username: str, password: str) -> bool:
    username = username.strip()

    if not username or not password:
        return False

    query = """
        SELECT password_hash, enabled
        FROM public.mpi_users
        WHERE username = %s
    """

    with _get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (username,))
            record = cursor.fetchone()

    if not record:
        return False

    password_hash, enabled = record

    if not enabled:
        return False

    return _verify_password(password, password_hash)


# ==========================================================
# SIGN-IN SCREEN
# ==========================================================

_LOGIN_CSS = """
<style>
[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"],
[data-testid="stAppDeployButton"],
footer {
    display: none !important;
}

[data-testid="stMainBlockContainer"],
.block-container {
    max-width: 460px;
    padding: 9vh 1rem 2rem;
}

[data-testid="stForm"] {
    background: #fff;
    border: 1px solid #dde5ee;
    border-radius: 12px;
    padding: 2rem 2rem 1.6rem;
    box-shadow: 0 4px 18px rgba(16, 42, 67, .06);
}

[data-testid="InputInstructions"] {
    display: none !important;
}

.lg-head {
    text-align: center;
    margin-bottom: 1.4rem;
}

.lg-logos {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.lg-logos img {
    height: 84px;
    width: auto;
}

.lg-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #102a43;
    line-height: 1.3;
}

.lg-sub {
    font-size: .88rem;
    color: #667085;
    margin-top: 2px;
}

.lg-note {
    text-align: center;
    color: #667085;
    font-size: .83rem;
    margin-top: 1rem;
}
</style>
"""


def _logo(*filenames: str) -> str:
    from core.ui import _safe_image_data_uri, asset_path

    path = asset_path(*filenames)
    uri = _safe_image_data_uri(str(path)) if path else None

    return f'<img src="{uri}" alt="">' if uri else ""


def login_form() -> None:
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    header = f"""
    <div class="lg-head">
        <div class="lg-logos">
            {_logo("ngao.png", "logo.png")}
            {_logo("nbs.png", "nbs_logo.png", "logo_right.png")}
        </div>
        <div class="lg-title">NMPI Automation Tool</div>
        <div class="lg-sub">National Multidimensional Poverty Index</div>
    </div>
    """

    with st.form("login_form"):
        st.markdown(header, unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        submitted = st.form_submit_button(
            "Sign in",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            if authenticate(username, password):
                users = load_users()
                record = users[username.strip()]

                st.session_state.authenticated = True
                st.session_state.username = username.strip()
                st.session_state.user_role = record["role"]
                st.session_state.user_name = record["name"]
                st.rerun()
            else:
                st.error(
                    "Invalid username/password or the account is disabled."
                )

        except Exception:
            st.error(
                "Unable to connect to the authentication database. "
                "Please try again later or contact the system administrator."
            )

    st.markdown(
        '<div class="lg-note">'
        "Forgot your password? Contact the system administrator."
        "</div>",
        unsafe_allow_html=True,
    )


def logout() -> None:
    for key in [
        "authenticated",
        "username",
        "user_role",
        "user_name",
    ]:
        st.session_state.pop(key, None)

    st.rerun()


def require_login() -> bool:
    return bool(st.session_state.get("authenticated", False))


def role() -> str:
    return str(st.session_state.get("user_role", "")).lower()


def allowed(role_name: str, page_key: str) -> bool:
    permissions = {
        "admin": {
            "home", "load", "config", "analysis", "results",
            "export", "change", "guide", "users",
        },
        "analyst": {
            "home", "load", "config", "analysis", "results",
            "export", "change", "guide",
        },
        "viewer": {"home", "results", "guide"},
    }

    return page_key in permissions.get(role_name, set())


__all__ = [
    "load_users",
    "save_users",
    "authenticate",
    "login_form",
    "logout",
    "require_login",
    "role",
    "allowed",
    "_hash_password",
]
