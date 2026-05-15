"""
auth.py
───────
Handles user authentication and role-based access control (FR7).

Roles
-----
  admin       – data analyst; full access including admin panel
  basic       – sales / marketing; view & filter only
"""

import hashlib, os
from functools import wraps

# ── In-memory user store (replace with DB in production) ──────────────────────
def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

USERS = {
    "analyst": {
        "password": _hash("analyst123"),
        "role":     "admin",
        "name":     "Data Analyst",
        "avatar":   "DA",
    },
    "sales": {
        "password": _hash("sales123"),
        "role":     "basic",
        "name":     "Sales User",
        "avatar":   "SU",
    },
    "marketing": {
        "password": _hash("marketing123"),
        "role":     "basic",
        "name":     "Marketing User",
        "avatar":   "MU",
    },
}

def authenticate(username: str, password: str):
    """Returns user dict on success, None on failure."""
    user = USERS.get(username.lower())
    if user and user["password"] == _hash(password):
        return {"username": username.lower(), **user}
    return None

def is_admin(session_user: dict) -> bool:
    return session_user is not None and session_user.get("role") == "admin"

def is_authenticated(session_user: dict) -> bool:
    return session_user is not None
