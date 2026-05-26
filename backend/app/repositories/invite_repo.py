from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.invite import OrganizationInvite

class InviteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, invite: OrganizationInvite) -> OrganizationInvite:
        self.session.add(invite)
        await self.session.commit()
        await self.session.refresh(invite)
        return invite

    async def get_by_token(self, token: str) -> OrganizationInvite | None:
        stmt = select(OrganizationInvite).where(OrganizationInvite.token == token)
        result = await self.session.execute(stmt)
        return result.scalars().first()