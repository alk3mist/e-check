from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_db_url() -> str:
    return "postgresql+psycopg://scott:tiger@localhost/test"


engine = create_async_engine(get_db_url(), isolation_level="SERIALIZABLE")


def get_engine(url: str | None = None) -> AsyncEngine:
    url = url or get_db_url()
    engine = create_async_engine(url, isolation_level="SERIALIZABLE")
    return engine


def get_session_maker(url: str | None = None) -> async_sessionmaker[AsyncSession]:
    engine = get_engine(url)

    async_session = async_sessionmaker(engine)
    return async_session
