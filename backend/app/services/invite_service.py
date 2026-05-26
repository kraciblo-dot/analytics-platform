import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.repositories.invite_repo import InviteRepository
from app.models.invite import OrganizationInvite
from app.models.tenant import User, RoleEnum

# Secure password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class InviteService:
    def __init__(self, repo: InviteRepository, db: AsyncSession):
        self.repo = repo
        self.db = db

    async def create_invite(self, org_id: int, email: str, role: RoleEnum) -> dict:
        """Generates a secure, time-bound invite token."""
        # 32-byte secure random string for the URL
        token = secrets.token_urlsafe(32)
        
        # Strict 7-day expiration
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        invite = OrganizationInvite(
            email=email,
            token=token,
            organization_id=org_id,
            role=role,
            expires_at=expires_at
        )
        
        db_invite = await self.repo.create(invite)
        
        return {
            "id": db_invite.id,
            "email": db_invite.email,
            "role": db_invite.role,
            "expires_at": db_invite.expires_at,
            "invite_link": f"https://your-frontend.com/accept-invite?token={token}"
        }

    async def accept_invite(self, token: str, password: str) -> dict:
        """Validates the token, creates the user, and burns the invite."""
        invite = await self.repo.get_by_token(token)
        
        if not invite:
            raise HTTPException(status_code=404, detail="Invalid invite token.")
        if invite.is_accepted:
            raise HTTPException(status_code=400, detail="This invite has already been used.")
        
        # Ensure timezone-aware comparison
        if invite.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="This invite has expired.")
            
        new_user = User(
            email=invite.email,
            hashed_password=pwd_context.hash(password),
            role=invite.role,
            organization_id=invite.organization_id
        )
        self.db.add(new_user)
        
        invite.is_accepted = True
        
        await self.db.commit()
        return {"status": "success", "message": "Account created! You may now log in."}