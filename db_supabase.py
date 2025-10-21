from typing import Optional, Any, Sequence, List, Dict
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from contextlib import contextmanager

from config import get_supabase_database_url

_engine: Optional[Engine] = None


def init_engine() -> None:
	global _engine
	if _engine is not None:
		return
	url = get_supabase_database_url()
	if not url:
		raise RuntimeError("SUPABASE_DATABASE_URL is not configured")
	_engine = create_engine(url, pool_pre_ping=True)


@contextmanager
def get_conn():
	if _engine is None:
		init_engine()
	assert _engine is not None
	with _engine.connect() as conn:
		yield conn


def fetch_all(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
	with get_conn() as c:
		res = c.execute(text(sql), params or {})
		rows = [dict(r._mapping) for r in res]
		return rows


def fetch_one(sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
	with get_conn() as c:
		res = c.execute(text(sql), params or {})
		row = res.fetchone()
		return dict(row._mapping) if row else None


def execute(sql: str, params: Optional[Dict[str, Any]] = None) -> int:
	with get_conn() as c:
		res = c.execute(text(sql), params or {})
		c.commit()
		return res.rowcount or 0

