# Reference: Flask Documentation - Quickstart
# https://flask.palletsprojects.com/en/3.0.x/quickstart/
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session

# Reference: Flask-Login Documentation - Managing User Sessions
# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Reference: Werkzeug Documentation - Password Hashing
# https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from io import BytesIO
from email.message import EmailMessage
import smtplib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta, time, timezone

from config import (
	get_flask_config,
	get_supabase_database_url,
	get_openai_api_key,
	get_openai_model_name,
	get_smtp_config,
)
from db_supabase import fetch_all as sb_fetch_all, fetch_one as sb_fetch_one, execute as sb_execute  # type: ignore
from services.chatgpt_client import ChatGPTTaskBreakdownService, ChatGPTClientError, AssignmentReviewResponse
from services.analytics import upcoming_tasks_with_priority, assess_progress, normalise_due_datetime
SUPABASE_URL = get_supabase_database_url()


# Reference: Flask Documentation - Application Setup
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#a-minimal-application
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "your-secret-key-change-this-in-production"
app.config["OPENAI_API_KEY"] = get_openai_api_key()
app.config["OPENAI_MODEL_NAME"] = get_openai_model_name()

# Reference: Flask-Login Documentation - Initializing Extension
# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.init_app
# Setup follows Flask-Login quickstart guide
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

_chatgpt_service: Optional[ChatGPTTaskBreakdownService] = None
_AI_ALLOWED_SUFFIXES = {".txt", ".md", ".markdown", ".docx", ".pdf"}
_AI_MAX_UPLOAD_BYTES = 4 * 1024 * 1024


def get_chatgpt_service() -> ChatGPTTaskBreakdownService:
	"""Return a singleton ChatGPTTaskBreakdownService configured from Flask settings."""
	global _chatgpt_service
	if _chatgpt_service is not None:
		return _chatgpt_service
	api_key = app.config.get("OPENAI_API_KEY")
	if not api_key:
		raise ChatGPTClientError("OPENAI_API_KEY is not configured.")
	model_name = app.config.get("OPENAI_MODEL_NAME")


	_chatgpt_service = ChatGPTTaskBreakdownService(api_key=api_key, model_name=model_name)
	return _chatgpt_service


# Reference: Flask-Login Documentation - User Class Implementation
# https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin
# Used UserMixin pattern from Flask-Login docs. Adapted to work with our database structure.
class User(UserMixin):
	"""User model for authentication"""
	def __init__(
		self,
		id: int,
		name: str,
		email: str,
		student_number: Optional[str] = None,
		canvas_api_token: Optional[str] = None,
		email_notifications_enabled: bool = True,
		email_daily_summary_enabled: bool = True,
		last_daily_summary_sent_at: Optional[datetime] = None,
	):
		self.id = id
		self.name = name
		self.email = email
		self.student_number = student_number
		self.canvas_api_token = canvas_api_token
		self.email_notifications_enabled = email_notifications_enabled
		self.email_daily_summary_enabled = email_daily_summary_enabled
		self.last_daily_summary_sent_at = last_daily_summary_sent_at
	
	@staticmethod
	def get(user_id: int) -> Optional['User']:
		"""Get user by ID"""
		user_data = sb_fetch_one(
			"""
			SELECT id, name, email, student_number, canvas_api_token,
			       email_notifications_enabled, email_daily_summary_enabled, last_daily_summary_sent_at
			FROM students
			WHERE id = :id
			""",
			{"id": user_id}
		)
		if user_data:
			return User(
				id=user_data['id'],
				name=user_data['name'],
				email=user_data['email'],
				student_number=user_data.get('student_number'),
				canvas_api_token=user_data.get('canvas_api_token'),
				email_notifications_enabled=bool(user_data.get('email_notifications_enabled', True)),
				email_daily_summary_enabled=bool(user_data.get('email_daily_summary_enabled', True)),
				last_daily_summary_sent_at=user_data.get('last_daily_summary_sent_at'),
			)
		return None
	
	@staticmethod
	def get_by_email(email: str) -> Optional['User']:
		"""Get user by email"""
		user_data = sb_fetch_one(
			"""
			SELECT id, name, email, student_number, canvas_api_token,
			       email_notifications_enabled, email_daily_summary_enabled, last_daily_summary_sent_at
			FROM students
			WHERE email = :email
			""",
			{"email": email}
		)
		if user_data:
			return User(
				id=user_data['id'],
				name=user_data['name'],
				email=user_data['email'],
				student_number=user_data.get('student_number'),
				canvas_api_token=user_data.get('canvas_api_token'),
				email_notifications_enabled=bool(user_data.get('email_notifications_enabled', True)),
				email_daily_summary_enabled=bool(user_data.get('email_daily_summary_enabled', True)),
				last_daily_summary_sent_at=user_data.get('last_daily_summary_sent_at'),
			)
		return None


# Reference: Flask-Login Documentation - User Loader Callback
# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
# Required callback function for Flask-Login to load users from session
@login_manager.user_loader
def load_user(user_id):
	"""Load user by ID for Flask-Login"""
	return User.get(int(user_id))


# Reference: Flask Documentation - Custom Template Filters
# https://flask.palletsprojects.com/en/3.0.x/templating/#registering-filters
# Custom filter for Irish date format (DD/MM/YYYY)
@app.template_filter('irish_date')
def format_irish_date(value):
	"""Format date to DD/MM/YYYY"""
	if value is None:
		return ""
	
	# Reference: ChatGPT (OpenAI) - ISO Date Parsing with Timezone Handling
	# Date: 2025-10-12
	# Prompt: "I'm getting ISO date strings from a database that sometimes have 'Z' for UTC timezone. 
	# Python's fromisoformat() doesn't accept 'Z', it needs '+00:00'. Can you show me how to safely 
	# parse these ISO strings and handle the timezone conversion?"
	# ChatGPT provided the pattern for replacing 'Z' with '+00:00' before parsing ISO date strings.
	if isinstance(value, str):
		try:
			from datetime import datetime
			value = datetime.fromisoformat(value.replace('Z', '+00:00'))
		except:
			return value
	
	try:
		return value.strftime('%d/%m/%Y')
	except:
		return str(value)


@app.template_filter('irish_datetime')
def format_irish_datetime(value):
	"""Format datetime to DD/MM/YYYY HH:MM"""
	if value is None:
		return ""
	
	# Reference: ChatGPT (OpenAI) - ISO Date Parsing with Timezone Handling
	# Date: 2025-10-12
	# Prompt: "I'm getting ISO date strings from a database that sometimes have 'Z' for UTC timezone. 
	# Python's fromisoformat() doesn't accept 'Z', it needs '+00:00'. Can you show me how to safely 
	# parse these ISO strings and handle the timezone conversion?"
	# ChatGPT provided the pattern for replacing 'Z' with '+00:00' before parsing ISO date strings.
	if isinstance(value, str):
		try:
			from datetime import datetime
			value = datetime.fromisoformat(value.replace('Z', '+00:00'))
		except:
			return value
	
	try:
		return value.strftime('%d/%m/%Y %H:%M')
	except:
		return str(value)


def test_database_connection():
	"""Check database connection on startup"""
	print("\n" + "="*70)
	print("🚀 STUDENT TASK MANAGEMENT SYSTEM")
	print("="*70)
	
	if SUPABASE_URL:
		try:
			from urllib.parse import urlparse
			parsed = urlparse(SUPABASE_URL)
			safe_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}/{parsed.path.strip('/')}"
			print(f"📊 Database: Supabase PostgreSQL")
			print(f"🌍 Host: {parsed.hostname}")
			print(f"🔌 Port: {parsed.port}")
		except:
			print(f"📊 Database: Supabase PostgreSQL (configured)")
		
		try:
			result = sb_fetch_one("SELECT version(), current_database(), current_user")
			print(f"✅ Database Connection: SUCCESS")
			print(f"   └─ Database: {result['current_database']}")
			print(f"   └─ User: {result['current_user']}")
			
			tables = sb_fetch_all("""
				SELECT table_name 
				FROM information_schema.tables 
				WHERE table_schema = 'public' 
				AND table_type = 'BASE TABLE'
				ORDER BY table_name
			""")
			print(f"✅ Tables Found: {len(tables)}")
			for table in tables:
				count_result = sb_fetch_one(f"SELECT COUNT(*) as count FROM {table['table_name']}")
				count = count_result['count'] if count_result else 0
				print(f"   └─ {table['table_name']}: {count} records")
			
			print(f"✅ Frontend: Flask Templates Ready")
			print(f"✅ Backend: Supabase Connected")
			print("="*70 + "\n")
			return True
			
		except Exception as e:
			print(f"❌ Database Connection: FAILED")
			print(f"   └─ Error: {str(e)}")
			print("="*70 + "\n")
			return False
	else:
		print(f"❌ Database URL: NOT CONFIGURED")
		print("="*70 + "\n")
		return False


@app.route("/login", methods=["GET", "POST"])
def login():
	"""User login page and handler"""
	if current_user.is_authenticated:
		return redirect(url_for("index"))
	
	if request.method == "POST":
		email = request.form.get("email", "").strip().lower()
		password = request.form.get("password", "")
		
		if not email or not password:
			flash("Please provide both email and password", "error")
			return render_template("login.html")
		
		user_data = sb_fetch_one(
			"SELECT id, name, email, student_number, password_hash, canvas_api_token FROM students WHERE email = :email",
			{"email": email}
		)
		
		if not user_data:
			flash("Invalid email or password", "error")
			return render_template("login.html")
		
		if not user_data.get('password_hash'):
			flash("Account not activated. Please register first.", "error")
			return render_template("login.html")
		
		# Reference: Werkzeug Documentation - Password Verification
		# https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.check_password_hash
		# Verifies password against stored hash
		if not check_password_hash(user_data['password_hash'], password):
			flash("Invalid email or password", "error")
			return render_template("login.html")
		
		# Create user object and log in
		user = User(
			id=user_data['id'],
			name=user_data['name'],
			email=user_data['email'],
			student_number=user_data.get('student_number'),
			canvas_api_token=user_data.get('canvas_api_token')
		)
		# Reference: Flask-Login Documentation - Logging Users In
		# https://flask-login.readthedocs.io/en/latest/#flask_login.login_user
		# Creates user session
		login_user(user, remember=True)
		
		sb_execute(
			"UPDATE students SET last_login = NOW() WHERE id = :id",
			{"id": user.id}
		)
		
		flash(f"Welcome back, {user.name}!", "success")
		
		next_page = request.args.get('next')
		return redirect(next_page) if next_page else redirect(url_for('index'))
	
	return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
	"""User registration page and handler"""
	if current_user.is_authenticated:
		return redirect(url_for("index"))
	
	if request.method == "POST":
		name = request.form.get("name", "").strip()
		email = request.form.get("email", "").strip().lower()
		password = request.form.get("password", "")
		password_confirm = request.form.get("password_confirm", "")
		student_number = request.form.get("student_number", "").strip() or None
		canvas_api_token = request.form.get("canvas_api_token", "").strip()
		
		if not name or not email or not password:
			flash("All fields are required", "error")
			return render_template("register.html")
		
		if len(password) < 6:
			flash("Password must be at least 6 characters long", "error")
			return render_template("register.html")
		
		if password != password_confirm:
			flash("Passwords do not match", "error")
			return render_template("register.html")
		
		existing = sb_fetch_one("SELECT id FROM students WHERE email = :email", {"email": email})
		if existing:
			flash("Email already registered. Please login instead.", "error")
			return redirect(url_for("login"))
		
		# Reference: Werkzeug Documentation - Password Hashing
		# https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.generate_password_hash
		# Hashes password before storing in database
		password_hash = generate_password_hash(password)
		
		try:
			sb_execute(
				"""INSERT INTO students (name, email, student_number, password_hash, canvas_api_token, created_at) 
				   VALUES (:name, :email, :student_number, :password_hash, :canvas_api_token, NOW())""",
				{
					"name": name,
					"email": email,
					"student_number": student_number,
					"password_hash": password_hash,
					"canvas_api_token": canvas_api_token if canvas_api_token else None
				}
			)
			
			flash("Registration successful! Please login.", "success")
			return redirect(url_for("login"))
			
		except Exception as e:
			flash(f"Registration failed: {str(e)}", "error")
			return render_template("register.html")
	
	return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
	"""Log out current user"""
	logout_user()
	flash("You have been logged out successfully.", "success")
	return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
	"""User profile page"""
	return render_template("profile.html")


@app.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
	"""Update user profile (Canvas token)"""
	canvas_api_token = request.form.get("canvas_api_token", "").strip()
	student_number = request.form.get("student_number", "").strip() or None
	
	try:
		sb_execute(
			"UPDATE students SET canvas_api_token = :canvas_api_token, student_number = :student_number WHERE id = :id",
			{
				"canvas_api_token": canvas_api_token if canvas_api_token else None,
				"student_number": student_number,
				"id": current_user.id
			}
		)
		
		current_user.canvas_api_token = canvas_api_token if canvas_api_token else None
		current_user.student_number = student_number
		
		if canvas_api_token:
			flash("✅ Canvas API token updated successfully!", "success")
		else:
			flash("Canvas API token removed.", "success")
		
	except Exception as e:
		flash(f"Error updating profile: {str(e)}", "error")
	
	return redirect(url_for("profile"))


@app.route("/update-email-preferences", methods=["POST"])
@login_required
def update_email_preferences():
	email_notifications_enabled = request.form.get("email_notifications_enabled") == "1"
	email_daily_summary_enabled = request.form.get("email_daily_summary_enabled") == "1"
	try:
		sb_execute(
			"""
			UPDATE students
			SET email_notifications_enabled = :email_notifications_enabled,
			    email_daily_summary_enabled = :email_daily_summary_enabled
			WHERE id = :id
			""",
			{
				"email_notifications_enabled": email_notifications_enabled,
				"email_daily_summary_enabled": email_daily_summary_enabled,
				"id": current_user.id,
			}
		)
		current_user.email_notifications_enabled = email_notifications_enabled
		current_user.email_daily_summary_enabled = email_daily_summary_enabled
		flash("Email preferences updated.", "success")
	except Exception as e:
		flash(f"Error updating email preferences: {str(e)}", "error")
	return redirect(url_for("profile"))


@app.route("/email/test", methods=["POST"])
@login_required
def send_test_email():
	error = _send_reminder_email(
		to_email=current_user.email,
		subject="Test Email - Student Planner",
		body="This is a test email from your Student Planner notifications."
	)
	if error:
		flash(f"Failed to send test email: {error}", "error")
	else:
		flash("Test email sent successfully.", "success")
	return redirect(url_for("profile"))


@app.route("/email/daily-summary", methods=["POST"])
@login_required
def send_daily_summary():
	body = _build_daily_summary_email(current_user.id)
	if not body:
		flash("No upcoming tasks to include in the summary.", "warning")
		return redirect(url_for("profile"))
	error = _send_reminder_email(
		to_email=current_user.email,
		subject="Your daily study summary",
		body=body
	)
	if error:
		flash(f"Failed to send daily summary: {error}", "error")
	else:
		flash("Daily summary sent.", "success")
	return redirect(url_for("profile"))



# MAIN APPLICATION ROUTES


@app.route("/")
@login_required
def index():
	_generate_task_reminders(current_user.id)
	# Send daily summary once per day (if enabled)
	# Reference: ChatGPT (OpenAI) - Daily Summary Email Trigger Pattern
	# Date: 2026-01-22
	# Prompt: "I need to send a daily summary email once per day when the user loads the dashboard.
	# Can you help me design a last-sent check and update status flags?"
	# ChatGPT provided the trigger pattern and last-sent guard.
	try:
		student = sb_fetch_one(
			"""
			SELECT email, email_daily_summary_enabled, last_daily_summary_sent_at
			FROM students
			WHERE id = :student_id
			""",
			{"student_id": current_user.id}
		)
		if student and student.get("email") and student.get("email_daily_summary_enabled", True):
			last_sent = student.get("last_daily_summary_sent_at")
			should_send = True
			if last_sent:
				try:
					last_date = last_sent.date() if hasattr(last_sent, "date") else None
					should_send = last_date != datetime.now(timezone.utc).date()
				except Exception:
					should_send = True
			if should_send:
				body = _build_daily_summary_email(current_user.id)
				if body:
					error = _send_reminder_email(
						to_email=student.get("email"),
						subject="Your daily study summary",
						body=body
					)
					status = "sent" if error is None else "failed"
					sb_execute(
						"""
						UPDATE students
						SET last_daily_summary_sent_at = NOW(),
						    daily_summary_status = :status,
						    daily_summary_error = :error
						WHERE id = :student_id
						""",
						{
							"status": status,
							"error": error,
							"student_id": current_user.id
						}
					)
	except Exception as exc:
		print(f"[daily-summary] failed to send summary user={current_user.id} error={exc}")
	try:
		rows = sb_fetch_all(
			"""
			SELECT t.id, t.title, t.status, t.due_date, t.due_at, t.completed_at,
			       t.weight_percentage, t.canvas_score, t.canvas_possible,
			       m.code AS module_code
			FROM tasks t
			JOIN modules m ON m.id = t.module_id
			WHERE t.student_id = :student_id
			""",
			{"student_id": current_user.id}
		)
	except Exception as exc:
		print(f"[dashboard] failed to load tasks user={current_user.id} error={exc}")
		rows = []
	
	dashboard_cards = []
	for item in upcoming_tasks_with_priority(rows, limit=3):
		hours_remaining = max(0, int(item.due_in.total_seconds() // 3600))
		days = hours_remaining // 24
		hours = hours_remaining % 24
		time_label = f"{days}d {hours}h" if days else f"{hours}h"
		score_text = None
		# Reference: ChatGPT (OpenAI) - Canvas Grade Display Formatting
		# Date: 2026-01-22
		# Prompt: "I want to show Canvas grades on the dashboard as score/possible and percentage,
		# with safe handling for missing values. Can you suggest a robust formatting pattern?"
		# ChatGPT provided the formatting pattern with safe fallbacks.
		if item.canvas_score is not None:
			try:
				if item.canvas_possible not in (None, 0):
					percentage = (float(item.canvas_score) / float(item.canvas_possible)) * 100
					score_text = f"{item.canvas_score:.1f}/{item.canvas_possible:.1f} ({percentage:.0f}%)"
				else:
					score_text = f"{item.canvas_score:.1f}"
			except Exception:
				score_text = f"{item.canvas_score}" if item.canvas_score is not None else None
		dashboard_cards.append({
			"id": item.id,
			"title": item.title,
			"module_code": item.module_code,
			"due_at": item.due_at,
			"time_label": time_label,
			"weight": item.weight,
			"priority": item.priority,
			"status": item.status,
			"score_text": score_text,
		})
	
	progress = assess_progress(rows)

	reminders = []
	try:
		reminders = sb_fetch_all(
			"""
			SELECT r.id, r.message, r.reminder_type, r.due_at, r.created_at, r.task_id,
			       t.title, m.code AS module_code
			FROM reminders r
			LEFT JOIN tasks t ON t.id = r.task_id
			LEFT JOIN modules m ON m.id = t.module_id
			WHERE r.student_id = :student_id AND r.is_read = FALSE
			ORDER BY r.due_at NULLS LAST, r.created_at DESC
			LIMIT 5
			""",
			{"student_id": current_user.id}
		)
	except Exception as exc:
		print(f"[reminders] failed to load reminders user={current_user.id} error={exc}")

	lecturers = []
	try:
		lecturers = sb_fetch_all(
			"""
			SELECT id, name, email, module_code
			FROM lecturers
			ORDER BY name ASC
			"""
		)
	except Exception as exc:
		print(f"[lecturers] failed to load lecturers user={current_user.id} error={exc}")

	lecturer_history = []
	try:
		lecturer_history = sb_fetch_all(
			"""
			SELECT lm.id, lm.subject, lm.message, lm.sent_at, lm.email_status, lm.email_error,
			       l.name AS lecturer_name, l.module_code
			FROM lecturer_messages lm
			LEFT JOIN lecturers l ON l.id = lm.lecturer_id
			WHERE lm.student_id = :student_id
			ORDER BY lm.sent_at DESC
			LIMIT 10
			""",
			{"student_id": current_user.id}
		)
	except Exception as exc:
		print(f"[lecturers] history load failed user={current_user.id} err={exc}")

	lecturer_draft = session.pop("lecturer_draft", None)
	lecturer_subject = session.pop("lecturer_subject", "")
	lecturer_request = session.pop("lecturer_request", "")
	lecturer_id = session.pop("lecturer_id", "")

	return render_template(
		"index.html",
		upcoming_cards=dashboard_cards,
		progress=progress,
		reminders=reminders,
		lecturers=lecturers,
		lecturer_history=lecturer_history,
		lecturer_draft=lecturer_draft,
		lecturer_subject=lecturer_subject,
		lecturer_request=lecturer_request,
		lecturer_id=lecturer_id,
	)


@app.route("/semester")
@login_required
def active_semester():
	"""Active semester view filtered by a date window."""
	start_str = request.args.get("start")
	end_str = request.args.get("end")
	save_range = request.args.get("save") == "1"

	now = datetime.now(timezone.utc)
	default_start = (now - timedelta(days=120)).date()
	default_end = (now + timedelta(days=120)).date()

	def parse_date(value: str, fallback):
		try:
			return datetime.strptime(value, "%Y-%m-%d").date()
		except Exception:
			return fallback

	saved_start = session.get("semester_start")
	saved_end = session.get("semester_end")

	start_date = parse_date(start_str, parse_date(saved_start or "", default_start))
	end_date = parse_date(end_str, parse_date(saved_end or "", default_end))

	if save_range:
		session["semester_start"] = start_date.isoformat()
		session["semester_end"] = end_date.isoformat()
	start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
	end_dt = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)

	tasks = sb_fetch_all(
		"""
		SELECT t.id, t.title, t.status, t.due_date, t.due_at, t.weight_percentage,
		       m.code AS module_code
		FROM tasks t
		LEFT JOIN modules m ON m.id = t.module_id
		WHERE t.student_id = :student_id
		  AND (
			(t.due_at IS NOT NULL AND t.due_at BETWEEN :start_dt AND :end_dt)
			OR (t.due_at IS NULL AND t.due_date BETWEEN :start_date AND :end_date)
		  )
		ORDER BY t.due_at NULLS LAST, t.due_date NULLS LAST
		""",
		{
			"student_id": current_user.id,
			"start_dt": start_dt,
			"end_dt": end_dt,
			"start_date": start_date,
			"end_date": end_date,
		}
	)

	raw_events = sb_fetch_all(
		"""
		SELECT e.id, e.title, e.start_at, e.end_at, e.location, m.code AS module_code
		FROM events e
		LEFT JOIN modules m ON m.id = e.module_id
		WHERE e.student_id = :student_id
		  AND e.start_at BETWEEN :start_dt AND :end_dt
		ORDER BY e.start_at ASC
		""",
		{
			"student_id": current_user.id,
			"start_dt": start_dt,
			"end_dt": end_dt,
		}
	)

	events_map = {}
	for ev in raw_events:
		start_at = ev.get("start_at")
		time_key = None
		if start_at:
			try:
				time_key = start_at.strftime("%H:%M")
			except Exception:
				time_key = str(start_at)[11:16]
		key = (ev.get("title"), ev.get("module_code"), time_key)
		entry = events_map.get(key)
		if not entry:
			events_map[key] = {
				"title": ev.get("title"),
				"module_code": ev.get("module_code"),
				"time": time_key,
				"first": start_at,
				"last": start_at,
				"count": 1,
			}
		else:
			entry["count"] += 1
			if start_at and entry["first"] and start_at < entry["first"]:
				entry["first"] = start_at
			if start_at and entry["last"] and start_at > entry["last"]:
				entry["last"] = start_at

	events = sorted(events_map.values(), key=lambda item: (item.get("first") or datetime.min.replace(tzinfo=timezone.utc)))

	reviews = sb_fetch_all(
		"""
		SELECT ar.id, ar.filename, ar.ai_score_estimate, ar.reviewed_at,
		       t.title AS task_title, m.code AS module_code
		FROM assignment_reviews ar
		LEFT JOIN tasks t ON t.id = ar.task_id
		LEFT JOIN modules m ON m.id = t.module_id
		WHERE ar.student_id = :student_id
		  AND ar.reviewed_at BETWEEN :start_dt AND :end_dt
		ORDER BY ar.reviewed_at DESC
		LIMIT 50
		""",
		{"student_id": current_user.id, "start_dt": start_dt, "end_dt": end_dt}
	)

	lecturer_messages = sb_fetch_all(
		"""
		SELECT lm.id, lm.subject, lm.message, lm.sent_at, lm.email_status,
		       l.name AS lecturer_name
		FROM lecturer_messages lm
		LEFT JOIN lecturers l ON l.id = lm.lecturer_id
		WHERE lm.student_id = :student_id
		  AND lm.sent_at BETWEEN :start_dt AND :end_dt
		ORDER BY lm.sent_at DESC
		LIMIT 50
		""",
		{"student_id": current_user.id, "start_dt": start_dt, "end_dt": end_dt}
	)

	subtasks = sb_fetch_all(
		"""
		SELECT s.id, s.title, s.is_completed, s.planned_start, s.planned_end,
		       t.title AS task_title, m.code AS module_code
		FROM subtasks s
		JOIN tasks t ON t.id = s.task_id
		LEFT JOIN modules m ON m.id = t.module_id
		WHERE t.student_id = :student_id
		  AND (
			(s.planned_start IS NOT NULL AND s.planned_start BETWEEN :start_date AND :end_date)
			OR (s.planned_end IS NOT NULL AND s.planned_end BETWEEN :start_date AND :end_date)
			OR (s.planned_start IS NULL AND s.planned_end IS NULL AND s.created_at BETWEEN :start_dt AND :end_dt)
		  )
		ORDER BY s.created_at DESC
		LIMIT 100
		""",
		{
			"student_id": current_user.id,
			"start_date": start_date,
			"end_date": end_date,
			"start_dt": start_dt,
			"end_dt": end_dt,
		}
	)

	status_counts = {"pending": 0, "in_progress": 0, "completed": 0}
	for task in tasks:
		status = (task.get("status") or "pending").lower()
		if status in status_counts:
			status_counts[status] += 1
	total_tasks = sum(status_counts.values())
	completed_subtasks = sum(1 for s in subtasks if s.get("is_completed"))

	return render_template(
		"semester.html",
		start_date=start_date,
		end_date=end_date,
		tasks=tasks,
		events=events,
		reviews=reviews,
		lecturer_messages=lecturer_messages,
		subtasks=subtasks,
		status_counts=status_counts,
		total_tasks=total_tasks,
		total_events=len(events),
		total_reviews=len(reviews),
		total_subtasks=len(subtasks),
		completed_subtasks=completed_subtasks,
	)


@app.route("/reminders/<int:reminder_id>/read", methods=["POST"])
@login_required
def mark_reminder_read(reminder_id: int):
	try:
		sb_execute(
			"""
			UPDATE reminders
			SET is_read = TRUE
			WHERE id = :reminder_id AND student_id = :student_id
			""",
			{"reminder_id": reminder_id, "student_id": current_user.id}
		)
	except Exception as exc:
		print(f"[reminders] mark read failed user={current_user.id} err={exc}")
	return redirect(url_for("index"))


@app.route("/reminders/clear", methods=["POST"])
@login_required
def clear_reminders():
	try:
		sb_execute(
			"""
			UPDATE reminders
			SET is_read = TRUE
			WHERE student_id = :student_id
			""",
			{"student_id": current_user.id}
		)
	except Exception as exc:
		print(f"[reminders] clear failed user={current_user.id} err={exc}")
	return redirect(url_for("index"))


@app.route("/debug/db")
def debug_db():
	try:
		row = sb_fetch_one("SELECT 1 AS ok")
		ver_row = sb_fetch_one("SELECT version() AS version")
		status = {
			"connected": bool(row and row.get("ok") == 1),
			"database": "supabase_postgres",
			"version": ver_row.get("version") if ver_row else None,
		}
		return jsonify(status), 200
	except Exception as exc:
		return jsonify({"connected": False, "error": str(exc)}), 500


@app.route("/tasks")
@login_required
def tasks():
	sql = """
		SELECT t.id, t.title, t.status, t.due_date, 
		       t.canvas_assignment_id, t.canvas_course_id,
		       s.name AS student_name, 
		       m.code AS module_code
		FROM tasks t
		JOIN students s ON s.id = t.student_id
		LEFT JOIN modules m ON m.id = t.module_id
		WHERE t.student_id = :student_id
		ORDER BY t.due_date ASC
		LIMIT 200
	"""
	try:
		rows: List[Dict] = sb_fetch_all(sql, {"student_id": current_user.id})
	except Exception:
		rows = []
	return render_template("tasks.html", tasks=rows)


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id: int):
	"""Delete a task and its associated subtasks"""
	try:
		# First verify the task belongs to the current user
		task = sb_fetch_one(
			"SELECT id FROM tasks WHERE id = :task_id AND student_id = :student_id",
			{"task_id": task_id, "student_id": current_user.id}
		)
		if not task:
			flash("Task not found or permission denied.", "warning")
			return redirect(url_for("tasks"))
		
		# Delete subtasks first (if any)
		sb_execute(
			"DELETE FROM subtasks WHERE task_id = :task_id",
			{"task_id": task_id}
		)
		
		# Delete the task
		result = sb_execute(
			"DELETE FROM tasks WHERE id = :task_id AND student_id = :student_id",
			{"task_id": task_id, "student_id": current_user.id}
		)
		
		if result > 0:
			flash("Task and all associated subtasks deleted successfully.", "success")
		else:
			flash("Task not found or already deleted.", "warning")
	except Exception as exc:
		print(f"[tasks] delete failed user={current_user.id} task={task_id} err={exc}")
		flash("Failed to delete the task. Please try again.", "danger")
	return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>", methods=["GET", "POST"])
@login_required
def task_detail(task_id: int):
	"""Display a single task with its micro-task plan and allow creating subtasks."""
	task = sb_fetch_one(
		"""
		SELECT t.id, t.title, t.status, t.due_date, t.due_at, t.description,
		       t.weight_percentage, t.canvas_score, t.canvas_possible, t.canvas_graded_at,
		       t.canvas_assignment_id,
		       m.code AS module_code, m.id AS module_id
		FROM tasks t
		LEFT JOIN modules m ON m.id = t.module_id
		WHERE t.id = :task_id AND t.student_id = :student_id
		""",
		{"task_id": task_id, "student_id": current_user.id}
	)
	if not task:
		flash("Task not found or permission denied.", "error")
		return redirect(url_for("tasks"))
	
	if request.method == "POST":
		action = request.form.get("action", "add_subtask")
		if action == "update_task":
			# Reference: ChatGPT (OpenAI) - Task Update Form Validation and Date Parsing
			# Date: 2025-11-18
			# Prompt: "I need to handle form submission for updating task details. The form can have 
			# title, description, weight, due_date (date only), and due_at (datetime). I need to 
			# validate the title is required, parse dates with multiple formats, handle timezone 
			# conversions, and update the database. Can you help me write this validation and parsing 
			# logic?"
			# ChatGPT provided the form validation and date parsing logic that handles multiple date 
			# formats, timezone conversions, validates required fields, and safely updates the database 
			# with proper error handling.
			title = request.form.get("task_title", "").strip()
			description = request.form.get("task_description", "").strip() or None
			weight = request.form.get("weight_percentage")
			due_date_str = request.form.get("due_date", "").strip() or None
			due_at_str = request.form.get("due_at", "").strip() or None
			
			if not title:
				flash("Title is required.", "error")
				return redirect(url_for("task_detail", task_id=task_id))
			
			weight_value = None
			if weight:
				try:
					weight_value = float(weight)
				except ValueError:
					flash("Weighting must be numeric.", "warning")
					weight_value = None
			
			due_date = None
			due_at = None
			if due_date_str:
				try:
					from datetime import datetime
					due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
				except ValueError:
					flash("Invalid due date format.", "warning")
			if due_at_str:
				try:
					from datetime import datetime
					due_at = datetime.fromisoformat(due_at_str.replace('Z', '+00:00'))
				except ValueError:
					try:
						# Try parsing as date-time string
						due_at = datetime.strptime(due_at_str, "%Y-%m-%dT%H:%M")
					except ValueError:
						flash("Invalid due date/time format.", "warning")
			
			try:
				sb_execute(
					"""
					UPDATE tasks
					SET title = :title,
					    description = :description,
					    weight_percentage = :weight,
					    due_date = :due_date,
					    due_at = :due_at
					WHERE id = :task_id AND student_id = :student_id
					""",
					{
						"title": title,
						"description": description,
						"weight": weight_value,
						"due_date": due_date,
						"due_at": due_at,
						"task_id": task_id,
						"student_id": current_user.id
					}
				)
				flash("Assignment details updated successfully.", "success")
			except Exception as exc:
				flash(f"Failed to update assignment: {exc}", "error")
			return redirect(url_for("task_detail", task_id=task_id))

		title = request.form.get("title", "").strip()
		description = request.form.get("description", "").strip() or None
		sequence = request.form.get("sequence") or "1"
		est_hours = request.form.get("estimated_hours") or None
		planned_week = request.form.get("planned_week") or None
		planned_start = request.form.get("planned_start") or None
		planned_end = request.form.get("planned_end") or None
		
		if not title:
			flash("Subtask title is required.", "error")
		else:
			try:
				sequence_int = int(sequence)
			except ValueError:
				sequence_int = 1
			try:
				sb_execute(
					"""
					INSERT INTO subtasks (
						task_id, title, description, sequence, estimated_hours,
						planned_week, planned_start, planned_end
					) VALUES (
						:task_id, :title, :description, :sequence, :estimated_hours,
						:planned_week, :planned_start, :planned_end
					)
					""",
					{
						"task_id": task_id,
						"title": title,
						"description": description,
						"sequence": sequence_int,
						"estimated_hours": float(est_hours) if est_hours else None,
						"planned_week": int(planned_week) if planned_week else None,
						"planned_start": planned_start or None,
						"planned_end": planned_end or None,
					}
				)
				sb_execute(
					"UPDATE subtasks SET updated_at = NOW() WHERE task_id = :task_id",
					{"task_id": task_id}
				)
				flash("Subtask added successfully!", "success")
			except Exception as exc:
				flash(f"Failed to add subtask: {exc}", "error")
		return redirect(url_for("task_detail", task_id=task_id))
	
	subtasks = sb_fetch_all(
		"""
		SELECT id, title, description, sequence, estimated_hours,
		       planned_week, planned_start, planned_end,
		       is_completed, completed_at
		FROM subtasks
		WHERE task_id = :task_id
		ORDER BY sequence ASC, id ASC
		""",
		{"task_id": task_id}
	)
	print(f"[task_detail] task_id={task_id} found {len(subtasks)} subtasks")
	

	try:
		reviews = sb_fetch_all(
			"""
			SELECT id, filename, ai_feedback, ai_score_estimate, ai_possible_score,
			       reviewed_at, created_at
			FROM assignment_reviews
			WHERE task_id = :task_id AND student_id = :student_id
			ORDER BY reviewed_at DESC
			LIMIT 5
			""",
			{"task_id": task_id, "student_id": current_user.id}
		)
	except Exception as exc:
		# Table might not exist yet - return empty list
		print(f"[task_detail] Could not fetch reviews (table may not exist): {exc}")
		reviews = []
	
	return render_template("task_detail.html", task=task, subtasks=subtasks, reviews=reviews)


@app.route("/tasks/<int:task_id>/review", methods=["POST"])
@login_required
def review_assignment(task_id: int):
	"""Review and grade an assignment draft using AI"""
	# Reference: ChatGPT (OpenAI) - Assignment Review Orchestration
	# Date: 2026-01-22
	# Prompt: "I want a flow that accepts a file or text input, extracts content, sends it to
	# an AI reviewer, and stores feedback + score. Can you outline a clean end-to-end flow?"
	# ChatGPT provided the end-to-end flow and error-handling pattern.
	# Verify task exists and belongs to user
	task = sb_fetch_one(
		"""
		SELECT t.id, t.title, t.description, t.student_id
		FROM tasks t
		WHERE t.id = :task_id AND t.student_id = :student_id
		""",
		{"task_id": task_id, "student_id": current_user.id}
	)
	if not task:
		flash("Task not found or permission denied.", "error")
		return redirect(url_for("tasks"))
	
	error: Optional[str] = None
	review_result: Optional[AssignmentReviewResponse] = None
	
	# Get assignment text from file or text input
	assignment_text: Optional[str] = None
	filename: Optional[str] = None
	filepath: Optional[str] = None
	
	# Check for file upload
	file_storage = request.files.get("assignment_file")
	if file_storage and file_storage.filename:
		filename = file_storage.filename
		try:
			payload = file_storage.read()
			if not payload:
				raise ValueError("The uploaded file was empty.")
			if len(payload) > _AI_MAX_UPLOAD_BYTES:
				raise ValueError("The file is larger than 4 MB. Upload a smaller file.")
			
			# Extract text from file
			assignment_text = _extract_text_from_brief(filename, payload)
			
			# Store file on filesystem
			uploads_dir = os.path.join(app.root_path, "uploads", "assignments")
			os.makedirs(uploads_dir, exist_ok=True)
			# Create unique filename: task_id_timestamp_originalname
			from datetime import datetime
			timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
			safe_filename = f"{task_id}_{timestamp}_{filename}"
			filepath = os.path.join(uploads_dir, safe_filename)
			with open(filepath, "wb") as f:
				f.write(payload)
			
		except ValueError as exc:
			error = str(exc)
			print(f"[review-assignment] file validation error user={current_user.id} task={task_id} err={exc}")
		except Exception as exc:
			error = f"Failed to process uploaded file: {str(exc)}"
			print(f"[review-assignment] file processing failed user={current_user.id} task={task_id} err={exc}")
			import traceback
			traceback.print_exc()
	
	# Check for text input
	if not assignment_text:
		assignment_text = request.form.get("assignment_text", "").strip()
	
	if not assignment_text:
		error = "Please provide assignment content by uploading a file or pasting text."
	
	if not error:
		try:
			# Get assignment brief from task description
			assignment_brief = task.get("description")
			
			# Call ChatGPT to review and grade
			service = get_chatgpt_service()
			review_result = service.review_and_grade_assignment(
				assignment_text=assignment_text,
				task_title=task.get("title", "Assignment"),
				assignment_brief=assignment_brief
			)
			# Enforce conservative scoring caps based on weaknesses/suggestions
			if review_result and review_result.score_estimate is not None:
				try:
					score_value = float(review_result.score_estimate)
					if review_result.weaknesses or review_result.suggestions:
						score_value = min(score_value, 74.0)
					else:
						score_value = min(score_value, 79.0)
					review_result.score_estimate = score_value
				except Exception:
					pass
			
			# Format comprehensive feedback including strengths, weaknesses, and suggestions
			feedback_parts = [review_result.feedback]
			if review_result.strengths:
				feedback_parts.append("\n\n**Strengths:**\n" + "\n".join(f"• {s}" for s in review_result.strengths))
			if review_result.weaknesses:
				feedback_parts.append("\n\n**Areas for Improvement:**\n" + "\n".join(f"• {w}" for w in review_result.weaknesses))
			if review_result.suggestions:
				feedback_parts.append("\n\n**Suggestions:**\n" + "\n".join(f"• {s}" for s in review_result.suggestions))
			comprehensive_feedback = "\n".join(feedback_parts)
			
			# Save review to database
			sb_execute(
				"""
				INSERT INTO assignment_reviews (
					task_id, student_id, filename, filepath, original_text,
					ai_feedback, ai_score_estimate, ai_possible_score, reviewed_at
				) VALUES (
					:task_id, :student_id, :filename, :filepath, :original_text,
					:ai_feedback, :ai_score_estimate, :ai_possible_score, NOW()
				)
				""",
				{
					"task_id": task_id,
					"student_id": current_user.id,
					"filename": filename,
					"filepath": filepath,
					"original_text": assignment_text[:5000] if assignment_text else None,  # Store first 5000 chars
					"ai_feedback": comprehensive_feedback,
					"ai_score_estimate": review_result.score_estimate,
					"ai_possible_score": review_result.possible_score,
				}
			)
			flash("Assignment reviewed successfully! Check the review section below.", "success")
		except ChatGPTClientError as exc:
			error = f"AI review failed: {str(exc)}"
			print(f"[review-assignment] ChatGPT error user={current_user.id} task={task_id} err={exc}")
		except Exception as exc:
			error = f"Unexpected error: {str(exc)}"
			print(f"[review-assignment] Unexpected error user={current_user.id} task={task_id} err={exc}")
			import traceback
			traceback.print_exc()
	
	if error:
		flash(error, "error")
	
	return redirect(url_for("task_detail", task_id=task_id))


@app.route("/tasks/<int:task_id>/subtasks/<int:subtask_id>/toggle", methods=["POST"])
@login_required
def toggle_subtask(task_id: int, subtask_id: int):
	"""Toggle completion status of a subtask"""
	# Verify the subtask belongs to a task owned by the current user
	subtask = sb_fetch_one(
		"""
		SELECT s.id, s.task_id, s.is_completed
		FROM subtasks s
		JOIN tasks t ON t.id = s.task_id
		WHERE s.id = :subtask_id 
		  AND s.task_id = :task_id
		  AND t.student_id = :student_id
		""",
		{"subtask_id": subtask_id, "task_id": task_id, "student_id": current_user.id}
	)
	
	if not subtask:
		flash("Subtask not found or access denied.", "error")
		return redirect(url_for("task_detail", task_id=task_id))
	
	# Toggle completion status
	new_status = not subtask.get("is_completed", False)
	from datetime import datetime, timezone
	completed_at = datetime.now(timezone.utc) if new_status else None
	
	try:
		sb_execute(
			"""
			UPDATE subtasks 
			SET is_completed = :is_completed, 
			    completed_at = :completed_at,
			    updated_at = NOW()
			WHERE id = :subtask_id
			""",
			{
				"is_completed": new_status,
				"completed_at": completed_at,
				"subtask_id": subtask_id
			}
		)
		flash(f"Subtask marked as {'completed' if new_status else 'pending'}.", "success")
	except Exception as exc:
		flash(f"Failed to update subtask: {exc}", "error")
	
	return redirect(url_for("task_detail", task_id=task_id))


def _iso_date(value):
	if value is None:
		return None
	try:
		return value.strftime("%Y-%m-%d")
	except Exception:
		return str(value)


def _iso_datetime(value):
	if value is None:
		return None
	try:
		return value.isoformat()
	except Exception:
		return str(value)


# Reference: ChatGPT (OpenAI) - Text Summarization Algorithm
# Date: 2025-11-14
# Prompt: "I need a function that summarizes text to a maximum length by extracting complete 
# sentences. It should split text into sentences, add sentences until the max length is 
# reached, and handle edge cases like single very long sentences. Can you help me write this?"
# ChatGPT provided the algorithm for summarizing text by sentence extraction. It uses regex 
# to split sentences, accumulates sentences until the max length, handles single long 
# sentences, and ensures the summary doesn't cut words mid-sentence.
def _summarize_text(raw: str, max_len: int = 400) -> Optional[str]:
	text = raw.strip()
	if not text:
		return None
	try:
		import re
		sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
	except Exception:
		sentences = [s.strip() for s in text.split(".") if s.strip()]
	if not sentences:
		return None
	summary_parts = []
	total_len = 0
	for sentence in sentences:
		if summary_parts:
			add_len = len(sentence) + 1
		else:
			add_len = len(sentence)
		if summary_parts and total_len + add_len > max_len:
			break
		if not summary_parts and len(sentence) > max_len:
			sentence = sentence[:max_len]
			summary_parts.append(sentence)
			total_len = len(sentence)
			break
		summary_parts.append(sentence)
		total_len += add_len
		if total_len >= max_len:
			break
	if not summary_parts:
		return None
	combined = " ".join(summary_parts).strip()
	if len(combined) > max_len:
		combined = combined[:max_len].rsplit(" ", 1)[0] + " ..."
	return combined or None


def _build_reminder_message(task: Dict[str, Any], reminder_type: str) -> str:
	title = task.get("title") or "Untitled task"
	module_code = task.get("module_code")
	module_part = f" ({module_code})" if module_code else ""
	if reminder_type == "overdue":
		return f"Overdue: {title}{module_part}"
	if reminder_type == "due_24h":
		return f"Due in 24h: {title}{module_part}"
	return f"Due soon: {title}{module_part}"


def _send_reminder_email(*, to_email: str, subject: str, body: str) -> Optional[str]:
	# Reference: ChatGPT (OpenAI) - SMTP Email Sender Pattern
	# Date: 2026-01-22
	# Prompt: "Can you help me build a simple SMTP email sender that supports TLS and
	# optional login credentials, returning errors as strings?"
	# ChatGPT provided the SMTP send pattern used here.
	smtp_config = get_smtp_config()
	if not smtp_config:
		return "SMTP is not configured"
	try:
		message = EmailMessage()
		message["Subject"] = subject
		message["From"] = smtp_config.from_email
		message["To"] = to_email
		message.set_content(body)

		with smtplib.SMTP(smtp_config.host, smtp_config.port, timeout=10) as server:
			if smtp_config.use_tls:
				server.starttls()
			if smtp_config.username and smtp_config.password:
				server.login(smtp_config.username, smtp_config.password)
			server.send_message(message)
		return None
	except Exception as exc:
		return str(exc)


def _build_daily_summary_email(student_id: int) -> Optional[str]:
	# Reference: ChatGPT (OpenAI) - Daily Summary Grouping
	# Date: 2026-01-22
	# Prompt: "Can you help me build a daily summary email that groups tasks into overdue,
	# due in 24h, and due in 72h?"
	# ChatGPT provided the grouping and formatting pattern.
	try:
		rows = sb_fetch_all(
			"""
			SELECT t.id, t.title, t.status, t.due_date, t.due_at,
			       m.code AS module_code
			FROM tasks t
			LEFT JOIN modules m ON m.id = t.module_id
			WHERE t.student_id = :student_id
			  AND t.status IN ('pending', 'in_progress')
			""",
			{"student_id": student_id}
		)
	except Exception as exc:
		print(f"[daily-summary] failed to load tasks user={student_id} error={exc}")
		return None

	now = datetime.now(timezone.utc)
	overdue = []
	due_24h = []
	due_72h = []
	for task in rows:
		due_at = normalise_due_datetime(task, now)
		if not due_at:
			continue
		hours_remaining = (due_at - now).total_seconds() / 3600
		entry = f"- {task.get('title')} ({task.get('module_code') or 'Module'}) due {due_at.strftime('%d/%m/%Y %H:%M')}"
		if hours_remaining <= 0:
			overdue.append(entry)
		elif hours_remaining <= 24:
			due_24h.append(entry)
		elif hours_remaining <= 72:
			due_72h.append(entry)

	if not (overdue or due_24h or due_72h):
		return None

	lines = ["Your daily study summary:", ""]
	if overdue:
		lines.append("Overdue:")
		lines.extend(overdue[:5])
		lines.append("")
	if due_24h:
		lines.append("Due within 24h:")
		lines.extend(due_24h[:5])
		lines.append("")
	if due_72h:
		lines.append("Due within 72h:")
		lines.extend(due_72h[:5])
		lines.append("")
	lines.append("Open your dashboard to plan micro-tasks and stay on track.")
	return "\n".join(lines).strip()


def _generate_task_reminders(student_id: int) -> None:
	try:
		rows = sb_fetch_all(
			"""
			SELECT t.id, t.title, t.status, t.due_date, t.due_at,
			       m.code AS module_code
			FROM tasks t
			LEFT JOIN modules m ON m.id = t.module_id
			WHERE t.student_id = :student_id
			  AND t.status IN ('pending', 'in_progress')
			""",
			{"student_id": student_id}
		)
	except Exception as exc:
		print(f"[reminders] failed to load tasks user={student_id} error={exc}")
		return

	student_email = None
	email_notifications_enabled = True
	email_daily_summary_enabled = True
	try:
		student = sb_fetch_one(
			"""
			SELECT email, email_notifications_enabled, email_daily_summary_enabled
			FROM students
			WHERE id = :student_id
			""",
			{"student_id": student_id}
		)
		student_email = (student or {}).get("email")
		email_notifications_enabled = bool((student or {}).get("email_notifications_enabled", True))
		email_daily_summary_enabled = bool((student or {}).get("email_daily_summary_enabled", True))
	except Exception as exc:
		print(f"[reminders] failed to load student email user={student_id} error={exc}")

	now = datetime.now(timezone.utc)
	for task in rows:
		due_at = normalise_due_datetime(task, now)
		if not due_at:
			continue
		hours_remaining = (due_at - now).total_seconds() / 3600
		if hours_remaining <= 0:
			reminder_type = "overdue"
		elif hours_remaining <= 24:
			reminder_type = "due_24h"
		elif hours_remaining <= 72:
			reminder_type = "due_72h"
		else:
			continue

		message = _build_reminder_message(task, reminder_type)
		try:
			inserted = sb_execute(
				"""
				INSERT INTO reminders (
					student_id, task_id, reminder_type, message, due_at, created_at, is_read
				) VALUES (
					:student_id, :task_id, :reminder_type, :message, :due_at, NOW(), FALSE
				)
				ON CONFLICT (student_id, task_id, reminder_type) DO NOTHING
				""",
				{
					"student_id": student_id,
					"task_id": task.get("id"),
					"reminder_type": reminder_type,
					"message": message,
					"due_at": due_at,
				}
			)
			if inserted and student_email and email_notifications_enabled:
				subject = message
				body = (
					f"{message}\n"
					f"Due: {due_at.strftime('%d/%m/%Y %H:%M')}\n\n"
					"Open your dashboard to view task details."
				)
				error = _send_reminder_email(
					to_email=student_email,
					subject=subject,
					body=body
				)
				status = "sent" if error is None else "failed"
				sb_execute(
					"""
					UPDATE reminders
					SET email_sent_at = NOW(),
					    email_status = :status,
					    email_error = :error
					WHERE student_id = :student_id
					  AND task_id = :task_id
					  AND reminder_type = :reminder_type
					""",
					{
						"status": status,
						"error": error,
						"student_id": student_id,
						"task_id": task.get("id"),
						"reminder_type": reminder_type,
					}
				)
		except Exception as exc:
			print(f"[reminders] insert failed user={student_id} task={task.get('id')} err={exc}")


def _extract_query_terms(question: str) -> List[str]:
	import re
	stopwords = {
		"the", "and", "for", "with", "that", "this", "from", "into", "onto", "over", "under",
		"about", "what", "when", "where", "which", "who", "whom", "why", "how", "can", "could",
		"should", "would", "will", "may", "might", "must", "is", "are", "was", "were", "be",
		"been", "being", "a", "an", "of", "to", "in", "on", "at", "by", "as", "it", "its",
		"your", "our", "their", "they", "we", "you", "i", "me", "my", "mine", "ours"
	}
	tokens = re.findall(r"[a-z0-9']+", question.lower())
	return [t for t in tokens if len(t) > 2 and t not in stopwords]


def _score_text_for_query(text: str, terms: List[str]) -> int:
	if not text or not terms:
		return 0
	text_lower = text.lower()
	return sum(text_lower.count(term) for term in terms)


def _select_course_materials(
	documents: List[Dict[str, Any]],
	question: str,
	max_docs: int = 3,
	max_chars: int = 6000
) -> List[Dict[str, str]]:
	terms = _extract_query_terms(question)
	scored = []
	for doc in documents:
		text = (doc.get("extracted_text") or "").strip()
		score = _score_text_for_query(text, terms)
		uploaded = doc.get("uploaded_at") or datetime.min
		scored.append((score, uploaded, doc))
	scored.sort(key=lambda item: (item[0], item[1]), reverse=True)

	selected: List[Dict[str, str]] = []
	total_chars = 0
	for score, _uploaded, doc in scored:
		if len(selected) >= max_docs:
			break
		raw_text = (doc.get("extracted_text") or "").strip()
		if not raw_text:
			continue
		clean = " ".join(raw_text.split())
		remaining = max_chars - total_chars
		if remaining <= 0:
			break
		snippet = clean[:min(2500, remaining)]
		source_name = doc.get("filename") or f"Document {doc.get('id')}"
		selected.append({"source": source_name, "content": snippet})
		total_chars += len(snippet)
	return selected


# Reference: ChatGPT (OpenAI) - Prompt Text Sanitization
# Date: 2025-11-14
# Prompt: "I need to sanitize assignment briefs before sending them to AI. I need to remove 
# sensitive words (plagiarism, harassment, etc.) and replace them with safer alternatives. 
# Also strip content after certain markers like 'Rubric:' or 'Required Format:'. Can you 
# help me write this sanitization function?"
# ChatGPT provided the text sanitization logic that replaces sensitive keywords, strips 
# content after specific markers, and calls the summarization function to keep text concise. 
# This prevents AI safety blocks and keeps prompts focused.
def _sanitize_prompt_text(value: Optional[str]) -> Optional[str]:
	if not value:
		return None
	text = str(value)
	for marker in [
		"Rubric:",
		"Required Format:",
		"Referencing:",
		"Assignments should be",
		"Applications must be made",
	]:
		if marker in text:
			text = text.split(marker)[0]
			break
	replacements = {
		"plagiarism": "academic integrity",
		"harassment": "unwanted behaviour",
		"violence": "serious behaviour issue",
		"suicide": "self-care concern",
		"self-harm": "self-care concern",
	}
	for target, replacement in list(replacements.items()):
		text = text.replace(target, replacement)
		text = text.replace(target.capitalize(), replacement.capitalize())
		text = text.replace(target.upper(), replacement.upper())
	clean = " ".join(text.split())
	summary = _summarize_text(clean, max_len=400)
	return summary


# Reference: ChatGPT (OpenAI) - Multi-Format File Text Extraction
# Date: 2025-11-14
# Prompt: "I need a function that extracts text from multiple file formats: plain text (.txt, 
# .md), DOCX files, and PDF files. It should handle encoding issues, extract text from DOCX 
# paragraphs and tables, and extract text from PDF pages. Can you help me write this with 
# proper error handling?"
# ChatGPT provided the multi-format text extraction logic with encoding fallbacks for text 
# files, paragraph and table extraction for DOCX files, and page-by-page extraction for PDFs. 
# Includes comprehensive error handling and validation.
def _extract_text_from_brief(filename: str, payload: bytes) -> str:
	suffix = Path(filename or "").suffix.lower()
	if suffix not in _AI_ALLOWED_SUFFIXES:
		allowed = ", ".join(sorted(_AI_ALLOWED_SUFFIXES))
		raise ValueError(f"Unsupported file type '{suffix or 'unknown'}'. Upload one of: {allowed}.")
	if suffix in {".txt", ".md", ".markdown"}:
		for encoding in ("utf-8", "utf-16", "latin-1"):
			try:
				return payload.decode(encoding)
			except UnicodeDecodeError:
				continue
		return payload.decode("utf-8", errors="ignore")
	if suffix == ".docx":
		try:
			from docx import Document  # type: ignore
		except ImportError as exc:  # pragma: no cover - dependency guard
			raise ValueError("python-docx is required to read DOCX files. Install python-docx.") from exc
		try:
			document = Document(BytesIO(payload))
			# Extract text from all paragraphs
			lines = []
			for paragraph in document.paragraphs:
				if paragraph.text and paragraph.text.strip():
					lines.append(paragraph.text.strip())
			# Also try to extract text from tables
			for table in document.tables:
				for row in table.rows:
					for cell in row.cells:
						if cell.text and cell.text.strip():
							lines.append(cell.text.strip())
			result = "\n".join(lines).strip()
			if not result:
				raise ValueError("The DOCX file appears to be empty or contains only formatting.")
			return result
		except ValueError:
			raise  # Re-raise ValueError as-is
		except Exception as exc:
			print(f"[docx-extract] Error reading DOCX file: {exc}")
			import traceback
			traceback.print_exc()
			raise ValueError(f"Could not read the DOCX file: {str(exc)}. Ensure it is not password protected or corrupted.") from exc
	if suffix == ".pdf":
		try:
			from pypdf import PdfReader  # type: ignore
		except ImportError as exc:  # pragma: no cover
			raise ValueError("pypdf is required to read PDF files. Install pypdf.") from exc
		try:
			reader = PdfReader(BytesIO(payload))
			pages = []
			for page in reader.pages:
				text = page.extract_text() or ""
				text = text.strip()
				if text:
					pages.append(text)
			content = "\n\n".join(pages).strip()
			if not content:
				raise ValueError("The PDF did not contain extractable text.")
			return content
		except ValueError:
			raise
		except Exception as exc:
			raise ValueError("Could not read the PDF file. Ensure it is not locked or scanned.") from exc
	return ""


def _format_future_date(value) -> str:
	if value is None:
		return "unscheduled"
	try:
		if isinstance(value, datetime):
			return value.strftime("%d %b %Y %H:%M")
		return value.strftime("%d %b %Y")  # date
	except Exception:
		return str(value)


# Reference: ChatGPT (OpenAI) - Calendar Context Building for AI Prompts
# Date: 2025-11-14
# Prompt: "I need to build a summary of a student's upcoming assignments and calendar events 
# to include in the AI prompt. This helps the AI suggest realistic timing for new task breakdowns 
# that don't conflict with existing commitments. Can you help me format this context information?"
# ChatGPT provided the structure for building a context summary that includes upcoming assignments 
# with due dates, weights, and status, plus calendar events with locations. This context is 
# included in AI prompts to enable smarter scheduling suggestions.
def _build_schedule_context(student_id: int) -> str:
	"""Summarise upcoming assignments and events so the AI can propose realistic timings."""
	lines: List[str] = []
	try:
		upcoming_tasks = sb_fetch_all(
			"""
			SELECT t.title,
			       t.due_date,
			       t.due_at,
			       t.status,
			       t.weight_percentage,
			       m.code AS module_code
			FROM tasks t
			JOIN modules m ON m.id = t.module_id
			WHERE t.student_id = :student_id
			  AND (t.status IS NULL OR t.status <> 'completed')
			  AND (t.due_date IS NULL OR t.due_date >= CURRENT_DATE)
			ORDER BY t.due_date ASC NULLS LAST
			LIMIT 5
			""",
			{"student_id": student_id}
		)
	except Exception as exc:
		print(f"[ai-workspace] schedule task fetch failed user={student_id} err={exc}")
		upcoming_tasks = []
	if upcoming_tasks:
		lines.append("Upcoming assignments:")
		for task in upcoming_tasks:
			title = task.get("title") or "Assignment"
			module = task.get("module_code") or "Module"
			due_date = _format_future_date(task.get("due_at") or task.get("due_date"))
			status = task.get("status") or "pending"
			weight = task.get("weight_percentage")
			weight_str = f" · weight {weight:.0f}%" if weight else ""
			lines.append(f"- {title} ({module}) due {due_date} · status {status}{weight_str}")
	else:
		lines.append("No other upcoming assignments found in the database.")
	try:
		upcoming_events = sb_fetch_all(
			"""
			SELECT title, start_at, end_at, location
			FROM events
			WHERE student_id = :student_id
			  AND start_at >= NOW()
			ORDER BY start_at ASC
			LIMIT 4
			""",
			{"student_id": student_id}
		)
	except Exception as exc:
		print(f"[ai-workspace] schedule events fetch failed user={student_id} err={exc}")
		upcoming_events = []
	if upcoming_events:
		lines.append("Calendar events:")
		for event in upcoming_events:
			title = event.get("title") or "Event"
			start = _format_future_date(event.get("start_at"))
			location = event.get("location")
			loc = f" @ {location}" if location else ""
			lines.append(f"- {title} on {start}{loc}")
	else:
		lines.append("No upcoming events in the calendar.")
	return "\n".join(lines)


# Reference: ChatGPT (OpenAI) - Datetime Rounding to Nearest Half Hour
# Date: 2025-11-14
# Prompt: "I need a function that rounds a datetime to the nearest hour or 30-minute mark, 
# always rounding up. So 2:15 PM becomes 2:30 PM, 2:45 PM becomes 3:00 PM. Can you help me 
# write this rounding logic?"
# ChatGPT provided the datetime rounding algorithm that rounds to the nearest hour or 
# 30-minute mark, always rounding up. This ensures calendar events start at clean time 
# boundaries (hour or half-hour marks).
def _round_to_nearest_half_hour(dt: datetime) -> datetime:
	"""Round datetime to nearest hour or 30-minute mark, always rounding up"""
	minutes = dt.minute
	seconds = dt.second
	microseconds = dt.microsecond
	
	if minutes < 15 and seconds == 0 and microseconds == 0:
		return dt.replace(second=0, microsecond=0)
	elif minutes < 15:
		return dt.replace(minute=30, second=0, microsecond=0)
	elif minutes < 45:
		return dt.replace(minute=30, second=0, microsecond=0)
	else:
		# Round up to next hour
		return (dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))


def _ensure_datetime(value, tzinfo) -> Optional[datetime]:
	if value is None:
		return None
	if isinstance(value, datetime):
		if value.tzinfo is None:
			return value.replace(tzinfo=tzinfo)
		return value
	if isinstance(value, str):
		try:
			dt = datetime.fromisoformat(value)
		except ValueError:
			return None
		if dt.tzinfo is None:
			return dt.replace(tzinfo=tzinfo)
		return dt
	return None


# Reference: ChatGPT (OpenAI) - Interval Arithmetic for Time Slots
# Date: 2025-11-14
# Prompt: "I need a function that subtracts a busy time interval from a list of free time segments. 
# If a busy interval overlaps with a free segment, I need to split the free segment into parts 
# that don't overlap. Can you help me write this interval subtraction logic?"
# ChatGPT provided the algorithm for subtracting busy intervals from free time segments by 
# checking overlap conditions and splitting segments accordingly. This is used to find available 
# time slots after accounting for existing calendar events.
def _subtract_interval(segments: List[Tuple[datetime, datetime]], busy: Tuple[datetime, datetime]) -> List[Tuple[datetime, datetime]]:
	result: List[Tuple[datetime, datetime]] = []
	busy_start, busy_end = busy
	for start, end in segments:
		if busy_end <= start or busy_start >= end:
			result.append((start, end))
			continue
		if busy_start > start:
			result.append((start, busy_start))
		if busy_end < end:
			result.append((busy_end, end))
	return [(s, e) for s, e in result if s < e]


# Reference: ChatGPT (OpenAI) - Free Time Slot Generation Algorithm
# Date: 2025-11-14
# Prompt: "I need to find free time slots in a student's calendar. I have a working day window 
# (9 AM to 9 PM), existing calendar events (busy intervals), and I need to find all available 
# 30+ minute slots over the next few weeks. Can you help me write an algorithm that subtracts 
# busy intervals from working hours and returns free slots?"
# ChatGPT provided the algorithm for generating free time slots by defining a working window 
# (9 AM - 9 PM), iterating through each day, and subtracting busy intervals from each day's 
# working hours using interval arithmetic. This ensures AI-generated tasks can be scheduled 
# in available time.
def _generate_free_slots(student_id: int, tzinfo, horizon_days: int = 21) -> List[Tuple[datetime, datetime]]:
	now = datetime.now(tzinfo)
	start_date = now.date()
	try:
		rows = sb_fetch_all(
			"""
			SELECT start_at, end_at
			FROM events
			WHERE student_id = :student_id
			  AND start_at IS NOT NULL
			  AND end_at IS NOT NULL
			  AND start_at >= NOW()
			  AND start_at <= NOW() + interval '30 days'
			""",
			{"student_id": student_id}
		)
	except Exception:
		rows = []
	busy_intervals: List[Tuple[datetime, datetime]] = []
	for row in rows:
		start = _ensure_datetime(row.get("start_at"), tzinfo)
		end = _ensure_datetime(row.get("end_at"), tzinfo)
		if start and end and end > now:
			busy_intervals.append((start, end))
	busy_intervals.sort(key=lambda item: item[0])
	free_slots: List[Tuple[datetime, datetime]] = []
	work_start = time(hour=9)
	work_end = time(hour=21)
	for day_offset in range(horizon_days):
		day = start_date + timedelta(days=day_offset)
		day_start = datetime.combine(day, work_start, tzinfo)
		day_end = datetime.combine(day, work_end, tzinfo)
		if day_end <= now:
			continue
		if day_start < now:
			day_start = now
		segments = [(day_start, day_end)]
		for busy in busy_intervals:
			if busy[0].date() != day:
				continue
			segments = _subtract_interval(segments, busy)
			if not segments:
				break
		for segment in segments:
			if segment[1] - segment[0] >= timedelta(minutes=30):
				free_slots.append(segment)
	return free_slots


def _parse_due_datetime(due_date_str: Optional[str], tzinfo) -> Optional[datetime]:
	if not due_date_str:
		return None
	try:
		dt = datetime.strptime(due_date_str, "%Y-%m-%d")
	except ValueError:
		return None
	return datetime.combine(dt.date(), time(hour=23, minute=59), tzinfo)


def _lookup_module_id(module_code: Optional[str], student_id: int) -> Optional[int]:
	if not module_code:
		return None
	try:
		row = sb_fetch_one(
			"""
			SELECT id FROM modules
			WHERE code ILIKE :code
			LIMIT 1
			""",
			{"code": module_code}
		)
	except Exception:
		row = None
	if row:
		return row.get("id")
	return None


# Reference: ChatGPT (OpenAI) - Task Lookup and Creation Pattern
# Date: 2025-11-14
# Prompt: "I need a function that looks up an existing task by title and module, and if 
# not found, creates a new task. It should handle both tasks with and without modules, 
# parse due dates from strings, and set default due times. Can you help me write this?"
# ChatGPT provided the lookup-or-create pattern for tasks. It searches by title and module 
# (or NULL module), handles date parsing with multiple formats, sets default due times, and 
# returns the task ID for linking subtasks.
def _lookup_or_create_task(assignment_title: str, module_id: Optional[int], module_code: Optional[str], 
                           student_id: int, due_date_str: Optional[str]) -> Optional[int]:
	"""Look up existing task or create a new one for AI-generated subtasks"""
	if not assignment_title:
		return None
	
	# First, try to find an existing task by title and module
	try:
		if module_id:
			task = sb_fetch_one(
				"""
				SELECT id FROM tasks
				WHERE student_id = :student_id
				  AND module_id = :module_id
				  AND title ILIKE :title
				LIMIT 1
				""",
				{"student_id": student_id, "module_id": module_id, "title": assignment_title}
			)
		else:
			task = sb_fetch_one(
				"""
				SELECT id FROM tasks
				WHERE student_id = :student_id
				  AND module_id IS NULL
				  AND title ILIKE :title
				LIMIT 1
				""",
				{"student_id": student_id, "title": assignment_title}
			)
		
		if task:
			return task.get("id")
	except Exception as exc:
		print(f"[ai-workspace] task lookup failed: {exc}")
		import traceback
		traceback.print_exc()
		pass
	
	# Create new task if not found
	try:
		print(f"[ai-workspace] Creating new task: title='{assignment_title}', module_id={module_id}, due_date={due_date_str}")
		from datetime import datetime, date, timezone
		due_date = None
		due_at_value = None
		
		if due_date_str:
			try:
				# Try parsing as date first
				due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
				# Set due_at to end of day (5 PM) if only date provided
				due_at_value = datetime.combine(due_date, datetime.min.time().replace(hour=17, minute=0))
				if due_at_value.tzinfo is None:
					due_at_value = due_at_value.replace(tzinfo=timezone.utc)
			except ValueError:
				try:
					due_at_value = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
					due_date = due_at_value.date()
				except:
					pass
		
		sb_execute(
			"""INSERT INTO tasks (title, student_id, module_id, due_date, due_at, status) 
			   VALUES (:title, :student_id, :module_id, :due_date, :due_at, 'pending')""",
			{
				"title": assignment_title,
				"student_id": student_id,
				"module_id": module_id,
				"due_date": due_date,
				"due_at": due_at_value
			}
		)
		
		# Fetch the newly created task ID
		if module_id:
			task = sb_fetch_one(
				"""
				SELECT id FROM tasks
				WHERE student_id = :student_id
				  AND module_id = :module_id
				  AND title ILIKE :title
				LIMIT 1
				""",
				{"student_id": student_id, "module_id": module_id, "title": assignment_title}
			)
		else:
			task = sb_fetch_one(
				"""
				SELECT id FROM tasks
				WHERE student_id = :student_id
				  AND module_id IS NULL
				  AND title ILIKE :title
				LIMIT 1
				""",
				{"student_id": student_id, "title": assignment_title}
			)
		
		if task:
			print(f"[ai-workspace] Successfully created task_id={task.get('id')}")
			return task.get("id")
		else:
			print(f"[ai-workspace] WARNING: Task created but could not retrieve task_id")
	except Exception as exc:
		print(f"[ai-workspace] failed to create task: {exc}")
		import traceback
		traceback.print_exc()
		pass
	
	return None


# Reference: ChatGPT (OpenAI) - Natural Language Date/Time Parsing
# Date: 2025-11-14
# Prompt: "The AI sometimes returns time hints like 'Tuesday evening', 'next week afternoon', 
# or ISO dates. I need a function that can parse these natural language hints and convert them 
# to datetime objects. It should handle multiple date formats and extract time-of-day hints 
# (morning, afternoon, evening, night) to set appropriate hours."
# ChatGPT provided the parsing logic for multiple date formats and natural language time-of-day 
# hints. The function tries various date formats, extracts time-of-day keywords to set hours, 
# and falls back to ISO parsing. This allows the scheduling system to respect AI-suggested 
# preferred times.
def _parse_plan_hint(text: Optional[str], tzinfo) -> Optional[datetime]:
	if not text:
		return None
	value = text.strip()
	if not value:
		return None
	candidates = [
		"%Y-%m-%d %H:%M",
		"%Y-%m-%d",
		"%d %b %Y",
		"%d %B %Y",
		"%b %d %Y",
		"%B %d %Y",
	]
	lower = value.lower()
	hour = 9
	if "evening" in lower:
		hour = 19
	elif "afternoon" in lower:
		hour = 14
	elif "morning" in lower:
		hour = 10
	elif "night" in lower:
		hour = 21
	for fmt in candidates:
		try:
			dt = datetime.strptime(value.split(" evening")[0].split(" afternoon")[0].split(" morning")[0].split(" night")[0].strip(), fmt)
			if "hour" in fmt.lower():
				return dt.replace(tzinfo=tzinfo)
			return datetime.combine(dt.date(), time(hour=hour), tzinfo)
		except ValueError:
			continue
	# Try ISO parse
	try:
		dt = datetime.fromisoformat(value)
		if dt.tzinfo is None:
			dt = dt.replace(tzinfo=tzinfo)
		return dt
	except ValueError:
		return None


# Reference: ChatGPT (OpenAI) - Even Task Distribution Scheduling Algorithm
# Date: 2025-11-14
# Prompt: "I need to schedule AI-generated subtasks into calendar slots. The AI suggests preferred 
# times, but I need to distribute tasks evenly across available time until the deadline. If a task 
# can't fit in the preferred time slot, find the nearest available slot. Tasks should be spread out 
# evenly, not clustered on one day. Can you help me write this scheduling algorithm?"
# ChatGPT provided the algorithm for distributing subtasks evenly across available time slots. 
# It prioritizes AI-suggested times when possible, but evenly spreads tasks across the available 
# window until the deadline. The algorithm uses slot consumption to prevent double-booking and 
# finds nearest available slots when preferred times are unavailable.
def _schedule_ai_subtasks(
	*,
	subtasks: List[Dict[str, Any]],
	student_id: int,
	module_id: Optional[int],
	assignment_title: str,
	due_date_str: Optional[str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
	tzinfo = datetime.now().astimezone().tzinfo
	now = datetime.now(tzinfo)
	free_slots = _generate_free_slots(student_id, tzinfo)
	if not free_slots:
		return [], subtasks
	due_deadline = _parse_due_datetime(due_date_str, tzinfo)
	if due_deadline:
		before = [slot for slot in free_slots if slot[0] <= due_deadline]
		after = [slot for slot in free_slots if slot[0] > due_deadline]
		slot_queue = before + after
	else:
		slot_queue = free_slots[:]
	slot_queue.sort(key=lambda s: s[0])
	scheduled: List[Dict[str, Any]] = []
	unscheduled: List[Dict[str, Any]] = []

	def consume_slot(idx: int, duration: timedelta) -> Optional[Tuple[datetime, datetime]]:
		start, end = slot_queue[idx]
		# Need duration + 30 min buffer for spacing
		if end - start < duration + timedelta(minutes=30):
			return None
		
		# Round start time to nearest hour or 30 minutes, but never below slot start
		assigned_start = _round_to_nearest_half_hour(start)
		# If rounding went below slot start, round up to next half hour
		if assigned_start < start:
			# Round up to next :00 or :30
			if start.minute < 30:
				assigned_start = start.replace(minute=30, second=0, microsecond=0)
			else:
				assigned_start = (start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
			# If still below, just use the slot start
			if assigned_start < start:
				assigned_start = start.replace(second=0, microsecond=0)
		
		if assigned_start >= end:
			return None
		
		# Calculate end time
		assigned_end = assigned_start + duration
		# Round end time to nearest half hour, but ensure it doesn't exceed slot end
		assigned_end_rounded = _round_to_nearest_half_hour(assigned_end)
		if assigned_end_rounded > end:

			assigned_end = end.replace(second=0, microsecond=0)
		else:
			assigned_end = assigned_end_rounded
		
		# Ensure end is after start
		if assigned_end <= assigned_start:
			assigned_end = assigned_start + duration
			if assigned_end > end:
				return None
		
		# Add 30 minute buffer after event to prevent overlap (increased from 15 to 30)
		buffer_end = assigned_end + timedelta(minutes=30)
		
		if buffer_end <= end:
			slot_queue[idx] = (buffer_end, end)
		elif assigned_end < end:
			slot_queue[idx] = (assigned_end, end)
		else:
			slot_queue.pop(idx)
		return assigned_start, assigned_end

	total_subtasks = len(subtasks)
	if total_subtasks <= 0:
		return [], []

	for idx, subtask in enumerate(subtasks):
		estimated_hours = subtask.get("estimated_hours")
		try:
			duration_hours = float(estimated_hours) if estimated_hours is not None else 2.0
		except (ValueError, TypeError):
			duration_hours = 2.0
		duration_hours = max(0.5, min(duration_hours, 6.0))
		duration = timedelta(hours=duration_hours)
		target_time = _parse_plan_hint(subtask.get("planned_start"), tzinfo)
		if not target_time:
			if due_deadline:
				window = max(due_deadline - now, timedelta(days=1))
				# Spread more evenly across available time
				target_time = now + (window * (idx / max(total_subtasks - 1, 1)))
			else:
				# Spread across days: one task per day
				target_time = now + timedelta(days=idx)

		# Build candidates with preference for spreading across days
		candidate_indices = list(range(len(slot_queue)))
		# Count how many tasks are already scheduled on each day
		day_counts = {}
		for scheduled_item in scheduled:
			start_dt = scheduled_item.get("start")
			if isinstance(start_dt, datetime):
				day_key = start_dt.date()
				day_counts[day_key] = day_counts.get(day_key, 0) + 1
		
		candidate_indices.sort(
			key=lambda i: (
				0 if slot_queue[i][0] >= target_time else 1,  # Prefer future slots
				day_counts.get(slot_queue[i][0].date(), 0),  # Prefer days with fewer tasks
				abs((slot_queue[i][0] - target_time).total_seconds())  # Then closest to target
			)
		)

		assignment_slot = None
		for slot_idx in candidate_indices:
			if slot_idx >= len(slot_queue):
				continue
			slot_start, slot_end = slot_queue[slot_idx]
			if slot_end - slot_start < duration + timedelta(minutes=30):
				continue
			
			# Calculate what the assigned times would be (before consuming)
			# Round start time to nearest hour or 30 minutes, but never below slot start
			potential_start = _round_to_nearest_half_hour(slot_start)
			if potential_start < slot_start:
				if slot_start.minute < 30:
					potential_start = slot_start.replace(minute=30, second=0, microsecond=0)
				else:
					potential_start = (slot_start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
				if potential_start < slot_start:
					potential_start = slot_start.replace(second=0, microsecond=0)
			
			if potential_start >= slot_end:
				continue
			
			potential_end = potential_start + duration
			potential_end_rounded = _round_to_nearest_half_hour(potential_end)
			if potential_end_rounded > slot_end:
				potential_end = slot_end.replace(second=0, microsecond=0)
			else:
				potential_end = potential_end_rounded
			
			if potential_end <= potential_start:
				potential_end = potential_start + duration
				if potential_end > slot_end:
					continue
			
			# Reference: ChatGPT (OpenAI) - Calendar Event Overlap Detection
			# Date: 2025-11-14
			# Prompt: "I need to check if a new calendar event would overlap with existing events, 
			# including a buffer time (30 minutes) between events. The overlap check should account 
			# for both the new event's time and the buffer. Can you help me write this overlap 
			# detection logic?"
			# ChatGPT provided the overlap detection algorithm that checks if a new event (with buffer) 
			# overlaps with existing events. It compares start and end times with buffers to prevent 
			# double-booking and ensures events have proper spacing.
			# Check for overlaps with already-scheduled events (with 30 min buffer)
			overlaps = False
			for existing in scheduled:
				existing_start = existing.get("start")
				existing_end = existing.get("end")
				if isinstance(existing_start, datetime) and isinstance(existing_end, datetime):
					# Check if new event overlaps with existing event (with buffers)
					new_start = potential_start
					new_end = potential_end + timedelta(minutes=30)  # Include buffer in check
					existing_end_buffered = existing_end + timedelta(minutes=30)
					# Overlap if: new_start < existing_end_buffered AND new_end > existing_start
					if new_start < existing_end_buffered and new_end > existing_start:
						overlaps = True
						break
			
			if overlaps:
				# Skip this slot and try next one
				continue
			
			# No overlap found, consume the slot
			assignment_slot = consume_slot(slot_idx, duration)
			if assignment_slot:
				start_ts, end_ts = assignment_slot
				scheduled.append({
					"title": f"{assignment_title}: {subtask.get('title') or 'Subtask'}",
					"start": start_ts,
					"end": end_ts,
					"focus": subtask.get("focus"),
					"module_id": module_id,
				})
				break
		
		if not assignment_slot:
			unscheduled.append(subtask)
	return scheduled, unscheduled


@app.route("/ai-workspace", methods=["GET", "POST"])
@login_required
def ai_workspace():
	error: Optional[str] = None
	breakdown = None
	combined_text: Optional[str] = None
	sanitized_summary: Optional[str] = None
	uploaded_filename: Optional[str] = None
	form_data: Dict[str, str] = {}
	schedule_context_text: Optional[str] = None
	plan_payload: Optional[Dict[str, Any]] = None
	
	if request.method == "POST":
		form_data = request.form.to_dict()
		title = (form_data.get("assignment_title") or "").strip()
		module_code = (form_data.get("module_code") or "").strip() or None
		due_date = (form_data.get("due_date") or "").strip() or None
		status = (form_data.get("status") or "").strip() or None
		context_text = (form_data.get("additional_context") or "").strip()
		manual_text = (form_data.get("brief_text") or "").strip()
		
		segments: List[str] = []
		file_storage = request.files.get("brief_file")
		if file_storage and file_storage.filename:
			uploaded_filename = file_storage.filename
			try:
				payload = file_storage.read()
				if not payload:
					raise ValueError("The uploaded file was empty.")
				if len(payload) > _AI_MAX_UPLOAD_BYTES:
					raise ValueError("The file is larger than 4 MB. Upload a smaller brief.")
				segments.append(_extract_text_from_brief(uploaded_filename, payload))
			except ValueError as exc:
				error = str(exc)
				print(f"[ai-workspace] file validation error user={current_user.id} file={uploaded_filename} err={exc}")
			except Exception as exc:  # pragma: no cover - defensive guard
				print(f"[ai-workspace] file read failed user={current_user.id} file={uploaded_filename} err={exc}")
				import traceback
				traceback.print_exc()
				error = f"Failed to read the uploaded file: {str(exc)}"
		
		if manual_text:
			segments.append(manual_text)
		
		if not error:
			combined_text = "\n\n".join([segment for segment in segments if segment]).strip()
			if not combined_text:
				error = "Provide an assignment brief by uploading a file or pasting text."
			else:
				sanitized_summary = _sanitize_prompt_text(combined_text) or _summarize_text(combined_text, max_len=400)
				context_summary = _sanitize_prompt_text(context_text) or None
				if not sanitized_summary:
					error = "Could not prepare the assignment brief. Try adding more detail."
				else:
					schedule_context = _build_schedule_context(current_user.id)
					schedule_context_text = schedule_context
					try:
						service = get_chatgpt_service()
						breakdown = service.breakdown_task(
							task_title=title or "Assignment Plan",
							module_code=module_code,
							due_date=due_date,
							due_at=None,
							status=status,
							description=sanitized_summary,
							additional_context=context_summary,
							schedule_context=schedule_context
						)
					except ChatGPTClientError as exc:
						error = str(exc)
					except Exception as exc:  # pragma: no cover - defensive logging
						print(f"[ai-workspace] chatgpt breakdown failed user={current_user.id} err={exc}")
						error = "ChatGPT request failed. Try again later."
					else:
						if breakdown:
							plan_payload = {
								"subtasks": [
									{
										"sequence": item.sequence,
										"title": item.title,
										"description": item.description,
										"estimated_hours": item.estimated_hours,
										"planned_start": item.planned_start,
										"planned_end": item.planned_end,
										"focus": item.focus,
									}
									for item in breakdown.subtasks
								],
								"advice": breakdown.advice,
							}
	else:
		form_data = {
			"assignment_title": "",
			"module_code": "",
			"due_date": "",
			"status": "",
			"brief_text": "",
			"additional_context": "",
		}
	
	return render_template(
		"ai_workspace.html",
		breakdown=breakdown,
		error=error,
		form_data=form_data,
		source_text=combined_text,
		sanitized_summary=sanitized_summary,
		uploaded_filename=uploaded_filename,
		schedule_context_text=schedule_context_text,
		plan_payload=plan_payload,
	)


@app.route("/ai-workspace/save", methods=["POST"])
@login_required
def ai_workspace_save():
	plan_json = request.form.get("plan_json")
	if not plan_json:
		flash("No AI plan found to save.", "danger")
		return redirect(url_for("ai_workspace"))
	try:
		payload = json.loads(plan_json)
	except json.JSONDecodeError:
		flash("The AI plan data was invalid.", "danger")
		return redirect(url_for("ai_workspace"))
	subtasks = payload.get("subtasks")
	if not isinstance(subtasks, list) or not subtasks:
		flash("The AI plan did not contain any subtasks to schedule.", "warning")
		return redirect(url_for("ai_workspace"))

	assignment_title = (request.form.get("assignment_title") or "Assignment Plan").strip()
	module_code = (request.form.get("module_code") or "").strip() or None
	due_date_str = (request.form.get("due_date") or "").strip() or None

	module_id = _lookup_module_id(module_code, current_user.id)
	
	# Look up or create task for the subtasks
	task_id = _lookup_or_create_task(assignment_title, module_id, module_code, current_user.id, due_date_str)
	print(f"[ai-workspace] task_id={task_id} for assignment '{assignment_title}' (module_id={module_id})")
	
	if not task_id:
		print(f"[ai-workspace] WARNING: Could not find or create task for '{assignment_title}'. Subtasks will only be saved to calendar.")
	
	try:
		scheduled, unscheduled = _schedule_ai_subtasks(
			subtasks=subtasks,
			student_id=current_user.id,
			module_id=module_id,
			assignment_title=assignment_title,
			due_date_str=due_date_str,
		)
	except Exception as exc:
		print(f"[ai-workspace] schedule failed user={current_user.id} err={exc}")
		import traceback
		traceback.print_exc()
		flash("Failed to schedule the AI plan. Please try again.", "danger")
		return redirect(url_for("ai_workspace"))

	created_events = 0
	created_subtasks = 0
	
	# Save subtasks to the subtasks table (if task was found/created)
	if task_id:
		print(f"[ai-workspace] Saving {len(subtasks)} subtasks to task_id={task_id}")
		for idx, item in enumerate(subtasks, start=1):
			try:
				sequence = item.get("sequence", idx)
				subtask_title = item.get("title") or f"Subtask {idx}"
				description = item.get("description")
				estimated_hours = item.get("estimated_hours")
				planned_start = item.get("planned_start")
				planned_end = item.get("planned_end")
				
				# Parse planned dates if they're strings
				planned_start_date = None
				planned_end_date = None
				if planned_start:
					try:
						from datetime import datetime
						if isinstance(planned_start, str):
							planned_start_date = datetime.fromisoformat(planned_start.replace('Z', '+00:00')).date()
						else:
							planned_start_date = planned_start.date() if hasattr(planned_start, 'date') else planned_start
					except:
						pass
				if planned_end:
					try:
						from datetime import datetime
						if isinstance(planned_end, str):
							planned_end_date = datetime.fromisoformat(planned_end.replace('Z', '+00:00')).date()
						else:
							planned_end_date = planned_end.date() if hasattr(planned_end, 'date') else planned_end
					except:
						pass
				
				sb_execute(
					"""
					INSERT INTO subtasks (
						task_id, title, description, sequence, estimated_hours,
						planned_start, planned_end
					) VALUES (
						:task_id, :title, :description, :sequence, :estimated_hours,
						:planned_start, :planned_end
					)
					""",
					{
						"task_id": task_id,
						"title": subtask_title[:255],
						"description": description[:1000] if description else None,
						"sequence": int(sequence) if sequence else idx,
						"estimated_hours": float(estimated_hours) if estimated_hours else None,
						"planned_start": planned_start_date,
						"planned_end": planned_end_date,
					}
				)
				created_subtasks += 1
			except Exception as exc:
				print(f"[ai-workspace] subtask insert failed user={current_user.id} subtask_idx={idx} err={exc}")
				import traceback
				traceback.print_exc()
				continue
		
		print(f"[ai-workspace] Successfully saved {created_subtasks}/{len(subtasks)} subtasks to task_id={task_id}")
	else:
		print(f"[ai-workspace] Skipping subtask save - no task_id available")
	
	# Save scheduled subtasks to calendar events
	for item in scheduled:
		start_ts = item.get("start")
		end_ts = item.get("end")
		if not start_ts or not end_ts:
			continue
		title = item.get("title") or assignment_title
		try:
			sb_execute(
				"""
				INSERT INTO events (student_id, module_id, title, start_at, end_at, location)
				VALUES (:student_id, :module_id, :title, :start_at, :end_at, :location)
				""",
				{
					"student_id": current_user.id,
					"module_id": item.get("module_id"),
					"title": title[:255],
					"start_at": start_ts,
					"end_at": end_ts,
					"location": item.get("focus"),
				}
			)
			created_events += 1
		except Exception as exc:
			print(f"[ai-workspace] event insert failed user={current_user.id} err={exc}")
			continue

	# Build success message
	messages = []
	if created_subtasks:
		messages.append(f"Saved {created_subtasks} subtask{'s' if created_subtasks != 1 else ''} to task breakdown.")
	if created_events:
		messages.append(f"Scheduled {created_events} subtask{'s' if created_events != 1 else ''} into your calendar.")
	if unscheduled:
		messages.append(f"{len(unscheduled)} item{'s' if len(unscheduled) != 1 else ''} could not be scheduled due to limited availability.")
	
	if messages:
		flash(" ".join(messages), "success")
	else:
		if unscheduled:
			flash("No suitable time slots were available to schedule those subtasks.", "warning")
		else:
			flash("Unable to save the AI plan. Please try again.", "danger")

	return redirect(url_for("ai_workspace"))

@app.route("/calendar")
@login_required
def calendar_view():
	"""Calendar view of tasks by due date"""
	sql = """
		SELECT t.id, t.title, t.status, t.due_date,
		       t.due_at,
		       t.canvas_assignment_id, m.code AS module_code
		FROM tasks t
		JOIN modules m ON m.id = t.module_id
		WHERE t.student_id = :student_id
		AND t.due_date IS NOT NULL
		ORDER BY t.due_date ASC
		LIMIT 500
	"""
	try:
		rows: List[Dict] = sb_fetch_all(sql, {"student_id": current_user.id})
	except Exception:
		rows = []

	# Reference: ChatGPT (OpenAI) - Calendar Event Time Boundary Handling
	# Date: 2025-11-04
	# Prompt: "Canvas sometimes gives a due_at timestamp or just a due_date. Can you show me how to safely 
	# convert either one into a start and end time in ISO format for my calendar view?"
	# ChatGPT provided a helper block to convert Canvas assignment due information into calendar event start 
	# and end timestamps. When due_at (a full datetime) is available, it is used as the event start, with an 
	# end time five minutes later and clamped to the end of the same day. If only a due_date is available, 
	# the code treats it as an all-day event. This ensures every assignment can be plotted on the calendar, 
	# even when Canvas only supplies date-level precision.
	events: List[Dict] = []
	for r in rows:
		due_at = r.get("due_at")
		if due_at:
			try:
				start_iso = due_at.isoformat()
			except Exception:
				start_iso = str(due_at)
			try:
				from datetime import timedelta
				start_dt = r.get("due_at")
				end_dt = start_dt + timedelta(minutes=5)
				end_of_day = start_dt.replace(hour=23, minute=59, second=59, microsecond=0)
				if end_dt > end_of_day:
					end_dt = end_of_day
				end_iso = end_dt.isoformat()
			except Exception:
				end_iso = start_iso
		else:
			due_date = r.get("due_date")
			start_iso = due_date.strftime("%Y-%m-%d") if hasattr(due_date, "strftime") else str(due_date)
			end_iso = start_iso

		status = r.get("status", "pending")
		if status == "completed":
			color = "#16a34a"
		elif status == "in_progress":
			color = "#f59e0b"
		else:
			color = "#2563eb"

		is_canvas = r.get("canvas_assignment_id") is not None
		prefix = "📚 " if is_canvas else ""

		event = {
			"id": r.get("id"),
			"title": f"{prefix}{r.get('title')} [{r.get('module_code')}]",
			"start": start_iso,
			"end": end_iso,
			"allDay": False if due_at else True,
			"color": color,
			"extendedProps": {
				"status": status,
				"module": r.get("module_code")
			},
			"classNames": ["assignment"]
		}
		events.append(event)

	try:
		rows_ev: List[Dict] = sb_fetch_all(
			"""
			SELECT e.id, e.title, e.start_at, e.end_at, e.location, e.canvas_course_id, e.canvas_event_id, m.code AS module_code
			FROM events e
			LEFT JOIN modules m ON m.id = e.module_id
			WHERE e.student_id = :student_id
			AND e.start_at IS NOT NULL
			AND e.end_at IS NOT NULL
			ORDER BY e.start_at ASC
			LIMIT 1000
			""",
			{"student_id": current_user.id}
		)
	except Exception:
		rows_ev = []

	for ev in rows_ev:
		start_val = ev.get("start_at")
		end_val = ev.get("end_at")
		# Reference: FullCalendar.js Documentation - Event Object
		# https://fullcalendar.io/docs/event-object
		# FullCalendar requires ISO-8601 date strings for timed events
		try:
			start_iso = start_val.isoformat()
		except Exception:
			start_iso = str(start_val)
		try:
			end_iso = end_val.isoformat()
		except Exception:
			end_iso = str(end_val)
		mod = ev.get("module_code")
		title = ev.get("title")
		canvas_course_id = ev.get("canvas_course_id")
		# Manual events (no Canvas course ID) get a different color
		if canvas_course_id is None:
			# Manual event (work, training, etc.) - purple color
			color = "#9333ea"
			prefix = "📅 "
		else:
			# Canvas-synced event (lectures, etc.) - cyan color
			color = "#0ea5e9"
			prefix = "📚 "
		events.append({
			"id": f"event-{ev.get('id')}",
			"title": f"{prefix}{title} [{mod}]" if mod else f"{prefix}{title}",
			"start": start_iso,
			"end": end_iso,
			"allDay": False,
			"color": color,
			"extendedProps": {
				"module": mod,
				"location": ev.get("location")
			}
		})

	try:
		print(f"[calendar] user={current_user.id} events_total={len(events)}")
	except Exception:
		pass

	try:
		user_events = sb_fetch_all(
			"""
			SELECT id, title, start_at, end_at
			FROM events
			WHERE student_id = :student_id
			ORDER BY start_at ASC
			LIMIT 50
			""",
			{"student_id": current_user.id}
		)
	except Exception:
		user_events = []

	return render_template("calendar.html", events=events, user_events=user_events)


@app.route("/calendar/add", methods=["POST"])
@login_required
def add_calendar_event():
	"""Add a manual calendar event (e.g., part-time work, training)"""
	title = request.form.get("title", "").strip()
	start_date = request.form.get("start_date", "").strip()
	start_time = request.form.get("start_time", "").strip()
	end_date = request.form.get("end_date", "").strip()
	end_time = request.form.get("end_time", "").strip()
	location = request.form.get("location", "").strip() or None
	is_recurring = request.form.get("is_recurring") == "on"
	recurrence_end_date_str = request.form.get("recurrence_end_date", "").strip()
	
	if not title:
		flash("Title is required.", "error")
		return redirect(url_for("calendar_view"))
	
	if not start_date or not start_time:
		flash("Start date and time are required.", "error")
		return redirect(url_for("calendar_view"))
	
	if not end_date or not end_time:
		flash("End date and time are required.", "error")
		return redirect(url_for("calendar_view"))
	
	try:
		from datetime import datetime, timedelta, date
		# Combine date and time strings
		start_str = f"{start_date} {start_time}"
		end_str = f"{end_date} {end_time}"
		
		# Parse to datetime (assuming local timezone, convert to UTC if needed)
		try:
			start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
			end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
		except ValueError:
			flash("Invalid date or time format. Use YYYY-MM-DD and HH:MM.", "error")
			return redirect(url_for("calendar_view"))
		
		# Ensure timezone aware
		from datetime import timezone
		if start_dt.tzinfo is None:
			# Convert local time to UTC
			start_dt = start_dt.replace(tzinfo=timezone.utc)
		if end_dt.tzinfo is None:
			end_dt = end_dt.replace(tzinfo=timezone.utc)
		
		if end_dt <= start_dt:
			flash("End time must be after start time.", "error")
			return redirect(url_for("calendar_view"))
		
		# Calculate duration for recurring events
		duration = end_dt - start_dt
		
		# Handle recurring events
		if is_recurring:
			if not recurrence_end_date_str:
				# Default to 3 months from start date if no end date specified
				recurrence_end_date = (start_dt.date() + timedelta(days=90))
			else:
				try:
					recurrence_end_date = datetime.strptime(recurrence_end_date_str, "%Y-%m-%d").date()
				except ValueError:
					flash("Invalid recurrence end date format. Use YYYY-MM-DD.", "error")
					return redirect(url_for("calendar_view"))
			
			# Generate weekly recurring instances
			current_start = start_dt
			current_date = start_dt.date()
			created_count = 0
			
			while current_date <= recurrence_end_date:
				current_end = current_start + duration
				
				# Insert each recurring instance
				sb_execute(
					"""
					INSERT INTO events (student_id, title, start_at, end_at, location, is_recurring, recurrence_end_date)
					VALUES (:student_id, :title, :start_at, :end_at, :location, :is_recurring, :recurrence_end_date)
					""",
					{
						"student_id": current_user.id,
						"title": title[:255],
						"start_at": current_start,
						"end_at": current_end,
						"location": location,
						"is_recurring": True,
						"recurrence_end_date": recurrence_end_date,
					}
				)
				created_count += 1
				
				# Move to next week (same day, same time)
				current_start = current_start + timedelta(weeks=1)
				current_date = current_start.date()
			
			flash(f"Recurring event '{title}' added - {created_count} instances created until {recurrence_end_date.strftime('%d/%m/%Y')}.", "success")
		else:
			# Single event (non-recurring)
			sb_execute(
				"""
				INSERT INTO events (student_id, title, start_at, end_at, location, is_recurring)
				VALUES (:student_id, :title, :start_at, :end_at, :location, :is_recurring)
				""",
				{
					"student_id": current_user.id,
					"title": title[:255],
					"start_at": start_dt,
					"end_at": end_dt,
					"location": location,
					"is_recurring": False,
				}
			)
			flash(f"Event '{title}' added to your calendar.", "success")
	except Exception as exc:
		print(f"[calendar] add event failed user={current_user.id} err={exc}")
		flash(f"Failed to add event: {str(exc)}", "danger")
	
	return redirect(url_for("calendar_view"))


@app.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id: int):
	try:
		result = sb_execute(
			"DELETE FROM events WHERE id = :id AND student_id = :student_id",
			{"id": event_id, "student_id": current_user.id}
		)
		if result == 0:
			flash("Event not found or already deleted.", "warning")
		else:
			flash("Event removed from your calendar.", "success")
	except Exception as exc:
		print(f"[events] delete failed user={current_user.id} event={event_id} err={exc}")
		flash("Failed to delete the event. Please try again.", "danger")
	return redirect(url_for("calendar_view"))


@app.route("/debug/calendar")
@login_required
def debug_calendar():
	"""Return counts of tasks and events for current user for troubleshooting"""
	counts = {"tasks": 0, "events": 0}
	try:
		row = sb_fetch_one("SELECT COUNT(*) AS c FROM tasks WHERE student_id = :sid", {"sid": current_user.id})
		counts["tasks"] = row["c"] if row else 0
		rowe = sb_fetch_one("SELECT COUNT(*) AS c FROM events WHERE student_id = :sid", {"sid": current_user.id})
		counts["events"] = rowe["c"] if rowe else 0
	except Exception as exc:
		return jsonify({"ok": False, "error": str(exc)}), 500
	return jsonify({"ok": True, "counts": counts}), 200


@app.route("/debug/events")
@login_required
def debug_events():
	"""Return next 50 timed events for troubleshooting"""
	try:
		rows = sb_fetch_all(
			"""
			SELECT id, title, start_at, end_at, canvas_course_id
			FROM events
			WHERE student_id = :sid
			AND start_at >= NOW() - INTERVAL '14 days'
			ORDER BY start_at ASC
			LIMIT 50
			""",
			{"sid": current_user.id}
		)
		def to_iso(x):
			try:
				return x.isoformat()
			except Exception:
				return str(x)
		items = [
			{
				"id": r.get("id"),
				"title": r.get("title"),
				"start_at": to_iso(r.get("start_at")),
				"end_at": to_iso(r.get("end_at")),
				"canvas_course_id": r.get("canvas_course_id"),
			}
			for r in rows
		]
		return jsonify({"ok": True, "events": items}), 200
	except Exception as exc:
		return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/analytics")
@login_required
def analytics():
	charts_dir = os.path.join(app.static_folder or "static", "charts")
	os.makedirs(charts_dir, exist_ok=True)

	cutoff_date = datetime.now().date()

	try:
		status_overview = sb_fetch_all("""
			SELECT status, COUNT(id) as count
			FROM tasks
			WHERE student_id = :student_id
			  AND (due_date IS NULL OR due_date >= :cutoff_date)
			GROUP BY status
		""", {"student_id": current_user.id, "cutoff_date": cutoff_date})
		
		# Reference: ChatGPT (OpenAI) - Data Extraction with Generator Expressions
		# Date: 2025-10-18
		# Prompt: "I have a list of dictionaries with 'status' and 'count' keys. I need to extract 
		# counts for specific statuses (completed, in_progress, pending) and default to 0 if not found. 
		# Can you show me how to use next() with generator expressions and default values?"
		# ChatGPT provided the pattern using next() with generator expressions to extract values 
		# from a list of dictionaries, with default values if the status is not found.
		total_tasks = sum(s['count'] for s in status_overview)
		completed_tasks = next((s['count'] for s in status_overview if s['status'] == 'completed'), 0)
		in_progress_tasks = next((s['count'] for s in status_overview if s['status'] == 'in_progress'), 0)
		pending_tasks = next((s['count'] for s in status_overview if s['status'] == 'pending'), 0)
		
		# Reference: PostgreSQL Documentation - Date/Time Functions
		# https://www.postgresql.org/docs/current/functions-datetime.html#FUNCTIONS-DATETIME-TRUNC
		# DATE_TRUNC groups dates by week for weekly analytics
		weekly_data = sb_fetch_all("""
			SELECT 
				DATE_TRUNC('week', completed_at) as week,
				COUNT(*) as completions
			FROM tasks
			WHERE student_id = :student_id 
			  AND status = 'completed' 
			  AND completed_at IS NOT NULL
			  AND (due_date IS NULL OR due_date >= :cutoff_date)
			GROUP BY DATE_TRUNC('week', completed_at)
			ORDER BY week
		""", {"student_id": current_user.id, "cutoff_date": cutoff_date})
		
		max_weekly_completions = max((w['completions'] for w in weekly_data), default=1)
		
		# Reference: ChatGPT (OpenAI) - Analytics SQL with Conditional Aggregation
		# Date: 2025-10-18
		# Prompt: "I need SQL queries for analytics in PostgreSQL. I need to count completed tasks 
		# that were on-time (completed_at <= due_date) vs late. Can you provide the SQL with proper 
		# CASE WHEN statements for conditional counting?"
		# ChatGPT provided the SQL query using CASE WHEN for conditional aggregation to distinguish 
		# between on-time and late completions.
		completion_stats = sb_fetch_one("""
			SELECT 
				COUNT(*) as total_completed,
				SUM(CASE WHEN completed_at <= due_date THEN 1 ELSE 0 END) as on_time,
				SUM(CASE WHEN completed_at > due_date THEN 1 ELSE 0 END) as late
			FROM tasks 
			WHERE student_id = :student_id 
			  AND status = 'completed' 
			  AND completed_at IS NOT NULL
			  AND (due_date IS NULL OR due_date >= :cutoff_date)
		""", {"student_id": current_user.id, "cutoff_date": cutoff_date})
		
		if completion_stats and completion_stats['total_completed'] > 0:
			on_time_percentage = round((completion_stats['on_time'] / completion_stats['total_completed']) * 100, 1)
			late_percentage = round((completion_stats['late'] / completion_stats['total_completed']) * 100, 1)
			completion_stats['on_time_percentage'] = on_time_percentage
			completion_stats['late_percentage'] = late_percentage
		
		# Reference: ChatGPT (OpenAI) - Module Performance Analytics with NULLIF
		# Date: 2025-10-18
		# Prompt: "I need to calculate completion rates per module using LEFT JOIN in PostgreSQL, 
		# handling division by zero with NULLIF. The query should group by module and only show 
		# modules that have tasks. Can you provide the SQL with proper NULLIF for safe division?"
		# ChatGPT provided the SQL query with LEFT JOIN, NULLIF to prevent division by zero, 
		# and HAVING clause to filter modules with tasks.
		module_stats = sb_fetch_all("""
			SELECT 
				m.code as module_code,
				COUNT(t.id) as total_tasks,
				SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed,
				ROUND(
					(SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(t.id), 0)) * 100, 
					1
				) as completion_rate
			FROM modules m
			LEFT JOIN tasks t ON m.id = t.module_id 
				AND t.student_id = :student_id
				AND (t.due_date IS NULL OR t.due_date >= :cutoff_date)
			GROUP BY m.id, m.code
			HAVING COUNT(t.id) > 0
			ORDER BY completion_rate DESC
		""", {"student_id": current_user.id, "cutoff_date": cutoff_date})
		
		# 1. Grade Performance Analytics (using Canvas scores)

		grade_performance = sb_fetch_all("""
			SELECT 
				m.code as module_code,
				COUNT(t.id) as graded_count,
				AVG(CASE 
					WHEN t.canvas_possible > 0 
					THEN (t.canvas_score::numeric / t.canvas_possible::numeric) * 100 
					ELSE NULL 
				END) as avg_percentage,
				AVG(t.canvas_score) as avg_score,
				AVG(t.canvas_possible) as avg_possible
			FROM modules m
			LEFT JOIN tasks t ON m.id = t.module_id 
				AND t.student_id = :student_id
				AND t.canvas_score IS NOT NULL
			GROUP BY m.id, m.code
			HAVING COUNT(t.id) > 0
			ORDER BY avg_percentage DESC NULLS LAST
		""", {"student_id": current_user.id})
		
		# Overall grade stats
		overall_grade_stats = sb_fetch_one("""
			SELECT 
				COUNT(*) as total_graded,
				AVG(CASE 
					WHEN canvas_possible > 0 
					THEN (canvas_score::numeric / canvas_possible::numeric) * 100 
					ELSE NULL 
				END) as overall_avg_percentage
			FROM tasks 
			WHERE student_id = :student_id 
			  AND canvas_score IS NOT NULL
		""", {"student_id": current_user.id})
		
		# Predicted overall grade (weighted by assignment weights)

		predicted_grade = sb_fetch_one("""
			SELECT 
				SUM(CASE 
					WHEN canvas_possible > 0 AND weight_percentage IS NOT NULL
					THEN ((canvas_score::numeric / canvas_possible::numeric) * 100) * (weight_percentage::numeric / 100)
					ELSE NULL
				END) as weighted_grade_sum,
				SUM(CASE 
					WHEN weight_percentage IS NOT NULL AND canvas_score IS NOT NULL
					THEN weight_percentage
					ELSE NULL
				END) as total_weight
			FROM tasks 
			WHERE student_id = :student_id 
			  AND canvas_score IS NOT NULL
			  AND weight_percentage IS NOT NULL
		""", {"student_id": current_user.id})
		
		# Individual graded assignments with scores
		individual_grades = sb_fetch_all("""
			SELECT 
				t.id,
				t.title,
				m.code as module_code,
				t.canvas_score,
				t.canvas_possible,
				CASE 
					WHEN t.canvas_possible > 0 
					THEN ROUND((t.canvas_score::numeric / t.canvas_possible::numeric) * 100, 1)
					ELSE NULL 
				END as percentage,
				t.canvas_graded_at,
				t.weight_percentage,
				t.due_date
			FROM tasks t
			LEFT JOIN modules m ON t.module_id = m.id
			WHERE t.student_id = :student_id 
			  AND t.canvas_score IS NOT NULL
			ORDER BY t.canvas_graded_at DESC NULLS LAST, t.due_date DESC NULLS LAST
		""", {"student_id": current_user.id})
		
		# 3. Priority & Weighting Analytics
		# High priority tasks (high weight + due soon)
		high_priority_tasks = sb_fetch_all("""
			SELECT 
				t.id, t.title, t.status, t.due_date, t.due_at,
				t.weight_percentage, m.code as module_code,
				CASE 
					WHEN t.due_at IS NOT NULL 
					THEN EXTRACT(EPOCH FROM (t.due_at - NOW())) / 3600
					WHEN t.due_date IS NOT NULL
					THEN EXTRACT(EPOCH FROM (t.due_date::timestamp - NOW())) / 3600
					ELSE NULL
				END as hours_remaining
			FROM tasks t
			JOIN modules m ON m.id = t.module_id
			WHERE t.student_id = :student_id
			  AND t.status != 'completed'
			  AND (t.due_date IS NULL OR t.due_date >= :cutoff_date)
			ORDER BY 
				t.weight_percentage DESC NULLS LAST,
				t.due_at ASC NULLS LAST,
				t.due_date ASC NULLS LAST
			LIMIT 10
		""", {"student_id": current_user.id, "cutoff_date": cutoff_date})
		
		# Calculate priority scores for high priority tasks
		from services.analytics import calculate_priority, normalise_due_datetime
		from datetime import timezone
		now = datetime.now(timezone.utc)
		high_priority_with_scores = []
		for task in high_priority_tasks:
			due_at = normalise_due_datetime(task, now)
			if due_at:
				hours_remaining = (due_at - now).total_seconds() / 3600
				# Convert weight_percentage to float if it's a Decimal
				weight = task.get('weight_percentage')
				if weight is not None:
					try:
						weight = float(weight)
					except (TypeError, ValueError):
						weight = None
				priority = calculate_priority(
					weight, 
					max(0, hours_remaining)
				)
				task['priority'] = priority
				high_priority_with_scores.append(task)
		
		high_priority_with_scores.sort(key=lambda x: x.get('priority', 0), reverse=True)
		
		# Weight distribution stats
		weight_stats = sb_fetch_one("""
			SELECT 
				COUNT(*) as total_with_weight,
				AVG(weight_percentage) as avg_weight,
				MAX(weight_percentage) as max_weight,
				MIN(weight_percentage) as min_weight
			FROM tasks
			WHERE student_id = :student_id
			  AND weight_percentage IS NOT NULL
			  AND (due_date IS NULL OR due_date >= :cutoff_date)
		""", {"student_id": current_user.id, "cutoff_date": cutoff_date})
		
		# 7. Actionable Insights
		# Focus module (lowest completion rate)
		focus_module = next((m for m in module_stats if m['completion_rate'] < 100), None)
		
		# At-risk assignments (high weight + due within 7 days)
		at_risk_assignments = sb_fetch_all("""
			SELECT 
				t.id, t.title, t.status, t.due_date, t.due_at,
				t.weight_percentage, m.code as module_code,
				EXTRACT(EPOCH FROM (t.due_date::timestamp - NOW())) / 86400 as days_remaining
			FROM tasks t
			JOIN modules m ON m.id = t.module_id
			WHERE t.student_id = :student_id
			  AND t.status != 'completed'
			  AND t.weight_percentage IS NOT NULL
			  AND t.weight_percentage >= 10
			  AND t.due_date >= :cutoff_date
			  AND t.due_date <= :cutoff_date + INTERVAL '7 days'
			ORDER BY t.weight_percentage DESC, t.due_date ASC
			LIMIT 5
		""", {"student_id": current_user.id, "cutoff_date": cutoff_date})
		
		# Overdue count by module
		overdue_by_module = sb_fetch_all("""
			SELECT 
				m.code as module_code,
				COUNT(t.id) as overdue_count
			FROM modules m
			LEFT JOIN tasks t ON m.id = t.module_id 
				AND t.student_id = :student_id
				AND t.status != 'completed'
				AND t.due_date < :cutoff_date
				AND (t.due_date IS NULL OR t.due_date >= :cutoff_date - INTERVAL '90 days')
			GROUP BY m.id, m.code
			HAVING COUNT(t.id) > 0
			ORDER BY overdue_count DESC
		""", {"student_id": current_user.id, "cutoff_date": cutoff_date})
		
		# Calculate predicted grade percentage
		predicted_grade_pct = None
		if predicted_grade and predicted_grade.get('weighted_grade_sum') and predicted_grade.get('total_weight'):
			if predicted_grade['total_weight'] > 0:
				predicted_grade_pct = round((predicted_grade['weighted_grade_sum'] / predicted_grade['total_weight']), 1)
		
		analytics_data = {
			'total_tasks': total_tasks,
			'completed_tasks': completed_tasks,
			'in_progress_tasks': in_progress_tasks,
			'pending_tasks': pending_tasks,
			'weekly_data': weekly_data,
			'max_weekly_completions': max_weekly_completions,
			'completion_stats': completion_stats,
			'module_stats': module_stats,
			# Grade Performance
			'grade_performance': grade_performance,
			'overall_grade_stats': overall_grade_stats,
			'predicted_grade_pct': predicted_grade_pct,
			'individual_grades': individual_grades,
			# Priority & Weighting
			'high_priority_tasks': high_priority_with_scores[:5],
			'weight_stats': weight_stats,
			# Actionable Insights
			'focus_module': focus_module,
			'at_risk_assignments': at_risk_assignments,
			'overdue_by_module': overdue_by_module
		}
		
	except Exception as e:
		print(f"Error fetching analytics data: {e}")
		import traceback
		traceback.print_exc()
		analytics_data = {
			'total_tasks': 0,
			'completed_tasks': 0,
			'in_progress_tasks': 0,
			'pending_tasks': 0,
			'weekly_data': [],
			'max_weekly_completions': 1,
			'completion_stats': None,
			'module_stats': [],
			'grade_performance': [],
			'overall_grade_stats': None,
			'predicted_grade_pct': None,
			'individual_grades': [],
			'high_priority_tasks': [],
			'weight_stats': None,
			'focus_module': None,
			'at_risk_assignments': [],
			'overdue_by_module': []
		}

	return render_template("analytics.html", analytics=analytics_data)


@app.route("/study-planner", methods=["GET", "POST"])
@login_required
def study_planner():
	"""AI Study Planner - Generate personalized study recommendations"""
	# Reference: ChatGPT (OpenAI) - Study Planner Prompt Context
	# Date: 2026-01-22
	# Prompt: "I need to summarize tasks and progress into a compact prompt for study
	# recommendations. Can you help structure the summary text?"
	# ChatGPT provided the prompt context structure.
	recommendations: Optional[str] = None
	error: Optional[str] = None
	
	# Fetch tasks data
	try:
		task_rows = sb_fetch_all(
			"""
			SELECT t.id, t.title, t.status, t.due_date, t.due_at, t.weight_percentage,
			       m.code AS module_code
			FROM tasks t
			LEFT JOIN modules m ON m.id = t.module_id
			WHERE t.student_id = :student_id
			ORDER BY t.due_at NULLS LAST, t.due_date NULLS LAST
			""",
			{"student_id": current_user.id}
		)
	except Exception as exc:
		print(f"[study-planner] failed to load tasks user={current_user.id} error={exc}")
		task_rows = []
	
	# Build progress summary using assess_progress
	progress = assess_progress(task_rows)
	
	# Build tasks summary
	tasks_summary_lines = []
	if task_rows:
		pending = [t for t in task_rows if t.get("status") == "pending"]
		in_progress = [t for t in task_rows if t.get("status") == "in_progress"]
		completed = [t for t in task_rows if t.get("status") == "completed"]
		
		tasks_summary_lines.append(f"Total tasks: {len(task_rows)}")
		tasks_summary_lines.append(f"Pending: {len(pending)}, In Progress: {len(in_progress)}, Completed: {len(completed)}")
		
		if pending or in_progress:
			tasks_summary_lines.append("\nUpcoming/Active tasks:")
			for task in (pending + in_progress)[:10]:  # Limit to 10 for prompt size
				module = task.get("module_code") or "No module"
				due = task.get("due_at") or task.get("due_date") or "No due date"
				weight = task.get("weight_percentage")
				weight_str = f" ({weight}% weight)" if weight else ""
				tasks_summary_lines.append(f"- {task.get('title')} ({module}){weight_str} - Due: {due}")
	else:
		tasks_summary_lines.append("No tasks found.")
	
	tasks_summary = "\n".join(tasks_summary_lines)
	
	# Build progress summary
	progress_summary_lines = [
		f"Status: {progress.get('status', 'unknown').replace('_', ' ').title()}",
		f"Overdue tasks: {progress.get('overdue', 0)}",
		f"Due in 48 hours: {progress.get('nearly_due', 0)}",
		f"Completed this week: {progress.get('completed_this_week', 0)}"
	]
	progress_summary = "\n".join(progress_summary_lines)
	
	# Generate recommendations if POST request
	if request.method == "POST":
		try:
			chatgpt = get_chatgpt_service()
			recommendations = chatgpt.get_study_recommendations(
				tasks_summary=tasks_summary,
				progress_summary=progress_summary
			)
		except ChatGPTClientError as exc:
			error = f"Failed to generate recommendations: {str(exc)}"
			print(f"[study-planner] ChatGPT error: {exc}")
		except Exception as exc:
			error = f"Unexpected error: {str(exc)}"
			print(f"[study-planner] Unexpected error: {exc}")
			import traceback
			traceback.print_exc()
	
	return render_template(
		"study_planner.html",
		recommendations=recommendations,
		error=error,
		tasks_summary=tasks_summary,
		progress_summary=progress_summary
	)


@app.route("/course-bot", methods=["GET", "POST"])
@login_required
def course_bot():
	"""AI Course Bot - Ask questions based on uploaded course materials."""
	# Reference: ChatGPT (OpenAI) - Course Bot Upload + Q&A Flow
	# Date: 2026-01-22
	# Prompt: "I want a course bot that stores uploaded materials and answers questions using
	# only those sources. Can you outline the flow and storage steps?"
	# ChatGPT provided the upload + Q&A orchestration pattern.
	error: Optional[str] = None
	success_message: Optional[str] = None

	if request.method == "POST":
		action = request.form.get("action", "").strip()
		if action == "upload_course_doc":
			file_storage = request.files.get("course_file")
			if not file_storage or not file_storage.filename:
				error = "Please upload a course file."
			else:
				filename = file_storage.filename
				try:
					payload = file_storage.read()
					if not payload:
						raise ValueError("The uploaded file was empty.")
					if len(payload) > _AI_MAX_UPLOAD_BYTES:
						raise ValueError("The file is larger than 4 MB. Upload a smaller file.")

					extracted_text = _extract_text_from_brief(filename, payload)
					if not extracted_text or not extracted_text.strip():
						raise ValueError("Could not extract text from the uploaded file.")

					uploads_dir = os.path.join(app.root_path, "uploads", "course_packs")
					os.makedirs(uploads_dir, exist_ok=True)
					timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
					safe_filename = f"{current_user.id}_{timestamp}_{filename}"
					filepath = os.path.join(uploads_dir, safe_filename)
					with open(filepath, "wb") as f:
						f.write(payload)

					sb_execute(
						"""
						INSERT INTO course_documents (
							student_id, filename, filepath, extracted_text, uploaded_at
						) VALUES (
							:student_id, :filename, :filepath, :extracted_text, NOW()
						)
						""",
						{
							"student_id": current_user.id,
							"filename": filename,
							"filepath": filepath,
							"extracted_text": extracted_text,
						}
					)
					success_message = "Course material uploaded successfully."
				except ValueError as exc:
					error = str(exc)
					print(f"[course-bot] upload validation error user={current_user.id} err={exc}")
				except Exception as exc:
					error = f"Failed to process upload: {str(exc)}"
					print(f"[course-bot] upload failed user={current_user.id} err={exc}")
					import traceback
					traceback.print_exc()
		elif action == "clear_course_docs":
			try:
				rows = sb_fetch_all(
					"""
					SELECT id, filepath
					FROM course_documents
					WHERE student_id = :student_id
					""",
					{"student_id": current_user.id}
				)
				sb_execute(
					"""
					DELETE FROM course_documents
					WHERE student_id = :student_id
					""",
					{"student_id": current_user.id}
				)
				for row in rows:
					filepath = row.get("filepath")
					if filepath and os.path.exists(filepath):
						try:
							os.remove(filepath)
						except Exception:
							pass
				success_message = "Uploaded materials cleared."
			except Exception as exc:
				error = f"Failed to clear materials: {str(exc)}"
				print(f"[course-bot] clear docs failed user={current_user.id} err={exc}")
		elif action == "ask_course_question":
			question = request.form.get("question", "").strip()
			if not question:
				error = "Please enter a question."
			else:
				try:
					documents = sb_fetch_all(
						"""
						SELECT id, filename, extracted_text, uploaded_at
						FROM course_documents
						WHERE student_id = :student_id
						ORDER BY uploaded_at DESC
						""",
						{"student_id": current_user.id}
					)
					if not documents:
						error = "Upload course materials before asking a question."
					else:
						sources = _select_course_materials(documents, question)
						if not sources:
							error = "No relevant course materials found for this question."
						else:
							service = get_chatgpt_service()
							response = service.answer_course_question(
								question=question,
								sources=sources
							)
							citations_payload = [
								{"source": c.source, "quote": c.quote} for c in response.citations
							]
							sb_execute(
								"""
								INSERT INTO course_bot_history (
									student_id, question, answer, citations, asked_at
								) VALUES (
									:student_id, :question, :answer, :citations, NOW()
								)
								""",
								{
									"student_id": current_user.id,
									"question": question,
									"answer": response.answer,
									"citations": json.dumps(citations_payload),
								}
							)
							success_message = "Answer generated. See the history below."
				except ChatGPTClientError as exc:
					error = f"Failed to answer question: {str(exc)}"
					print(f"[course-bot] ChatGPT error user={current_user.id} err={exc}")
				except Exception as exc:
					error = f"Unexpected error: {str(exc)}"
					print(f"[course-bot] Unexpected error user={current_user.id} err={exc}")
					import traceback
					traceback.print_exc()
		elif action == "clear_course_history":
			try:
				sb_execute(
					"""
					DELETE FROM course_bot_history
					WHERE student_id = :student_id
					""",
					{"student_id": current_user.id}
				)
				success_message = "Q&A history cleared."
			except Exception as exc:
				error = f"Failed to clear history: {str(exc)}"
				print(f"[course-bot] clear history failed user={current_user.id} err={exc}")
		else:
			error = "Invalid request."

	docs = []
	history = []
	try:
		docs = sb_fetch_all(
			"""
			SELECT id, filename, uploaded_at
			FROM course_documents
			WHERE student_id = :student_id
			ORDER BY uploaded_at DESC
			""",
			{"student_id": current_user.id}
		)
	except Exception as exc:
		print(f"[course-bot] failed to load docs user={current_user.id} error={exc}")

	try:
		history = sb_fetch_all(
			"""
			SELECT id, question, answer, citations, asked_at
			FROM course_bot_history
			WHERE student_id = :student_id
			ORDER BY asked_at DESC
			LIMIT 20
			""",
			{"student_id": current_user.id}
		)
		for item in history:
			answer_text = item.get("answer")
			item["qa_pairs"] = []
			if isinstance(answer_text, str) and answer_text.strip().startswith("["):
				try:
					parsed = json.loads(answer_text)
					if isinstance(parsed, list) and all(isinstance(entry, str) for entry in parsed):
						item["answer"] = "\n".join(parsed)
				except Exception:
					pass
			elif isinstance(answer_text, str) and "['" in answer_text and "]" in answer_text:
				try:
					import ast
					parsed = ast.literal_eval(answer_text)
					if isinstance(parsed, list) and all(isinstance(entry, str) for entry in parsed):
						item["answer"] = "\n".join(parsed)
				except Exception:
					pass
			answer_text = item.get("answer")
			if isinstance(answer_text, str) and "| Answer:" in answer_text:
				lines = [line.strip() for line in answer_text.splitlines() if line.strip()]
				for line in lines:
					if "| Answer:" not in line:
						continue
					parts = line.split("| Answer:", 1)
					question_part = parts[0].replace("Q:", "").strip()
					answer_part = parts[1]
					expl = ""
					if "| Explanation:" in answer_part:
						answer_value, expl = answer_part.split("| Explanation:", 1)
						answer_value = answer_value.strip()
						expl = expl.strip()
					else:
						answer_value = answer_part.strip()
					item["qa_pairs"].append({
						"question": question_part,
						"answer": answer_value,
						"explanation": expl,
					})
			raw = item.get("citations")
			try:
				item["citations_list"] = json.loads(raw) if raw else []
			except Exception:
				item["citations_list"] = []
	except Exception as exc:
		print(f"[course-bot] failed to load history user={current_user.id} error={exc}")

	return render_template(
		"course_bot.html",
		docs=docs,
		history=history,
		error=error,
		success_message=success_message
	)


@app.route("/assignment-review", methods=["GET", "POST"])
@login_required
def assignment_review():
	"""AI Assignment Review & Grading - Standalone page"""
	error: Optional[str] = None
	success_message: Optional[str] = None
	
	# Fetch user's tasks for optional linking
	tasks = []
	try:
		tasks = sb_fetch_all(
			"""
			SELECT t.id, t.title, m.code AS module_code
			FROM tasks t
			LEFT JOIN modules m ON m.id = t.module_id
			WHERE t.student_id = :student_id
			ORDER BY t.due_at NULLS LAST, t.due_date NULLS LAST, t.title
			LIMIT 50
			""",
			{"student_id": current_user.id}
		)
	except Exception as exc:
		print(f"[assignment-review] failed to load tasks user={current_user.id} error={exc}")
	
	# Fetch all reviews for the user
	reviews = []
	try:
		reviews = sb_fetch_all(
			"""
			SELECT ar.id, ar.task_id, ar.filename, ar.ai_feedback, ar.ai_score_estimate, 
			       ar.ai_possible_score, ar.reviewed_at,
			       t.title AS task_title, m.code AS module_code
			FROM assignment_reviews ar
			LEFT JOIN tasks t ON t.id = ar.task_id
			LEFT JOIN modules m ON m.id = t.module_id
			WHERE ar.student_id = :student_id
			ORDER BY ar.reviewed_at DESC
			LIMIT 20
			""",
			{"student_id": current_user.id}
		)
	except Exception as exc:
		print(f"[assignment-review] failed to load reviews user={current_user.id} error={exc}")
	
	if request.method == "POST":
		# Get assignment text from file or text input
		assignment_text: Optional[str] = None
		filename: Optional[str] = None
		filepath: Optional[str] = None
		task_id: Optional[int] = None
		
		# Get optional task_id
		task_id_str = request.form.get("task_id", "").strip()
		if task_id_str:
			try:
				task_id = int(task_id_str)
			except ValueError:
				pass
		
		# Check for file upload
		file_storage = request.files.get("assignment_file")
		if file_storage and file_storage.filename:
			filename = file_storage.filename
			try:
				payload = file_storage.read()
				if not payload:
					raise ValueError("The uploaded file was empty.")
				if len(payload) > _AI_MAX_UPLOAD_BYTES:
					raise ValueError("The file is larger than 4 MB. Upload a smaller file.")
				
				assignment_text = _extract_text_from_brief(filename, payload)
				if not assignment_text:
					raise ValueError("Could not extract text from the uploaded file.")
				
				# Store file on filesystem
				uploads_dir = os.path.join(app.root_path, "uploads", "assignments")
				os.makedirs(uploads_dir, exist_ok=True)
				timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
				safe_filename = f"{current_user.id}_{timestamp}_{filename}"
				filepath = os.path.join(uploads_dir, safe_filename)
				with open(filepath, "wb") as f:
					f.write(payload)
			except ValueError as exc:
				error = str(exc)
				print(f"[assignment-review] file validation error user={current_user.id} err={exc}")
			except Exception as exc:
				error = f"Failed to process uploaded file: {str(exc)}"
				print(f"[assignment-review] file processing failed user={current_user.id} err={exc}")
				import traceback
				traceback.print_exc()
		
		# Check for text input
		if not assignment_text:
			assignment_text = request.form.get("assignment_text", "").strip()
		
		if not assignment_text:
			error = "Please provide assignment content by uploading a file or pasting text."
		
		# Get assignment title and brief (optional)
		assignment_title = "Assignment"
		assignment_brief: Optional[str] = None
		
		# Get brief/rubric from form input (takes priority)
		assignment_brief = request.form.get("assignment_brief", "").strip() or None
		
		if task_id:
			task = sb_fetch_one(
				"""
				SELECT t.id, t.title, t.description, t.student_id
				FROM tasks t
				WHERE t.id = :task_id AND t.student_id = :student_id
				""",
				{"task_id": task_id, "student_id": current_user.id}
			)
			if task:
				assignment_title = task.get("title", "Assignment")
				# Use task description as brief if no form input provided
				if not assignment_brief:
					assignment_brief = task.get("description")
		
		if not error:
			try:
				service = get_chatgpt_service()
				review_result = service.review_and_grade_assignment(
					assignment_text=assignment_text,
					task_title=assignment_title,
					assignment_brief=assignment_brief
				)
				
				# Format comprehensive feedback
				feedback_parts = [review_result.feedback]
				if review_result.strengths:
					feedback_parts.append("\n\n**Strengths:**\n" + "\n".join(f"• {s}" for s in review_result.strengths))
				if review_result.weaknesses:
					feedback_parts.append("\n\n**Areas for Improvement:**\n" + "\n".join(f"• {w}" for w in review_result.weaknesses))
				if review_result.suggestions:
					feedback_parts.append("\n\n**Suggestions:**\n" + "\n".join(f"• {s}" for s in review_result.suggestions))
				comprehensive_feedback = "\n".join(feedback_parts)
				
				# Save review to database
				sb_execute(
					"""
					INSERT INTO assignment_reviews (
						task_id, student_id, filename, filepath, original_text,
						ai_feedback, ai_score_estimate, ai_possible_score, reviewed_at
					) VALUES (
						:task_id, :student_id, :filename, :filepath, :original_text,
						:ai_feedback, :ai_score_estimate, :ai_possible_score, NOW()
					)
					""",
					{
						"task_id": task_id,
						"student_id": current_user.id,
						"filename": filename,
						"filepath": filepath,
						"original_text": assignment_text[:5000] if assignment_text else None,
						"ai_feedback": comprehensive_feedback,
						"ai_score_estimate": review_result.score_estimate,
						"ai_possible_score": review_result.possible_score,
					}
				)
				success_message = "Assignment reviewed successfully!"
				# Reload reviews
				try:
					reviews = sb_fetch_all(
						"""
						SELECT ar.id, ar.task_id, ar.filename, ar.ai_feedback, ar.ai_score_estimate, 
						       ar.ai_possible_score, ar.reviewed_at,
						       t.title AS task_title, m.code AS module_code
						FROM assignment_reviews ar
						LEFT JOIN tasks t ON t.id = ar.task_id
						LEFT JOIN modules m ON m.id = t.module_id
						WHERE ar.student_id = :student_id
						ORDER BY ar.reviewed_at DESC
						LIMIT 20
						""",
						{"student_id": current_user.id}
					)
				except Exception:
					pass
			except ChatGPTClientError as exc:
				error = f"AI review failed: {str(exc)}"
				print(f"[assignment-review] ChatGPT error user={current_user.id} err={exc}")
			except Exception as exc:
				error = f"Unexpected error: {str(exc)}"
				print(f"[assignment-review] Unexpected error user={current_user.id} err={exc}")
				import traceback
				traceback.print_exc()
	
	return render_template(
		"assignment_review.html",
		tasks=tasks,
		reviews=reviews,
		error=error,
		success_message=success_message
	)


@app.route("/reviews")
@login_required
def reviews_history():
	page_str = request.args.get("page", "1").strip()
	try:
		page = max(1, int(page_str))
	except ValueError:
		page = 1
	per_page = 20
	offset = (page - 1) * per_page

	count_row = sb_fetch_one(
		"SELECT COUNT(*) as count FROM assignment_reviews WHERE student_id = :student_id",
		{"student_id": current_user.id}
	)
	total = count_row["count"] if count_row else 0
	total_pages = max(1, (total + per_page - 1) // per_page)

	reviews = sb_fetch_all(
		"""
		SELECT ar.id, ar.filename, ar.ai_feedback, ar.ai_score_estimate, ar.ai_possible_score, ar.reviewed_at,
		       t.title AS task_title, m.code AS module_code
		FROM assignment_reviews ar
		LEFT JOIN tasks t ON t.id = ar.task_id
		LEFT JOIN modules m ON m.id = t.module_id
		WHERE ar.student_id = :student_id
		ORDER BY ar.reviewed_at DESC
		LIMIT :limit OFFSET :offset
		""",
		{"student_id": current_user.id, "limit": per_page, "offset": offset}
	)

	return render_template(
		"reviews_history.html",
		reviews=reviews,
		page=page,
		total_pages=total_pages
	)


@app.route("/subtasks")
@login_required
def subtasks_history():
	page_str = request.args.get("page", "1").strip()
	try:
		page = max(1, int(page_str))
	except ValueError:
		page = 1
	per_page = 20
	offset = (page - 1) * per_page

	count_row = sb_fetch_one(
		"""
		SELECT COUNT(*) as count
		FROM subtasks s
		JOIN tasks t ON t.id = s.task_id
		WHERE t.student_id = :student_id
		""",
		{"student_id": current_user.id}
	)
	total = count_row["count"] if count_row else 0
	total_pages = max(1, (total + per_page - 1) // per_page)

	subtasks = sb_fetch_all(
		"""
		SELECT s.id, s.title, s.description, s.sequence, s.estimated_hours,
		       s.planned_start, s.planned_end, s.is_completed, s.completed_at,
		       t.title AS task_title, m.code AS module_code
		FROM subtasks s
		JOIN tasks t ON t.id = s.task_id
		LEFT JOIN modules m ON m.id = t.module_id
		WHERE t.student_id = :student_id
		ORDER BY s.created_at DESC
		LIMIT :limit OFFSET :offset
		""",
		{"student_id": current_user.id, "limit": per_page, "offset": offset}
	)

	return render_template(
		"subtasks_history.html",
		subtasks=subtasks,
		page=page,
		total_pages=total_pages
	)


@app.route("/lecturer-messages")
@login_required
def lecturer_messages_history():
	page_str = request.args.get("page", "1").strip()
	try:
		page = max(1, int(page_str))
	except ValueError:
		page = 1
	per_page = 20
	offset = (page - 1) * per_page

	count_row = sb_fetch_one(
		"""
		SELECT COUNT(*) as count
		FROM lecturer_messages
		WHERE student_id = :student_id
		""",
		{"student_id": current_user.id}
	)
	total = count_row["count"] if count_row else 0
	total_pages = max(1, (total + per_page - 1) // per_page)

	messages = sb_fetch_all(
		"""
		SELECT lm.id, lm.subject, lm.message, lm.sent_at, lm.email_status, lm.email_error,
		       l.name AS lecturer_name, l.module_code
		FROM lecturer_messages lm
		LEFT JOIN lecturers l ON l.id = lm.lecturer_id
		WHERE lm.student_id = :student_id
		ORDER BY lm.sent_at DESC
		LIMIT :limit OFFSET :offset
		""",
		{"student_id": current_user.id, "limit": per_page, "offset": offset}
	)

	return render_template(
		"lecturer_messages_history.html",
		messages=messages,
		page=page,
		total_pages=total_pages
	)


@app.route("/assignment-review/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_assignment_review(review_id: int):
	"""Delete a single assignment review (and stored file) for the current user."""
	try:
		review = sb_fetch_one(
			"""
			SELECT id, filepath
			FROM assignment_reviews
			WHERE id = :review_id AND student_id = :student_id
			""",
			{"review_id": review_id, "student_id": current_user.id}
		)
		if not review:
			flash("Review not found or permission denied.", "error")
			return redirect(url_for("assignment_review"))
		filepath = review.get("filepath")
		sb_execute(
			"""
			DELETE FROM assignment_reviews
			WHERE id = :review_id AND student_id = :student_id
			""",
			{"review_id": review_id, "student_id": current_user.id}
		)
		if filepath and os.path.exists(filepath):
			try:
				os.remove(filepath)
			except Exception:
				pass
		flash("Assignment review deleted.", "success")
	except Exception as exc:
		print(f"[assignment-review] delete failed user={current_user.id} review={review_id} err={exc}")
		flash("Failed to delete assignment review.", "error")
	return redirect(url_for("assignment_review"))


@app.route("/contact-lecturer", methods=["POST"])
@login_required
def contact_lecturer():
	"""Send a Quick Connect message to a lecturer via SMTP."""
	# Reference: ChatGPT (OpenAI) - Quick Connect Lecturer Email Flow
	# Date: 2026-01-23
	# Prompt: "I need a simple flow that lets students pick a lecturer, enter a subject
	# and message, and send it via SMTP with validation. Can you outline the pattern?"
	# ChatGPT provided the validation and send flow used here.
	action = request.form.get("action", "send").strip()
	lecturer_id = request.form.get("lecturer_id", "").strip()
	subject = request.form.get("subject", "").strip()
	request_text = request.form.get("request_text", "").strip()
	message = request.form.get("message", "").strip()
	if not lecturer_id or not subject:
		flash("Lecturer and subject are required.", "error")
		return redirect(url_for("index"))
	try:
		lecturer = sb_fetch_one(
			"SELECT name, email FROM lecturers WHERE id = :id",
			{"id": int(lecturer_id)}
		)
	except Exception:
		lecturer = None
	if not lecturer:
		flash("Lecturer not found.", "error")
		return redirect(url_for("index"))

	if action == "generate":
		if not request_text:
			flash("Please describe what you want from the lecturer.", "error")
			return redirect(url_for("index"))
		try:
			service = get_chatgpt_service()
			draft = service.draft_lecturer_email(
				student_name=current_user.name,
				student_id=current_user.student_number or current_user.id,
				lecturer_name=lecturer.get("name"),
				subject=subject,
				request_text=request_text,
			)
		except ChatGPTClientError as exc:
			flash(f"Failed to generate draft: {exc}", "error")
			return redirect(url_for("index"))
		except Exception as exc:
			print(f"[lecturers] draft failed user={current_user.id} err={exc}")
			flash("Failed to generate draft. Try again.", "error")
			return redirect(url_for("index"))
		session["lecturer_draft"] = draft
		session["lecturer_subject"] = subject
		session["lecturer_request"] = request_text
		session["lecturer_id"] = lecturer_id
		return redirect(url_for("index"))

	if not message:
		flash("Message is required to send.", "error")
		return redirect(url_for("index"))

	student_id_value = current_user.student_number or current_user.id
	signature = f"\n\nRegards,\n{current_user.name} (Student ID: {student_id_value})"
	lower_message = message.lower()
	if "regards," not in lower_message and "student id" not in lower_message:
		message = message.rstrip() + signature

	student_id_value = current_user.student_number or current_user.id
	full_body = (
		f"From: {current_user.name} ({current_user.email})\n"
		f"Student ID: {student_id_value}\n\n"
		f"{message}"
	)
	error = _send_reminder_email(
		to_email=lecturer.get("email"),
		subject=subject,
		body=full_body
	)
	try:
		sb_execute(
			"""
			INSERT INTO lecturer_messages (
				student_id, lecturer_id, subject, message, sent_at, email_status, email_error
			) VALUES (
				:student_id, :lecturer_id, :subject, :message, NOW(), :status, :error
			)
			""",
			{
				"student_id": current_user.id,
				"lecturer_id": int(lecturer_id),
				"subject": subject,
				"message": message,
				"status": "sent" if error is None else "failed",
				"error": error,
			}
		)
	except Exception as exc:
		print(f"[lecturers] message log failed user={current_user.id} err={exc}")
	if error:
		flash(f"Failed to send message: {error}", "error")
	else:
		flash(f"Message sent to {lecturer.get('name')}.", "success")
	return redirect(url_for("index"))


@app.route("/sync-canvas", methods=["GET", "POST"])
@login_required
def sync_canvas():
	"""Sync assignments from Canvas LMS"""
	if request.method == "POST":
		if not current_user.canvas_api_token:
			flash("Please add your Canvas API token in your profile first.", "error")
			return redirect(url_for("sync_canvas"))
		
		try:
			from canvas_sync import sync_canvas_assignments, sync_canvas_calendar_events
			import signal
			
			CANVAS_URL = "https://ucc.instructure.com"
			
			print(f"[sync] Starting assignment sync for user {current_user.id}...")
			stats = sync_canvas_assignments(
				canvas_url=CANVAS_URL,
				api_token=current_user.canvas_api_token,
				student_id=current_user.id,
				db_execute=sb_execute,
				db_fetch_all=sb_fetch_all,
				db_fetch_one=sb_fetch_one
			)
			print(f"[sync] Assignment sync complete: {stats}")

			print(f"[sync] Starting calendar events sync...")
			cal_stats = {"events_new": 0, "events_updated": 0, "errors": 0}
			try:
				api_token = current_user.canvas_api_token
				student_id = current_user.id
				
				# Reference: ChatGPT (OpenAI) - Background Threading with Timeout
				# Date: 2025-11-04
				# Prompt: [Threading pattern for Canvas sync - prompt from documentation]
				# ChatGPT suggested a pattern using threading and queue to run the Canvas sync in a background 
				# worker with a 15 second timeout. The worker thread calls the sync function and reports either 
				# success or an error back through a queue. If the sync exceeds the timeout, the system aborts 
				# the operation, records an error, and displays a warning to the user instead of blocking the request.
				# Reference: Python Documentation - threading Module
				# https://docs.python.org/3/library/threading.html
				# Reference: Python Documentation - queue Module
				# https://docs.python.org/3/library/queue.html
				import threading
				import queue
				
				result_queue = queue.Queue()
				
				def sync_worker():
					try:
						result = sync_canvas_calendar_events(
							canvas_url=CANVAS_URL,
							api_token=api_token,
							student_id=student_id,
							db_execute=sb_execute,
							db_fetch_all=sb_fetch_all,
							db_fetch_one=sb_fetch_one
						)
						result_queue.put(("success", result))
					except Exception as e:
						result_queue.put(("error", str(e)))
				
				thread = threading.Thread(target=sync_worker, daemon=True)
				thread.start()
				thread.join(timeout=15)  # 15 second timeout
				
				if thread.is_alive():
					print(f"[sync] Calendar events sync timed out after 15 seconds")
					cal_stats = {"events_new": 0, "events_updated": 0, "errors": 1}
					flash("Calendar events sync timed out (skipped)", "warning")
				else:
					if not result_queue.empty():
						status, result = result_queue.get()
						if status == "success":
							cal_stats = result
							print(f"[sync] Calendar events sync complete: {cal_stats}")
						else:
							print(f"[sync] Calendar events sync failed: {result}")
							cal_stats = {"events_new": 0, "events_updated": 0, "errors": 1}
							flash(f"Calendar events sync skipped: {result}", "warning")
					else:
						print(f"[sync] Calendar events sync returned no result")
						cal_stats = {"events_new": 0, "events_updated": 0, "errors": 1}
			except Exception as cal_error:
				print(f"[sync] Calendar events sync exception: {cal_error}")
				cal_stats = {"events_new": 0, "events_updated": 0, "errors": 1}
				flash(f"Calendar events sync skipped: {str(cal_error)}", "warning")
			
			if stats['errors']:
				for error in stats['errors']:
					flash(error, "warning")
			
			success_msg = f"✅ Canvas Sync Complete! "
			success_msg += f"Courses: {stats['courses_found']}, "
			success_msg += f"New: {stats['assignments_new']}, "
			success_msg += f"Updated: {stats['assignments_updated']}, "
			success_msg += f"Skipped: {stats['assignments_skipped']}"
			success_msg += f" | Events +{cal_stats['events_new']}/~{cal_stats['events_updated']}"
			
			if stats['modules_created'] > 0:
				success_msg += f", Modules Created: {stats['modules_created']}"
			
			flash(success_msg, "success")
			return redirect(url_for("sync_canvas"))
			
		except Exception as e:
			flash(f"Canvas sync failed: {str(e)}", "error")
			return redirect(url_for("sync_canvas"))
	
	has_token = current_user.canvas_api_token is not None and current_user.canvas_api_token != ""
	
	canvas_tasks_count = sb_fetch_one(
		"SELECT COUNT(*) as count FROM tasks WHERE student_id = :student_id AND canvas_assignment_id IS NOT NULL",
		{"student_id": current_user.id}
	)
	canvas_tasks = canvas_tasks_count['count'] if canvas_tasks_count else 0
	
	total_tasks = sb_fetch_one(
		"SELECT COUNT(*) as count FROM tasks WHERE student_id = :student_id",
		{"student_id": current_user.id}
	)
	total = total_tasks['count'] if total_tasks else 0
	
	return render_template("sync_canvas.html", 
	                      has_token=has_token, 
	                      canvas_tasks=canvas_tasks,
	                      total_tasks=total)


@app.route("/add-data")
@login_required
def add_data_form():
	"""Display forms for adding modules and tasks"""
	modules = sb_fetch_all("SELECT id, code FROM modules ORDER BY code")
	return render_template("add_data.html", modules=modules)


@app.route("/add-module", methods=["POST"])
@login_required
def add_module():
	"""Add a new module to the database"""
	try:
		code = request.form.get("code", "").strip().upper()
		if not code:
			flash("Module code is required", "error")
			return redirect(url_for("add_data_form"))
		
		sb_execute(
			"INSERT INTO modules (code) VALUES (:code)",
			{"code": code}
		)
		flash(f"Module '{code}' added successfully!", "success")
	except Exception as e:
		flash(f"Error adding module: {str(e)}", "error")
	
	return redirect(url_for("add_data_form"))


@app.route("/add-task", methods=["POST"])
@login_required
def add_task():
	"""Add a new task/assignment for the current user"""
	try:
		title = request.form.get("title", "").strip()
		module_id = request.form.get("module_id")
		due_date = request.form.get("due_date")
		due_time = request.form.get("due_time")
		description = request.form.get("description", "").strip() or None
		weight = request.form.get("weight_percentage")
		status = request.form.get("status", "pending")
		
		if not title:
			flash("Task title is required", "error")
			return redirect(url_for("add_data_form"))
		if not module_id:
			flash("Please select a module", "error")
			return redirect(url_for("add_data_form"))
		if not due_date:
			flash("Due date is required", "error")
			return redirect(url_for("add_data_form"))
		
		due_at_value = None
		if due_time:
			try:
				dt_combined = datetime.fromisoformat(f"{due_date}T{due_time}")
				due_at_value = dt_combined
			except ValueError:
				flash("Invalid due time provided; saving as all-day deadline.", "warning")
				due_at_value = None
		
		weight_value = None
		if weight:
			try:
				weight_value = float(weight)
			except ValueError:
				flash("Weighting must be a number.", "warning")
				weight_value = None
		
		sb_execute(
			"""INSERT INTO tasks (title, student_id, module_id, due_date, due_at, description, status, weight_percentage) 
			   VALUES (:title, :student_id, :module_id, :due_date, :due_at, :description, :status, :weight_percentage)""",
			{
				"title": title,
				"student_id": current_user.id,
				"module_id": int(module_id),
				"due_date": due_date,
				"due_at": due_at_value,
				"description": description,
				"status": status,
				"weight_percentage": weight_value
			}
		)
		flash(f"Task '{title}' added successfully!", "success")
	except Exception as e:
		flash(f"Error adding task: {str(e)}", "error")
	
	return redirect(url_for("add_data_form"))


@app.route("/add-lecturer", methods=["POST"])
@login_required
def add_lecturer():
	"""Add a lecturer contact for Quick Connect."""
	try:
		name = request.form.get("name", "").strip()
		email = request.form.get("email", "").strip()
		module_code = request.form.get("module_code", "").strip().upper() or None
		if not name or not email:
			flash("Lecturer name and email are required.", "error")
			return redirect(url_for("add_data_form"))
		sb_execute(
			"""
			INSERT INTO lecturers (name, email, module_code)
			VALUES (:name, :email, :module_code)
			""",
			{"name": name, "email": email, "module_code": module_code}
		)
		flash("Lecturer added successfully.", "success")
	except Exception as exc:
		print(f"[lecturers] add failed user={current_user.id} err={exc}")
		flash("Failed to add lecturer.", "error")
	return redirect(url_for("add_data_form"))


@app.route("/update-task-status/<int:task_id>", methods=["POST"])
@login_required
def update_task_status(task_id):
	"""Update the status of a task"""
	try:
		status = request.form.get("status")
		if status not in ["pending", "in_progress", "completed"]:
			flash("Invalid status", "error")
			return redirect(url_for("tasks"))
		
		task = sb_fetch_one("SELECT id FROM tasks WHERE id = :id AND student_id = :student_id", 
		                    {"id": task_id, "student_id": current_user.id})
		if not task:
			flash("Task not found or you don't have permission to update it", "error")
			return redirect(url_for("tasks"))
		
		if status == "completed":
			sb_execute(
				"""UPDATE tasks 
				   SET status = :status, completed_at = NOW() 
				   WHERE id = :task_id AND student_id = :student_id""",
				{"status": status, "task_id": task_id, "student_id": current_user.id}
			)
		else:
			sb_execute(
				"""UPDATE tasks 
				   SET status = :status, completed_at = NULL 
				   WHERE id = :task_id AND student_id = :student_id""",
				{"status": status, "task_id": task_id, "student_id": current_user.id}
			)
		
		flash("Task status updated successfully!", "success")
	except Exception as e:
		flash(f"Error updating task: {str(e)}", "error")
	
	return redirect(url_for("tasks"))


if __name__ == "__main__":
	test_database_connection()
	
	cfg = get_flask_config()
	app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)
