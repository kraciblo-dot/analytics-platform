from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import SECRET_KEY, ALGORITHM
from app.db.database import get_db
from app.models.tenant import User, RoleEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Base guard for all authenticated routes (Viewers and above)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user

async def get_current_analyst(current_user: User = Depends(get_current_active_user)):
    """Guard for dashboard creation and alerts (Analyst, Admin, Owner)."""
    if current_user.role not in [RoleEnum.OWNER, RoleEnum.ADMIN, RoleEnum.ANALYST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Analyst status required."
        )
    return current_user

async def get_current_admin(current_user: User = Depends(get_current_active_user)):
    """Guard for team invites and API key management (Admin, Owner)."""
    if current_user.role not in [RoleEnum.OWNER, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Admin status required."
        )
    return current_user

async def get_current_owner(current_user: User = Depends(get_current_active_user)):
    """Guard for destructive operations and billing (Owner only)."""
    if current_user.role != RoleEnum.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Organization Owner status required."
        )
    return current_user