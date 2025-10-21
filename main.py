from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import os
from typing import List, Dict
from datetime import datetime

from config import get_flask_config, get_supabase_database_url
from db_supabase import fetch_all as sb_fetch_all, fetch_one as sb_fetch_one, execute as sb_execute  # type: ignore
SUPABASE_URL = get_supabase_database_url()


app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "your-secret-key-change-this-in-production"  # For flash messages


@app.route("/")
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
def tasks():
	# Adjust table/column names to your schema if needed
	sql = (
		"SELECT t.id, t.title, t.status, t.due_date, "
		"s.name AS student_name, "
		"m.code AS module_code "
		"FROM tasks t "
		"JOIN students s ON s.id = t.student_id "
		"JOIN modules m ON m.id = t.module_id "
		"ORDER BY t.due_date ASC "
		"LIMIT 200"
	)
	try:
		rows: List[Dict] = sb_fetch_all(sql)
	except Exception:
		rows = []
	return render_template("tasks.html", tasks=rows)


@app.route("/analytics")
def analytics():
	charts_dir = os.path.join(app.static_folder or "static", "charts")
	os.makedirs(charts_dir, exist_ok=True)

	# Get analytics data from database
	try:
		# Task status overview
		status_overview = sb_fetch_all("""
			SELECT status, COUNT(id) as count
			FROM tasks
			GROUP BY status
		""")
		
		# Calculate totals
		total_tasks = sum(s['count'] for s in status_overview)
		completed_tasks = next((s['count'] for s in status_overview if s['status'] == 'completed'), 0)
		in_progress_tasks = next((s['count'] for s in status_overview if s['status'] == 'in_progress'), 0)
		pending_tasks = next((s['count'] for s in status_overview if s['status'] == 'pending'), 0)
		
		# Weekly completion data
		weekly_data = sb_fetch_all("""
			SELECT 
				DATE_TRUNC('week', completed_at) as week,
				COUNT(*) as completions
			FROM tasks
			WHERE status = 'completed' AND completed_at IS NOT NULL
			GROUP BY DATE_TRUNC('week', completed_at)
			ORDER BY week
		""")
		
		# Calculate max for scaling
		max_weekly_completions = max((w['completions'] for w in weekly_data), default=1)
		
		# Completion timing data
		completion_stats = sb_fetch_one("""
			SELECT 
				COUNT(*) as total_completed,
				SUM(CASE WHEN completed_at <= due_date THEN 1 ELSE 0 END) as on_time,
				SUM(CASE WHEN completed_at > due_date THEN 1 ELSE 0 END) as late
			FROM tasks 
			WHERE status = 'completed' AND completed_at IS NOT NULL
		""")
		
		# Calculate percentages
		if completion_stats and completion_stats['total_completed'] > 0:
			on_time_percentage = round((completion_stats['on_time'] / completion_stats['total_completed']) * 100, 1)
			late_percentage = round((completion_stats['late'] / completion_stats['total_completed']) * 100, 1)
			completion_stats['on_time_percentage'] = on_time_percentage
			completion_stats['late_percentage'] = late_percentage
		
		# Module performance data
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
			GROUP BY m.id, m.code
			ORDER BY completion_rate DESC
		""")
		
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


@app.route("/add-data")
def add_data_form():
	"""Display forms for adding students, modules, and tasks"""
	# Get existing students and modules for dropdowns
	students = sb_fetch_all("SELECT id, name FROM students ORDER BY name")
	modules = sb_fetch_all("SELECT id, code FROM modules ORDER BY code")
	return render_template("add_data.html", students=students, modules=modules)


@app.route("/add-student", methods=["POST"])
def add_student():
	"""Add a new student to the database"""
	try:
		name = request.form.get("name", "").strip()
		if not name:
			flash("Student name is required", "error")
			return redirect(url_for("add_data_form"))
		
		sb_execute(
			"INSERT INTO students (name) VALUES (:name)",
			{"name": name}
		)
		flash(f"Student '{name}' added successfully!", "success")
	except Exception as e:
		flash(f"Error adding student: {str(e)}", "error")
	
	return redirect(url_for("add_data_form"))


@app.route("/add-module", methods=["POST"])
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
def add_task():
	"""Add a new task/assignment to the database"""
	try:
		title = request.form.get("title", "").strip()
		student_id = request.form.get("student_id")
		module_id = request.form.get("module_id")
		due_date = request.form.get("due_date")
		status = request.form.get("status", "pending")
		
		# Validation
		if not title:
			flash("Task title is required", "error")
			return redirect(url_for("add_data_form"))
		if not student_id:
			flash("Please select a student", "error")
			return redirect(url_for("add_data_form"))
		if not module_id:
			flash("Please select a module", "error")
			return redirect(url_for("add_data_form"))
		if not due_date:
			flash("Due date is required", "error")
			return redirect(url_for("add_data_form"))
		
		sb_execute(
			"""INSERT INTO tasks (title, student_id, module_id, due_date, status) 
			   VALUES (:title, :student_id, :module_id, :due_date, :status)""",
			{
				"title": title,
				"student_id": int(student_id),
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
def update_task_status(task_id):
	"""Update the status of a task (mark as completed, in progress, etc.)"""
	try:
		status = request.form.get("status")
		if status not in ["pending", "in_progress", "completed"]:
			flash("Invalid status", "error")
			return redirect(url_for("tasks"))
		
		# If marking as completed, set completed_at timestamp
		if status == "completed":
			sb_execute(
				"""UPDATE tasks 
				   SET status = :status, completed_at = NOW() 
				   WHERE id = :task_id""",
				{"status": status, "task_id": task_id}
			)
		else:
			sb_execute(
				"""UPDATE tasks 
				   SET status = :status, completed_at = NULL 
				   WHERE id = :task_id""",
				{"status": status, "task_id": task_id}
			)
		
		flash("Task status updated successfully!", "success")
	except Exception as e:
		flash(f"Error updating task: {str(e)}", "error")
	
	return redirect(url_for("tasks"))


if __name__ == "__main__":
	cfg = get_flask_config()
	app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)
