"""
Datacube customised version of fastapi_utils.FastAPISessionMaker.

Adding conection pool to the sqlalchemy engine.
Exposing copies of all module level defs called by FastAPISessionMaker.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy.orm import Session

from fastapi_utils.session import FastAPISessionMaker as _OriginalFastAPISessionMaker


class FastAPISessionMaker(_OriginalFastAPISessionMaker):
    """
    A convenience class for managing a (cached) sqlalchemy ORM engine and sessionmaker.

    Intended for use creating ORM sessions injected into endpoint functions by FastAPI.

    Hacked from fastapi_utils, only change is the engine has pool information
    """

    def get_new_engine(self) -> sa.engine.Engine:
        """
        Returns a new sqlalchemy engine using the instance's database_uri.

        Hack to hook into local get_engine with pool.
        """
        return get_engine(self.database_uri)

    def get_db(self) -> Iterator[Session]:
        """
        A generator function that yields a sqlalchemy orm session and cleans up the session once resumed after yielding.

        Can be used directly as a context-manager FastAPI dependency, or yielded from inside a separate dependency.

        Hack calling local _get_db with connection pool
        """
        yield from _get_db(self.cached_sessionmaker)


def get_engine(uri: str) -> sa.engine.Engine:
    """
    Returns a sqlalchemy engine with pool_pre_ping enabled.

    This function may be updated over time to reflect recommended engine configuration for use with FastAPI.

    Modification to the engine where a pool is created assuming EC2 VM with uvicorn and 4 workers per instance
    """
    return sa.create_engine(
        uri,
        pool_size=5,  # Number of connections in the pool per worker
        max_overflow=10,  # Additional connections allowed beyond the pool size per worker
        pool_recycle=3600,  # Recycle connections every hour (3600 seconds)
        pool_timeout=30,  # Amount of time to wait for a connection
        pool_pre_ping=True,
    )


def get_sessionmaker_for_engine(engine: sa.engine.Engine) -> sa.orm.sessionmaker:
    """
    Returns a sqlalchemy sessionmaker for the provided engine with recommended configuration settings.

    This function may be updated over time to reflect recommended sessionmaker configuration for use with FastAPI.
    """
    return sa.orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def context_session(engine: sa.engine.Engine) -> Iterator[Session]:
    """
    This contextmanager yields a managed session for the provided engine.

    Usage is similar to `FastAPISessionMaker.context_session`, except that you have to provide the engine to use.

    A new sessionmaker is created for each call, so the FastAPISessionMaker.context_session
    method may be preferable in performance-sensitive contexts.
    """
    sessionmaker = get_sessionmaker_for_engine(engine)
    yield from _get_db(sessionmaker)


def _get_db(sessionmaker: sa.orm.sessionmaker) -> Iterator[Session]:
    """
    A generator function that yields an ORM session using the provided sessionmaker, and cleans it up when resumed.
    """
    session = sessionmaker()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        raise exc
    finally:
        session.close()
