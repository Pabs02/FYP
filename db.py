from typing import Any, Iterable, Optional, Sequence
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from contextlib import contextmanager

from config import get_database_config


_db_pool: Optional[MySQLConnectionPool] = None


def init_pool(minsize: int = 1, maxsize: int = 5) -> None:
	global _db_pool
	if _db_pool is not None:
		return
	db = get_database_config()
	_db_pool = MySQLConnectionPool(
		pool_name="fyp_pool",
		pool_size=maxsize,
		host=db.host,
		port=db.port,
		user=db.user,
		password=db.password,
		database=db.database,
		raise_on_warnings=True,
	)


@contextmanager
def get_connection():
	if _db_pool is None:
		init_pool()
	assert _db_pool is not None
	conn = _db_pool.get_connection()
	try:
		yield conn
	finally:
		conn.close()


@contextmanager
def get_cursor(dictionary: bool = True):
	with get_connection() as conn:
		cursor = conn.cursor(dictionary=dictionary)
		try:
			yield cursor
		finally:
			cursor.close()


def fetch_all(sql: str, params: Optional[Sequence[Any]] = None):
	with get_cursor(dictionary=True) as cur:
		cur.execute(sql, params or [])
		return cur.fetchall()


def fetch_one(sql: str, params: Optional[Sequence[Any]] = None):
	with get_cursor(dictionary=True) as cur:
		cur.execute(sql, params or [])
		return cur.fetchone()


def execute(sql: str, params: Optional[Sequence[Any]] = None) -> int:
	with get_cursor(dictionary=True) as cur:
		cur.execute(sql, params or [])
		rowcount = cur.rowcount
		cur.connection.commit()
		return rowcount
