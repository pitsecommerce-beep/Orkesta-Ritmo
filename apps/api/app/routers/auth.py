from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
from supabase import Client

from app.db import get_supabase, get_current_user_id, require_auth

router = APIRouter()


class MagicLinkRequest(BaseModel):
    email: str


class GuestSessionResponse(BaseModel):
    token: str
    expires_at: str


class GuestEmailRequest(BaseModel):
    guest_token: str
    email: str


class MigrateGuestRequest(BaseModel):
    guest_token: str


@router.post("/magic-link")
async def send_magic_link(
    req: MagicLinkRequest,
    db: Client = Depends(get_supabase),
):
    try:
        db.auth.sign_in_with_otp({"email": req.email})
    except Exception:
        pass
    return {
        "message": "Si el correo está registrado, recibirás un enlace de acceso.",
        "status": "sent",
    }


@router.post("/guest-session", response_model=GuestSessionResponse)
async def create_guest_session(
    db: Client = Depends(get_supabase),
):
    import uuid

    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    resp = db.table("guest_sessions").insert({
        "token": token,
        "expires_at": expires_at.isoformat(),
    }).execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Error al crear sesión de invitado.")

    return GuestSessionResponse(
        token=token,
        expires_at=expires_at.isoformat(),
    )


@router.post("/guest/set-email")
async def set_guest_email(
    req: GuestEmailRequest,
    db: Client = Depends(get_supabase),
):
    resp = (
        db.table("guest_sessions")
        .update({"email": req.email})
        .eq("token", req.guest_token)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Sesión de invitado no encontrada.")

    return {"status": "ok", "message": "Correo registrado para la sesión de invitado."}


@router.post("/migrate-guest")
async def migrate_guest_session(
    req: MigrateGuestRequest,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    guest_resp = (
        db.table("guest_sessions")
        .select("*")
        .eq("token", req.guest_token)
        .is_("migrated_to_user_id", "null")
        .single()
        .execute()
    )
    if not guest_resp.data:
        raise HTTPException(status_code=404, detail="Sesión de invitado no encontrada o ya migrada.")

    now = datetime.now(timezone.utc)
    if guest_resp.data["expires_at"] < now.isoformat():
        raise HTTPException(status_code=410, detail="Sesión de invitado expirada.")

    db.table("guest_sessions").update({
        "migrated_to_user_id": user_id,
    }).eq("token", req.guest_token).execute()

    return {"status": "migrated", "message": "Sesión de invitado migrada a tu cuenta."}


@router.get("/me")
async def get_current_user(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    profile_resp = (
        db.table("user_profiles")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )

    memberships_resp = (
        db.table("memberships")
        .select("*, tenants(id, rfc, nombre, regimen)")
        .eq("user_id", user_id)
        .execute()
    )

    profile = profile_resp.data if profile_resp.data else {}

    return {
        "user_id": user_id,
        "email": profile.get("email"),
        "nombre": profile.get("nombre"),
        "memberships": memberships_resp.data or [],
    }
