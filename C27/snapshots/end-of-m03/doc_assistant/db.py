"""Connections to PostgreSQL: one pool, opened when the app starts and closed when it stops.

    with db.tenant("larkfield") as conn:   # one transaction for Larkfield's rows
        conn.execute(...)
    with db.admin() as conn:               # one transaction with the owner's rights (migrations,
        conn.execute(...)                  # the job queue, loading the identity data)

Every query of a shop names the shop ("tenant_id = ..."). Module 4 adds a second lock here.
"""

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout


class DatabaseUnavailable(Exception):
    """The database does not answer, or every connection is busy."""


def _configure(conn: psycopg.Connection) -> None:
    try:
        register_vector(conn)
    except psycopg.ProgrammingError:
        pass  # the vector extension is not there yet (before the first migration)
    conn.commit()


class Database:
    def __init__(self, url: str, max_size: int = 10, timeout: float = 5.0):
        self.timeout = timeout
        self.pool = ConnectionPool(url, min_size=1, max_size=max_size, timeout=timeout, open=False,
                                   kwargs={"row_factory": dict_row, "connect_timeout": 3},
                                   configure=_configure, name="doc-assistant")

    def open(self) -> None:
        self.pool.open(wait=False)

    def close(self) -> None:
        self.pool.close()

    @contextmanager
    def _transaction(self) -> Iterator[psycopg.Connection]:
        try:
            with self.pool.connection() as conn:   # commit at the end, roll back on an error
                yield conn
        except PoolTimeout as e:
            raise DatabaseUnavailable(f"no database connection within {self.timeout} seconds") from e
        except psycopg.OperationalError as e:
            raise DatabaseUnavailable("the database does not answer") from e

    @contextmanager
    def tenant(self, tenant_id: str) -> Iterator[psycopg.Connection]:
        with self._transaction() as conn:
            yield conn

    @contextmanager
    def admin(self) -> Iterator[psycopg.Connection]:
        with self._transaction() as conn:
            yield conn

    def ping(self) -> bool:
        try:
            with self.admin() as conn:
                conn.execute("SELECT 1")
            return True
        except DatabaseUnavailable:
            return False
