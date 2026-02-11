import os
from dataclasses import dataclass
from typing import Optional

# Reference: python-dotenv Documentation
# https://github.com/theskumar/python-dotenv
# Loads environment variables from .env file
try:
	from dotenv import load_dotenv
	load_dotenv()
except Exception:

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


@dataclass(frozen=True)
class SmtpConfig:
	host: str
	port: int
	username: Optional[str]
	password: Optional[str]
	from_email: str
	use_tls: bool = True


@dataclass(frozen=True)
class ImapConfig:
	"""IMAP configuration for receiving lecturer replies"""
	host: str
	port: int
	username: str
	password: str
	use_ssl: bool = True
	folder: str = "INBOX"


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


def get_supabase_database_url() -> Optional[str]:
	url = os.getenv("SUPABASE_DATABASE_URL")
	return url if url else None


def get_openai_api_key() -> Optional[str]:
	key = os.getenv("OPENAI_API_KEY")
	return key if key else None


def get_openai_model_name(default: str = "gpt-4o-mini") -> str:
	model = os.getenv("OPENAI_MODEL_NAME", "").strip()
	return model or default


def get_smtp_config() -> Optional[SmtpConfig]:
	host = os.getenv("SMTP_HOST", "").strip()
	if not host:
		return None
	port_str = os.getenv("SMTP_PORT", "587").strip()
	try:
		port = int(port_str)
	except ValueError:
		port = 587
	username = os.getenv("SMTP_USERNAME", "").strip() or None
	password = os.getenv("SMTP_PASSWORD", "").strip() or None
	from_email = os.getenv("SMTP_FROM_EMAIL", "").strip() or None
	if not from_email:
		# Fallback to username if it looks like an email
		from_email = username or ""
	use_tls = os.getenv("SMTP_USE_TLS", "1") in {"1", "true", "True"}
	if not from_email:
		return None
	return SmtpConfig(
		host=host,
		port=port,
		username=username,
		password=password,
		from_email=from_email,
		use_tls=use_tls,
	)


def get_imap_config() -> Optional[ImapConfig]:
	"""
	Get IMAP configuration for receiving emails.
	
	Environment variables:
	- IMAP_HOST: IMAP server (e.g., imap.gmail.com)
	- IMAP_PORT: IMAP port (default 993 for SSL)
	- IMAP_USERNAME: Email address
	- IMAP_PASSWORD: App password (for Gmail, generate at https://myaccount.google.com/apppasswords)
	- IMAP_USE_SSL: Use SSL (default true)
	- IMAP_FOLDER: Folder to check (default INBOX)
	"""
	host = os.getenv("IMAP_HOST", "").strip()
	if not host:
		return None
	
	port_str = os.getenv("IMAP_PORT", "993").strip()
	try:
		port = int(port_str)
	except ValueError:
		port = 993
	
	username = os.getenv("IMAP_USERNAME", "").strip()
	password = os.getenv("IMAP_PASSWORD", "").strip()
	
	if not username or not password:
		return None
	
	use_ssl = os.getenv("IMAP_USE_SSL", "1") in {"1", "true", "True"}
	folder = os.getenv("IMAP_FOLDER", "INBOX").strip()
	
	return ImapConfig(
		host=host,
		port=port,
		username=username,
		password=password,
		use_ssl=use_ssl,
		folder=folder,
	)
