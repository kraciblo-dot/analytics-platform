from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.api_key import ApiKey

class ApiKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, api_key: ApiKey) -> ApiKey:
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key

    async def get_by_org(self, organization_id: int) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())