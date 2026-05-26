from fastapi import HTTPException
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from app.repositories.api_key_repo import ApiKeyRepository
from app.models.api_key import ApiKey
from sqlalchemy.future import select

class ApiKeyService:
    def __init__(self, repo: ApiKeyRepository):
        self.repo = repo

    def _generate_key_pair(self) -> tuple[str, str, str]:
        """Generates a raw key, a UI-friendly prefix, and a database hash."""
        # Generate a 32-byte secure random string
        raw_secret = secrets.token_urlsafe(32)
        
        # Create a prefix like "sk_live_abc12" for the UI
        prefix = f"sk_live_{raw_secret[:5]}"
        
        # The actual key the user uses
        raw_key = f"{prefix}_{raw_secret[5:]}"
        
        # The hash we store in the database
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        
        return raw_key, prefix, hashed_key

    async def create_api_key(self, org_id: int, name: str, expires_in_days: int = None) -> dict:
        raw_key, prefix, hashed_key = self._generate_key_pair()

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        new_key = ApiKey(
            organization_id=org_id,
            name=name,
            prefix=prefix,
            hashed_key=hashed_key,
            expires_at=expires_at
        )

        db_key = await self.repo.create(new_key)
        
        # We return a dictionary that matches our ApiKeyResponse schema
        return {
            "id": db_key.id,
            "name": db_key.name,
            "raw_key": raw_key, 
            "prefix": db_key.prefix,
            "created_at": db_key.created_at
        }
        
    async def list_org_keys(self, org_id: int):
        return await self.repo.get_by_org(org_id)
    
    async def revoke_api_key(self, key_id: int, org_id: int) -> bool:
        """Deletes an API key, ensuring it belongs to the user's organization."""
        stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.organization_id == org_id)
        result = await self.db.execute(stmt)
        key = result.scalars().first()
        
        if not key:
            raise HTTPException(status_code=404, detail="API Key not found or access denied.")
        
        await self.db.delete(key)
        await self.db.commit()
        return True

    async def rotate_api_key(self, key_id: int, org_id: int) -> dict:
        """Revokes the old key and generates a fresh one with the same name."""
        # 1. Verify the old key exists
        stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.organization_id == org_id)
        result = await self.db.execute(stmt)
        old_key = result.scalars().first()
        
        if not old_key:
            raise HTTPException(status_code=404, detail="API Key not found or access denied.")
            
        key_name = old_key.name
        
        # 2. Revoke the old key
        await self.db.delete(old_key)
        await self.db.commit()
        
        # 3. Generate and return the new key using your existing method!
        # (Assuming your create_api_key method accepts org_id and name)
        new_key = await self.create_api_key(org_id=org_id, name=f"{key_name} (Rotated)")
        return new_key