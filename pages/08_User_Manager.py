import streamlit as st
from html import escape

from core.auth import _hash_password, load_users, save_users

ROLES = ["admin", "analyst", "viewer"]

ROLE_ACCESS = {
    "admin": "Full access, including user management",
    "analyst": "Load data, configure, analyse and export",
    "viewer": "View results only",
}

st.markdown(
    """
    <style>
    .um-table { width: 100%; border-collapse: collapse; font-size: .92rem; }
    .um-table th, .um-table td { border: 0; text-align: left; padding: 10px 12px; }
    .um-table th {
        font-size: .74rem; font-weight: 600; letter-spacing: .05em; text-transform: uppercase;
        color: #667085; border-bottom: 1px solid #dde5ee;
    }
    .um-table td { border-bottom: 1px solid #eef1f5; color: #172b4d; }
    .um-table tbody tr:last-child td { border-bottom: 0; }
    .um-muted { color: #667085; font-size: .82rem; }
    .um-table td.um-on { color: #067647; font-weight: 600; }
    .um-table td.um-off { color: #b42318; font-weight: 600; }
    [data-testid="stForm"] { border: 0; padding: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("User Manager")
st.caption("Create accounts, change roles and control who can sign in.")

users = load_users()
me = st.session_state.get("username", "")


def has_enabled_admin(data: dict) -> bool:
    return any(r.get("role") == "admin" and r.get("enabled", True) for r in data.values())


def label(username: str) -> str:
    return f"{users[username].get('name', username)} (@{username})"


def done(message: str) -> None:
    st.session_state["um_flash"] = message
    st.rerun()


# ==========================================================
# 1. MANAGE ACCOUNTS
# ==========================================================

with st.container(border=True):
    st.markdown("#### Manage accounts")

    flash = st.session_state.pop("um_flash", None)
    if flash:
        st.success(flash)

    action = st.radio(
        "Action", ["Add user", "Edit user", "Delete user"],
        horizontal=True, label_visibility="collapsed", key="um_action",
    )

    # ---------------- add ----------------
    if action == "Add user":
        with st.form("um_add", clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_username = c1.text_input("Username")
            new_name = c2.text_input("Display name")
            new_password = c1.text_input("Temporary password", type="password")
            new_role = c2.selectbox("Role", ROLES, index=1, format_func=str.title)
            create = st.form_submit_button("Create user", type="primary")

        if create:
            username = new_username.strip()
            if not username or not new_password:
                st.error("Username and password are required.")
            elif any(ch.isspace() for ch in username):
                st.error("The username cannot contain spaces.")
            elif username.lower() in {u.lower() for u in users}:
                st.error("That username already exists.")
            else:
                users[username] = {
                    "password": _hash_password(new_password),
                    "role": new_role,
                    "enabled": True,
                    "name": new_name.strip() or username,
                }
                save_users(users)
                done(f"User @{username} created.")

    # ---------------- edit ----------------
    elif action == "Edit user":
        selected = st.selectbox("User", list(users), format_func=label, key="um_edit_user")
        record = users[selected]
        is_self = selected == me

        with st.form(f"um_edit_{selected}"):
            c1, c2 = st.columns(2)
            edit_name = c1.text_input("Display name", value=record.get("name", selected))
            edit_password = c1.text_input(
                "New password", type="password", placeholder="Leave blank to keep the current one"
            )
            role_now = record.get("role", "viewer")
            edit_role = c2.selectbox(
                "Role", ROLES, index=ROLES.index(role_now) if role_now in ROLES else 2,
                format_func=str.title, disabled=is_self,
            )
            edit_enabled = c2.checkbox(
                "Account enabled", value=bool(record.get("enabled", True)), disabled=is_self
            )
            save = st.form_submit_button("Save changes", type="primary")

        if is_self:
            st.caption("You cannot change your own role or disable your own account.")

        if save:
            updated = dict(record)
            updated["name"] = edit_name.strip() or selected
            if not is_self:
                updated["role"] = edit_role
                updated["enabled"] = edit_enabled
            if edit_password:
                updated["password"] = _hash_password(edit_password)

            if not has_enabled_admin({**users, selected: updated}):
                st.error("At least one enabled admin account must remain.")
            else:
                users[selected] = updated
                save_users(users)
                done(f"User @{selected} updated.")

    # ---------------- delete ----------------
    else:
        others = [u for u in users if u != me]

        if not others:
            st.info("There are no other accounts to delete.")
        else:
            target = st.selectbox("User", others, format_func=label, key="um_delete_user")
            st.warning(f"@{target} will be permanently deleted. This cannot be undone.")
            confirm = st.checkbox(f"Yes, delete @{target}", key=f"um_confirm_{target}")

            if st.button("Delete user", disabled=not confirm):
                remaining = {u: r for u, r in users.items() if u != target}
                if not has_enabled_admin(remaining):
                    st.error("At least one enabled admin account must remain.")
                else:
                    save_users(remaining)
                    done(f"User @{target} deleted.")


# ==========================================================
# 2. ALL USERS
# ==========================================================

with st.container(border=True):
    st.markdown("#### All users")
    st.caption(f"{len(users)} registered account{'s' if len(users) != 1 else ''}")

    rows = []
    for username, record in users.items():
        role_name = str(record.get("role", "viewer")).lower()
        enabled = bool(record.get("enabled", True))
        you = " (you)" if username == me else ""
        rows.append(
            "<tr>"
            f"<td><strong>{escape(str(record.get('name', username)))}</strong>{you}"
            f"<div class='um-muted'>@{escape(username)}</div></td>"
            f"<td>{escape(role_name.title())}</td>"
            f"<td class='{'um-on' if enabled else 'um-off'}'>{'Active' if enabled else 'Disabled'}</td>"
            f"<td>{escape(ROLE_ACCESS.get(role_name, ''))}</td>"
            "</tr>"
        )

    st.markdown(
        "<table class='um-table'>"
        "<thead><tr><th>User</th><th>Role</th><th>Status</th><th>Access</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>",
        unsafe_allow_html=True,
    )

    st.caption("Accounts are stored in data/users.json. Passwords are stored as salted hashes and are never shown.")