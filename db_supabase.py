from typing import Optional, Any, Sequence, List, Dict

# Reference: ChatGPT (OpenAI) - SQLAlchemy Supabase Connection
# Date: 2025-10-15
# Prompt: "I'm using Supabase PostgreSQL with SQLAlchemy. Can you show me how to set up a connection 
# engine with connection pooling and health checks? I need it to work with a PostgreSQL connection 
# string from an environment variable."
# ChatGPT provided the engine initialization pattern with pool_pre_ping for connection health checking.
# Reference: SQLAlchemy Documentation - Engine Configuration
# https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Reference: ChatGPT (OpenAI) - Connection Context Manager
# Date: 2025-10-15
# Prompt: "How do I create a context manager for database connections in SQLAlchemy that automatically 
# handles connection lifecycle and ensures connections are properly closed?"
# ChatGPT provided the context manager pattern for safe connection handling.
# Reference: Python Documentation  - contextlib.contextmanager
# https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager
from contextlib import contextmanager

from config import get_supabase_database_url

_engine: Optional[Engine] = None


# Reference: ChatGPT (OpenAI) - SQLAlchemy Engine Initialization
# Date: 2025-10-15
# Prompt: "I'm using Supabase PostgreSQL with SQLAlchemy. Can you show me how to set up a connection 
# engine with connection pooling and health checks? I need it to work with a PostgreSQL connection 
# string from an environment variable."
# ChatGPT provided singleton pattern for engine initialization with pool_pre_ping for connection 
# health checking. This ensures connections are tested before use.
def init_engine() -> None:
	global _engine
	if _engine is not None:
		return
	url = get_supabase_database_url()
	if not url:
		raise RuntimeError("SUPABASE_DATABASE_URL is not configured")
	_engine = create_engine(url, pool_pre_ping=True)


# Reference: ChatGPT (OpenAI) - Connection Context Manager Pattern
# Date: 2025-10-15
# Prompt: "How do I create a context manager for database connections in SQLAlchemy that automatically 
# handles connection lifecycle and ensures connections are properly closed?"
# ChatGPT provided the context manager pattern using SQLAlchemy's connect() method with proper 
# resource cleanup.
@contextmanager
def get_conn():
	if _engine is None:
		init_engine()
	assert _engine is not None
	with _engine.connect() as conn:
		yield conn


# Reference: ChatGPT (OpenAI) - Database Query Functions with Parameter Binding
# Date: 2025-10-15
# Prompt: "Can you help me create a fetch_all function using SQLAlchemy that executes SQL queries with 
# parameter binding to prevent SQL injection? It should return results as a list of dictionaries, and 
# use SQLAlchemy's text() function for raw SQL."
# ChatGPT provided the fetch_all function with parameterized queries and dictionary result mapping.
# Reference: SQLAlchemy Documentation - Executing SQL
# https://docs.sqlalchemy.org/en/20/tutorial/data_select.html
def fetch_all(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
	with get_conn() as c:
		res = c.execute(text(sql), params or {})
		rows = [dict(r._mapping) for r in res]
		return rows


# Reference: ChatGPT (OpenAI) - Single Row Database Query Function
# Date: 2025-10-15
# Prompt: "I need a fetch_one function similar to fetch_all but it should return a single row as a 
# dictionary or None if no results. Can you show me how to do this with SQLAlchemy?"
# ChatGPT provided the fetch_one function pattern using fetchone() and dictionary mapping.
def fetch_one(sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
	with get_conn() as c:
		res = c.execute(text(sql), params or {})
		row = res.fetchone()
		return dict(row._mapping) if row else None


# Reference: ChatGPT (OpenAI) - Database Transaction Management
# Date: 2025-10-15
# Prompt: "How do I create an execute function for INSERT/UPDATE/DELETE operations in SQLAlchemy that 
# uses transactions and parameter binding? It should use begin() for automatic transaction management 
# and bindparams() for safe parameter binding."
# ChatGPT provided the execute function with transaction management using begin() and parameter binding 
# using bindparams() to prevent SQL injection.
# Reference: SQLAlchemy Documentation  - Transaction Management
# https://docs.sqlalchemy.org/en/20/core/connections.html#using-transactions
def execute(sql: str, params: Optional[Dict[str, Any]] = None) -> int:
	if _engine is None:
		init_engine()
	assert _engine is not None
	
	with _engine.begin() as conn:
		if params:
			stmt = text(sql).bindparams(**params)
			res = conn.execute(stmt)
		else:
			res = conn.execute(text(sql))
		return res.rowcount or 0

