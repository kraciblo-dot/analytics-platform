from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError

from app.db.database import get_db
from app.models.tenant import User, Organization, RoleEnum
from app.schemas.user import UserCreate
from app.core import security
from app.core.security import SECRET_KEY, ALGORITHM 

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_org = Organization(name=payload.organization_name)
    db.add(new_org)
    await db.flush() 

    hashed_pw = security.get_password_hash(payload.password)
    new_user = User(
        email=payload.email,
        hashed_password=hashed_pw,
        organization_id=new_org.id,
        role=RoleEnum.OWNER  
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "id": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        "organization_id": new_user.organization_id
    }

@router.post("/login")
async def login(
    response: Response, 
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    # Search for the user by email
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = {
        "sub": user.email, 
        "org_id": user.organization_id,
        "role": user.role.value if isinstance(user.role, RoleEnum) else user.role
    }
    
    access_token = security.create_access_token(data=token_data)
    refresh_token = security.create_refresh_token(data={"sub": user.email})
    
    # Set the HTTP-Only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True, 
        max_age=7 * 24 * 60 * 60 
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token", httponly=True, secure=True, samesite="lax")
    return {"message": "Successfully logged out"}

@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User inactive or deleted")
            
        new_token_data = {
            "sub": user.email, 
            "org_id": user.organization_id,
            "role": user.role.value if isinstance(user.role, RoleEnum) else user.role
        }
        new_access_token = security.create_access_token(data=new_token_data)
        
        return {"access_token": new_access_token, "token_type": "bearer"}
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")