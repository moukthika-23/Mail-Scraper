from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.core.config import settings
from urllib.parse import urlencode

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


@router.get("/google", summary="Initiate Google OAuth 2.0 flow")
async def auth_google():
    """Redirects the browser to Google's OAuth consent screen."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": f"openid email profile {GMAIL_SCOPE}",
        "access_type": "offline",
        "prompt": "consent",
    }
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


import httpx
from typing import Optional
from app.core.db import supabase
from app.core.security import encrypt_token

@router.get("/callback", summary="Handle OAuth callback")
async def auth_callback(code: str, state: Optional[str] = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
        
    async with httpx.AsyncClient() as client:
        # 1. Exchange code for tokens
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        })
        token_data = token_res.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data)
            
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        
        # 2. Get user info
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo", 
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_res.json()
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")

        # 3. Upsert into Supabase directly using supabase-py
        user_record = {
            "google_id": google_id,
            "email": email,
            "name": name,
            "picture": picture,
        }
        
        # Only update refresh token if we got a new one
        if refresh_token:
            user_record["refresh_token_enc"] = encrypt_token(refresh_token)

        # We assume email/google_id are unique
        response = supabase.table("users").upsert(
            user_record, on_conflict="google_id"
        ).execute()
        
        user_db_id = response.data[0]["id"]
        
        # Redirect back to the frontend dashboard, you could pass session ID or JWT here
        # For this prototype, we'll redirect back to localhost:5173/ with the db id
        return RedirectResponse(f"{settings.FRONTEND_URL}/?user_id={user_db_id}")
