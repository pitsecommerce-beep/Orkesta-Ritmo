"""Supabase client with JWT propagation for RLS.

Every user operation uses the user's JWT so Postgres RLS policies
enforce tenant isolation. The service role key is NEVER used for
user operations.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from supabase import Client, create_client

from app.config import get_settings


def _get_supabase_anon() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_supabase(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> Client:
    """Supabase client scoped to the requesting user's JWT.

    If the request carries a valid Bearer token, the client is created
    with that token so RLS policies apply.  Without a token the anon
    client is returned (guest mode).
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=503,
            detail="Supabase no configurado.",
        )

    token: Optional[str] = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    client = create_client(settings.supabase_url, settings.supabase_anon_key)

    if token:
        client.postgrest.auth(token)

    return client


async def get_current_user_id(
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    """Extract user id from the Supabase JWT without hitting the DB.

    Returns None for guest/anonymous requests.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]

    try:
        from jose import jwt as jose_jwt

        settings = get_settings()
        payload = jose_jwt.decode(
            token,
            settings.supabase_anon_key,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        return payload.get("sub")
    except Exception:
        return None


def require_auth(
    user_id: Optional[str] = Depends(get_current_user_id),
) -> str:
    """Dependency that requires an authenticated user."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Autenticacion requerida.")
    return user_id


def guest_or_auth(
    user_id: Optional[str] = Depends(get_current_user_id),
) -> Optional[str]:
    """Returns user_id if authenticated, None for guests."""
    return user_id
