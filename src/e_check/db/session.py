import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from e_check.db.models import User


def get_db_url() -> str:
    return "postgresql+psycopg://scott:tiger@localhost/test"


engine = create_async_engine(get_db_url(), isolation_level="SERIALIZABLE")

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine)


async def main():
    async with async_session() as session:
        user = await session.scalar(
            select(User).where(User.username == "john").limit(1)
        )
        if not user:
            session.add(User(username="john", full_name="boris", password="bbbbbbbbb"))
            await session.commit()
            user = await session.scalar(select(User).limit(1))
            assert user is not None
        print(user.id, user.username, user.full_name)


if __name__ == "__main__":
    asyncio.run(main())
