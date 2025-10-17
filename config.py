import os
from dataclasses import dataclass
from typing import Optional

try:
	from dotenv import load_dotenv  # type: ignore
	load_dotenv()
except Exception:
	# dotenv is optional; ignore if not installed
	pass


@dataclass(frozen=True)
class DatabaseConfig:
	host: str
	port: int
	user: str
	password: str
	database: str


@dataclass(frozen=True)
class FlaskConfig:
	host: str = "127.0.0.1"
	port: int = 5001
	env: str = os.getenv("FLASK_ENV", "development")
	debug: bool = os.getenv("FLASK_DEBUG", "0") in {"1", "true", "True"}


def get_database_config() -> DatabaseConfig:
	host = os.getenv("FYP_DB_HOST", "127.0.0.1")
	port_str = os.getenv("FYP_DB_PORT", "3306")
	user = os.getenv("FYP_DB_USER", "root")
	password = os.getenv("FYP_DB_PASSWORD", "")
	database = os.getenv("FYP_DB_NAME", "fyp_db")

	try:
		port = int(port_str)
	except ValueError:
		port = 3306

	return DatabaseConfig(
		host=host,
		port=port,
		user=user,
		password=password,
		database=database,
	)


def get_flask_config() -> FlaskConfig:
	host = os.getenv("FLASK_HOST", "127.0.0.1")
	port_str = os.getenv("FLASK_PORT", "5001")
	try:
		port = int(port_str)
	except ValueError:
		port = 5001
	return FlaskConfig(host=host, port=port)
