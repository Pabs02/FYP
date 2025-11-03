from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from typing import List, Dict, Optional
from datetime import datetime

from config import get_flask_config, get_supabase_database_url
from db_supabase import fetch_all as sb_fetch_all, fetch_one as sb_fetch_one, execute as sb_execute  # type: ignore
SUPABASE_URL = get_supabase_database_url()


app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "your-secret-key-change-this-in-production"  # For flash messages and sessions

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'


# User model for Flask-Login
class User(UserMixin):
	"""User model for authentication"""
	def __init__(self, id: int, name: str, email: str, canvas_api_token: Optional[str] = None):
		self.id = id
		self.name = name
		self.email = email
		self.canvas_api_token = canvas_api_token
	
	@staticmethod
	def get(user_id: int) -> Optional['User']:
		"""Get user by ID"""
		user_data = sb_fetch_one("SELECT id, name, email, canvas_api_token FROM students WHERE id = :id", {"id": user_id})
		if user_data:
			return User(
				id=user_data['id'],
				name=user_data['name'],
				email=user_data['email'],
				canvas_api_token=user_data.get('canvas_api_token')
			)
		return None
	
	@staticmethod
	def get_by_email(email: str) -> Optional['User']:
		"""Get user by email"""
		user_data = sb_fetch_one("SELECT id, name, email, canvas_api_token FROM students WHERE email = :email", {"email": email})
		if user_data:
			return User(
				id=user_data['id'],
				name=user_data['name'],
				email=user_data['email'],
				canvas_api_token=user_data.get('canvas_api_token')
			)
		return None


@login_manager.user_loader
def load_user(user_id):
	"""Load user by ID for Flask-Login"""
	return User.get(int(user_id))


# Custom Jinja2 filter for Irish date format (DD/MM/YYYY)
@app.template_filter('irish_date')
def format_irish_date(value):
	"""Format date/datetime to Irish format DD/MM/YYYY"""
	if value is None:
		return ""
	
	# Handle both datetime and date objects, and strings
	if isinstance(value, str):
		try:
			# Try parsing common datetime formats
			from datetime import datetime
			value = datetime.fromisoformat(value.replace('Z', '+00:00'))
		except:
			return value
	
	# Format as DD/MM/YYYY
	try:
		return value.strftime('%d/%m/%Y')
	except:
		return str(value)


@app.template_filter('irish_datetime')
def format_irish_datetime(value):
	"""Format datetime to Irish format DD/MM/YYYY HH:MM"""
	if value is None:
		return ""
	
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


# Startup Connection Test
def test_database_connection():
	"""Test Supabase database connection on startup"""
	print("\n" + "="*70)
	print("🚀 STUDENT TASK MANAGEMENT SYSTEM")
	print("="*70)
	
	# Check database URL
	if SUPABASE_URL:
		# Extract safe info (hide password)
		try:
			from urllib.parse import urlparse
			parsed = urlparse(SUPABASE_URL)
			safe_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}/{parsed.path.strip('/')}"
			print(f"📊 Database: Supabase PostgreSQL")
			print(f"🌍 Host: {parsed.hostname}")
			print(f"🔌 Port: {parsed.port}")
		except:
			print(f"📊 Database: Supabase PostgreSQL (configured)")
		
		# Test connection
		try:
			result = sb_fetch_one("SELECT version(), current_database(), current_user")
			print(f"✅ Database Connection: SUCCESS")
			print(f"   └─ Database: {result['current_database']}")
			print(f"   └─ User: {result['current_user']}")
			
			# Test table access
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


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
	"""User login page and handler"""
	# Redirect if already logged in
	if current_user.is_authenticated:
		return redirect(url_for("index"))
	
	if request.method == "POST":
		email = request.form.get("email", "").strip().lower()
		password = request.form.get("password", "")
		
		if not email or not password:
			flash("Please provide both email and password", "error")
			return render_template("login.html")
		
		# Get user from database
		user_data = sb_fetch_one(
			"SELECT id, name, email, password_hash, canvas_api_token FROM students WHERE email = :email",
			{"email": email}
		)
		
		if not user_data:
			flash("Invalid email or password", "error")
			return render_template("login.html")
		
		# Check password
		if not user_data.get('password_hash'):
			flash("Account not activated. Please register first.", "error")
			return render_template("login.html")
		
		if not check_password_hash(user_data['password_hash'], password):
			flash("Invalid email or password", "error")
			return render_template("login.html")
		
		# Create user object and log in
		user = User(
			id=user_data['id'],
			name=user_data['name'],
			email=user_data['email'],
			canvas_api_token=user_data.get('canvas_api_token')
		)
		login_user(user, remember=True)
		
		# Update last login time
		sb_execute(
			"UPDATE students SET last_login = NOW() WHERE id = :id",
			{"id": user.id}
		)
		
		flash(f"Welcome back, {user.name}!", "success")
		
		# Redirect to next page or home
		next_page = request.args.get('next')
		return redirect(next_page) if next_page else redirect(url_for('index'))
	
	return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
	"""User registration page and handler"""
	# Redirect if already logged in
	if current_user.is_authenticated:
		return redirect(url_for("index"))
	
	if request.method == "POST":
		name = request.form.get("name", "").strip()
		email = request.form.get("email", "").strip().lower()
		password = request.form.get("password", "")
		password_confirm = request.form.get("password_confirm", "")
		canvas_api_token = request.form.get("canvas_api_token", "").strip()
		
		# Validation
		if not name or not email or not password:
			flash("All fields are required", "error")
			return render_template("register.html")
		
		if len(password) < 6:
			flash("Password must be at least 6 characters long", "error")
			return render_template("register.html")
		
		if password != password_confirm:
			flash("Passwords do not match", "error")
			return render_template("register.html")
		
		# Check if email already exists
		existing = sb_fetch_one("SELECT id FROM students WHERE email = :email", {"email": email})
		if existing:
			flash("Email already registered. Please login instead.", "error")
			return redirect(url_for("login"))
		
		# Hash password
		password_hash = generate_password_hash(password)
		
		try:
			# Insert new user (with optional Canvas token)
			sb_execute(
				"""INSERT INTO students (name, email, password_hash, canvas_api_token, created_at) 
				   VALUES (:name, :email, :password_hash, :canvas_api_token, NOW())""",
				{
					"name": name,
					"email": email,
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
	
	try:
		# Update Canvas API token
		sb_execute(
			"UPDATE students SET canvas_api_token = :canvas_api_token WHERE id = :id",
			{
				"canvas_api_token": canvas_api_token if canvas_api_token else None,
				"id": current_user.id
			}
		)
		
		# Update the current user's token in memory
		current_user.canvas_api_token = canvas_api_token if canvas_api_token else None
		
		if canvas_api_token:
			flash("✅ Canvas API token updated successfully!", "success")
		else:
			flash("Canvas API token removed.", "success")
		
	except Exception as e:
		flash(f"Error updating profile: {str(e)}", "error")
	
	return redirect(url_for("profile"))


# ============================================================================
# MAIN APPLICATION ROUTES
# ============================================================================

@app.route("/")
@login_required
def index():
	return render_template("index.html")


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
	# Only show tasks for the logged-in student
	sql = """
		SELECT t.id, t.title, t.status, t.due_date, 
		       t.canvas_assignment_id, t.canvas_course_id,
		       s.name AS student_name, 
		       m.code AS module_code
		FROM tasks t
		JOIN students s ON s.id = t.student_id
		JOIN modules m ON m.id = t.module_id
		WHERE t.student_id = :student_id
		ORDER BY t.due_date ASC
		LIMIT 200
	"""
	try:
		rows: List[Dict] = sb_fetch_all(sql, {"student_id": current_user.id})
	except Exception:
		rows = []
	return render_template("tasks.html", tasks=rows)


@app.route("/calendar")
@login_required
def calendar_view():
	"""Calendar view of tasks by due date for the current user"""
	# Fetch tasks for current user to render as calendar events
	sql = """
		SELECT t.id, t.title, t.status, t.due_date,
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

	# Prepare events for FullCalendar
	events: List[Dict] = []
	for r in rows:
		# FullCalendar expects ISO date strings (YYYY-MM-DD) for all-day events
		due_date = r.get("due_date")
		date_str = due_date.strftime("%Y-%m-%d") if hasattr(due_date, "strftime") else str(due_date)

		# Color coding by status
		status = r.get("status", "pending")
		if status == "completed":
			color = "#16a34a"  # green
		elif status == "in_progress":
			color = "#f59e0b"  # amber
		else:
			color = "#2563eb"  # blue (pending/default)

		# Badge for Canvas-synced tasks
		is_canvas = r.get("canvas_assignment_id") is not None
		prefix = "📚 " if is_canvas else ""

		events.append({
			"id": r.get("id"),
			"title": f"{prefix}{r.get('title')} [{r.get('module_code')}]",
			"start": date_str,
			"allDay": True,
			"color": color,
			"extendedProps": {
				"status": status,
				"module": r.get("module_code")
			}
		})

	# Include timed events (lectures) from events table
	try:
		rows_ev: List[Dict] = sb_fetch_all(
			"""
			SELECT e.id, e.title, e.start_at, e.end_at, e.location, e.canvas_course_id, m.code AS module_code
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
		# Ensure ISO-8601 strings for FullCalendar
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
		events.append({
			"id": f"event-{ev.get('id')}",
			"title": f"{title} [{mod}]" if mod else title,
			"start": start_iso,
			"end": end_iso,
			"allDay": False,
			"color": "#0ea5e9",  # cyan for lectures/events
			"extendedProps": {
				"module": mod,
				"location": ev.get("location")
			}
		})

	return render_template("calendar.html", events=events)


@app.route("/analytics")
@login_required
def analytics():
	charts_dir = os.path.join(app.static_folder or "static", "charts")
	os.makedirs(charts_dir, exist_ok=True)

	# Get analytics data from database (filtered by current user)
	try:
		# Task status overview for current user
		status_overview = sb_fetch_all("""
			SELECT status, COUNT(id) as count
			FROM tasks
			WHERE student_id = :student_id
			GROUP BY status
		""", {"student_id": current_user.id})
		
		# Calculate totals
		total_tasks = sum(s['count'] for s in status_overview)
		completed_tasks = next((s['count'] for s in status_overview if s['status'] == 'completed'), 0)
		in_progress_tasks = next((s['count'] for s in status_overview if s['status'] == 'in_progress'), 0)
		pending_tasks = next((s['count'] for s in status_overview if s['status'] == 'pending'), 0)
		
		# Weekly completion data for current user
		weekly_data = sb_fetch_all("""
			SELECT 
				DATE_TRUNC('week', completed_at) as week,
				COUNT(*) as completions
			FROM tasks
			WHERE student_id = :student_id 
			  AND status = 'completed' 
			  AND completed_at IS NOT NULL
			GROUP BY DATE_TRUNC('week', completed_at)
			ORDER BY week
		""", {"student_id": current_user.id})
		
		# Calculate max for scaling
		max_weekly_completions = max((w['completions'] for w in weekly_data), default=1)
		
		# Completion timing data for current user
		completion_stats = sb_fetch_one("""
			SELECT 
				COUNT(*) as total_completed,
				SUM(CASE WHEN completed_at <= due_date THEN 1 ELSE 0 END) as on_time,
				SUM(CASE WHEN completed_at > due_date THEN 1 ELSE 0 END) as late
			FROM tasks 
			WHERE student_id = :student_id 
			  AND status = 'completed' 
			  AND completed_at IS NOT NULL
		""", {"student_id": current_user.id})
		
		# Calculate percentages
		if completion_stats and completion_stats['total_completed'] > 0:
			on_time_percentage = round((completion_stats['on_time'] / completion_stats['total_completed']) * 100, 1)
			late_percentage = round((completion_stats['late'] / completion_stats['total_completed']) * 100, 1)
			completion_stats['on_time_percentage'] = on_time_percentage
			completion_stats['late_percentage'] = late_percentage
		
		# Module performance data for current user
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
			LEFT JOIN tasks t ON m.id = t.module_id AND t.student_id = :student_id
			GROUP BY m.id, m.code
			HAVING COUNT(t.id) > 0
			ORDER BY completion_rate DESC
		""", {"student_id": current_user.id})
		
		analytics_data = {
			'total_tasks': total_tasks,
			'completed_tasks': completed_tasks,
			'in_progress_tasks': in_progress_tasks,
			'pending_tasks': pending_tasks,
			'weekly_data': weekly_data,
			'max_weekly_completions': max_weekly_completions,
			'completion_stats': completion_stats,
			'module_stats': module_stats
		}
		
	except Exception as e:
		print(f"Error fetching analytics data: {e}")
		analytics_data = {
			'total_tasks': 0,
			'completed_tasks': 0,
			'in_progress_tasks': 0,
			'pending_tasks': 0,
			'weekly_data': [],
			'max_weekly_completions': 1,
			'completion_stats': None,
			'module_stats': []
		}

	return render_template("analytics.html", analytics=analytics_data)


@app.route("/sync-canvas", methods=["GET", "POST"])
@login_required
def sync_canvas():
	"""Sync assignments from Canvas LMS"""
	if request.method == "POST":
		# Check if user has Canvas API token
		if not current_user.canvas_api_token:
			flash("Please add your Canvas API token in your profile first.", "error")
			return redirect(url_for("sync_canvas"))
		
		try:
			# Import Canvas sync module
			from canvas_sync import sync_canvas_assignments, sync_canvas_calendar_events
			
			# Canvas URL for UCC
			CANVAS_URL = "https://ucc.instructure.com"
			
			# Perform assignment sync
			stats = sync_canvas_assignments(
				canvas_url=CANVAS_URL,
				api_token=current_user.canvas_api_token,
				student_id=current_user.id,
				db_execute=sb_execute,
				db_fetch_all=sb_fetch_all,
				db_fetch_one=sb_fetch_one
			)

			# Perform calendar events sync (lectures/timed events)
			cal_stats = sync_canvas_calendar_events(
				canvas_url=CANVAS_URL,
				api_token=current_user.canvas_api_token,
				student_id=current_user.id,
				db_execute=sb_execute,
				db_fetch_all=sb_fetch_all,
				db_fetch_one=sb_fetch_one
			)
			
			# Show results
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
			return redirect(url_for("tasks"))
			
		except Exception as e:
			flash(f"Canvas sync failed: {str(e)}", "error")
			return redirect(url_for("sync_canvas"))
	
	# GET request - show sync page
	has_token = current_user.canvas_api_token is not None and current_user.canvas_api_token != ""
	
	# Get sync statistics
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
	"""Display forms for adding modules and tasks (current user only)"""
	# Get all modules for dropdown
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
		status = request.form.get("status", "pending")
		
		# Validation
		if not title:
			flash("Task title is required", "error")
			return redirect(url_for("add_data_form"))
		if not module_id:
			flash("Please select a module", "error")
			return redirect(url_for("add_data_form"))
		if not due_date:
			flash("Due date is required", "error")
			return redirect(url_for("add_data_form"))
		
		# Use current user's ID
		sb_execute(
			"""INSERT INTO tasks (title, student_id, module_id, due_date, status) 
			   VALUES (:title, :student_id, :module_id, :due_date, :status)""",
			{
				"title": title,
				"student_id": current_user.id,
				"module_id": int(module_id),
				"due_date": due_date,
				"status": status
			}
		)
		flash(f"Task '{title}' added successfully!", "success")
	except Exception as e:
		flash(f"Error adding task: {str(e)}", "error")
	
	return redirect(url_for("add_data_form"))


@app.route("/update-task-status/<int:task_id>", methods=["POST"])
@login_required
def update_task_status(task_id):
	"""Update the status of a task (only for current user's tasks)"""
	try:
		status = request.form.get("status")
		if status not in ["pending", "in_progress", "completed"]:
			flash("Invalid status", "error")
			return redirect(url_for("tasks"))
		
		# Verify task belongs to current user
		task = sb_fetch_one("SELECT id FROM tasks WHERE id = :id AND student_id = :student_id", 
		                    {"id": task_id, "student_id": current_user.id})
		if not task:
			flash("Task not found or you don't have permission to update it", "error")
			return redirect(url_for("tasks"))
		
		# If marking as completed, set completed_at timestamp
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
	# Test database connection on startup
	test_database_connection()
	
	cfg = get_flask_config()
	app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)
