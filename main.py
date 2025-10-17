from flask import Flask, render_template
import os
from typing import List, Dict

from config import get_flask_config
from db import fetch_all, fetch_one


app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/debug/db")
def debug_db():
    try:
        row = fetch_one("SELECT 1 AS ok")
        # Try to retrieve DB and version info
        db_row = fetch_one("SELECT DATABASE() AS db")
        ver_row = fetch_one("SELECT VERSION() AS version")
        status = {
            "connected": bool(row and row.get("ok") == 1),
            "database": db_row.get("db") if db_row else None,
            "version": ver_row.get("version") if ver_row else None,
        }
        return render_template("index.html", status=status)
    except Exception as exc:
        status = {"connected": False, "error": str(exc)}
        return render_template("index.html", status=status), 500


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
        rows: List[Dict] = fetch_all(sql)
    except Exception:
        rows = []
    return render_template("tasks.html", tasks=rows)


@app.route("/analytics")
def analytics():
    charts_dir = os.path.join(app.static_folder or "static", "charts")
    os.makedirs(charts_dir, exist_ok=True)

    weekly_png = os.path.join(charts_dir, "weekly_completions.png")
    rate_png = os.path.join(charts_dir, "on_time_rate.png")

    need_generate = not (os.path.exists(weekly_png) and os.path.exists(rate_png))

    if need_generate:
        try:
            from analytics_report import generate_charts
            generate_charts(output_dir=charts_dir)
        except Exception:
            # If analytics fail, we still render the page; images may be missing
            pass

    return render_template("analytics.html")


if __name__ == "__main__":
    cfg = get_flask_config()
    app.run(host=cfg.host, port=cfg.port, debug=cfg.debug)
