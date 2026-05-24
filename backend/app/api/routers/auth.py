from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.models.tenant import User, Organization
from app.schemas.user import UserCreate
from app.core import security

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Check if the user already exists
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Create the brand new Organization
    new_org = Organization(name=payload.organization_name)
    db.add(new_org)
    await db.flush() # Assigns an ID without committing the transaction yet

    # 3. Create the User and assign them as the OWNER
    hashed_pw = security.get_password_hash(payload.password)
    new_user = User(
        email=payload.email,
        hashed_password=hashed_pw,
        organization_id=new_org.id,
        role="owner"  
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
    
    # Bake the organization ID and the Role into the secure token
    access_token = security.create_access_token(
        data={
            "sub": user.email, 
            "org_id": user.organization_id,
            "role": user.role
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}

@router.post("/refresh")
async def refresh_token():
    # Placeholder for the HTTP-only refresh cookie flow
    raise HTTPException(status_code=501, detail="Refresh logic implemented via interceptor")