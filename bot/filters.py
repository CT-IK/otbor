from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db import AsyncSessionLocal
from roles import Role
from models import User


class HasRoleFilter(BaseFilter):
    def __init__(self, roles: list[Role]) -> None:
        self.roles = roles

    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        async with AsyncSessionLocal() as session:  # type: AsyncSession
            result = await session.execute(select(User).where(User.tg_id == str(message.from_user.id)))
            user = result.scalar_one_or_none()
            if not user:
                return False
            return user.role in [r.value for r in self.roles]

