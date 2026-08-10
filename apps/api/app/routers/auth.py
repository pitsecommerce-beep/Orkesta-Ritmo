from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime, timedelta, timezone

router = APIRouter()


class MagicLinkRequest(BaseModel):
    email: str


class GuestSessionResponse(BaseModel):
    token: str
    expires_at: str


class MigrateGuestRequest(BaseModel):
    guest_token: str


@router.post("/magic-link")
async def send_magic_link(req: MagicLinkRequest):
    return {
        "message": "Si el correo está registrado, recibirás un enlace de acceso.",
        "status": "sent",
    }


@router.post("/guest-session", response_model=GuestSessionResponse)
async def create_guest_session():
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    return GuestSessionResponse(
        token=token,
        expires_at=expires_at.isoformat(),
    )


@router.post("/guest/set-email")
async def set_guest_email(req: MagicLinkRequest):
    return {"status": "ok", "message": "Correo registrado para la sesión de invitado."}


@router.post("/migrate-guest")
async def migrate_guest_session(req: MigrateGuestRequest):
    return {"status": "migrated", "message": "Sesión de invitado migrada a tu cuenta."}


@router.get("/me")
async def get_current_user():
    return {"message": "Endpoint requires Supabase Auth integration"}
