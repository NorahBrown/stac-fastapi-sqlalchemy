"""
Connection pool solution code suggested by CoPilot.

Needs some work, do not just cut and paste.

These suggestions will be integrated into session.py and tested.
"""

### **Synchronous Solution**

"""database session management."""
import logging
import os
from contextlib import contextmanager
from typing import Iterator

import attr
import psycopg2
import sqlalchemy as sa
from sqlalchemy.orm import Session as SqlSession
from sqlalchemy.pool import QueuePool
from stac_fastapi.types import errors

from stac_fastapi.sqlalchemy.config import SqlalchemySettings

logger = logging.getLogger(__name__)


class FastAPISessionMaker:
    """FastAPISessionMaker."""

    def __init__(self, connection_string: str):
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,  # Number of connections in the pool per worker
            max_overflow=10,  # Additional connections allowed beyond the pool size per worker
            pool_recycle=3600,  # Recycle connections every hour (3600 seconds)
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False
        )

    @contextmanager
    def context_session(self) -> Iterator[SqlSession]:
        """Override base method to include exception handling."""
        session = self.SessionLocal()
        try:
            yield session
        except sa.exc.StatementError as e:
            if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                raise errors.ConflictError("resource already exists") from e
            elif isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                raise errors.ForeignKeyError("collection does not exist") from e
            logger.error(e, exc_info=True)
            raise errors.DatabaseError("unhandled database error")
        finally:
            session.close()


@attr.s
class Session:
    """Database session management."""

    reader_conn_string: str = attr.ib()
    writer_conn_string: str = attr.ib()

    @classmethod
    def create_from_env(cls):
        """Create from environment."""
        return cls(
            reader_conn_string=os.environ["READER_CONN_STRING"],
            writer_conn_string=os.environ["WRITER_CONN_STRING"],
        )

    @classmethod
    def create_from_settings(cls, settings: SqlalchemySettings) -> "Session":
        """Create a Session object from settings."""
        return cls(
            reader_conn_string=settings.reader_connection_string,
            writer_conn_string=settings.writer_connection_string,
        )

    def __attrs_post_init__(self):
        """Post init handler."""
        self.reader = FastAPISessionMaker(self.reader_conn_string)
        self.writer = FastAPISessionMaker(self.writer_conn_string)


### **Asynchronous Solution**


"""database session management."""
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import attr
import asyncpg
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from stac_fastapi.types import errors

from stac_fastapi.sqlalchemy.config import SqlalchemySettings

logger = logging.getLogger(__name__)


class AsyncFastAPISessionMaker:
    """Async FastAPISessionMaker."""

    def __init__(self, connection_string: str):
        self.engine = create_async_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,  # Number of connections in the pool per worker
            max_overflow=10,  # Additional connections allowed beyond the pool size per worker
            pool_recycle=3600,  # Recycle connections every hour (3600 seconds)
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    @asynccontextmanager
    async def context_session(self) -> AsyncIterator[AsyncSession]:
        """Override base method to include exception handling."""
        async with self.SessionLocal() as session:
            try:
                yield session
            except sa.exc.StatementError as e:
                if isinstance(e.orig, asyncpg.exceptions.UniqueViolation):
                    raise errors.ConflictError("resource already exists") from e
                elif isinstance(e.orig, asyncpg.exceptions.ForeignKeyViolation):
                    raise errors.ForeignKeyError("collection does not exist") from e
                logger.error(e, exc_info=True)
                raise errors.DatabaseError("unhandled database error")


@attr.s
class Session:
    """Database session management."""

    reader_conn_string: str = attr.ib()
    writer_conn_string: str = attr.ib()

    @classmethod
    def create_from_env(cls):
        """Create from environment."""
        return cls(
            reader_conn_string=os.environ["READER_CONN_STRING"],
            writer_conn_string=os.environ["WRITER_CONN_STRING"],
        )

    @classmethod
    def create_from_settings(cls, settings: SqlalchemySettings) -> "Session":
        """Create a Session object from settings."""
        return cls(
            reader_conn_string=settings.reader_connection_string,
            writer_conn_string=settings.writer_connection_string,
        )

    def __attrs_post_init__(self):
        """Post init handler."""
        self.reader: AsyncFastAPISessionMaker = AsyncFastAPISessionMaker(
            self.reader_conn_string
        )
        self.writer: AsyncFastAPISessionMaker = AsyncFastAPISessionMaker(
            self.writer_conn_string
        )
