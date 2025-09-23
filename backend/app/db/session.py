from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings


async_database_url = settings.database_async_url or settings.database_url.replace(
    "+psycopg2", "+asyncpg"
).replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(async_database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

