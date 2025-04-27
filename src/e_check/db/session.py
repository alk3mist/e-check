from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def get_db_url() -> str:
    return "postgresql+psycopg://scott:tiger@localhost/test"


engine = create_async_engine(get_db_url(), isolation_level="SERIALIZABLE")

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine)
