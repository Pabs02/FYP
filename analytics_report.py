from typing import Optional
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from db import fetch_all


def _load_task_data() -> pd.DataFrame:
	# Adjust to match your schema: expects fields id, title, status, due_date, completed_at
	sql = (
		"SELECT id, title, status, due_date, completed_at "
		"FROM tasks"
	)
	rows = fetch_all(sql)
	df = pd.DataFrame(rows)
	if not df.empty:
		# Parse dates if present
		for col in ["due_date", "completed_at"]:
			if col in df.columns:
				df[col] = pd.to_datetime(df[col], errors="coerce")
	return df


def _weekly_completions(df: pd.DataFrame) -> pd.DataFrame:
	if df.empty:
		return pd.DataFrame({"week": [], "count": []})
	completed = df[df["status"] == "completed"].copy()
	if completed.empty:
		return pd.DataFrame({"week": [], "count": []})
	completed["week"] = completed["completed_at"].dt.to_period("W").dt.start_time
	agg = completed.groupby("week").size().reset_index(name="count").sort_values("week")
	return agg


def _on_time_rate(df: pd.DataFrame) -> pd.Series:
	if df.empty:
		return pd.Series({"on_time": 0, "late": 0})
	completed = df[df["status"] == "completed"].copy()
	if completed.empty:
		return pd.Series({"on_time": 0, "late": 0})
	on_time = (completed["completed_at"] <= completed["due_date"]).sum()
	late = (completed["completed_at"] > completed["due_date"]).sum()
	return pd.Series({"on_time": int(on_time), "late": int(late)})


def generate_charts(output_dir: Optional[str] = None) -> None:
	output_dir = output_dir or os.path.join("static", "charts")
	os.makedirs(output_dir, exist_ok=True)

	df = _load_task_data()

	# Chart 1: Weekly completions
	weekly = _weekly_completions(df)
	plt.figure(figsize=(6, 4))
	if not weekly.empty:
		plt.bar(weekly["week"].dt.strftime("%Y-%m-%d"), weekly["count"], color="#3b82f6")
		plt.xticks(rotation=45, ha="right")
		plt.ylabel("Completions")
		plt.title("Weekly Task Completions")
		plt.tight_layout()
	else:
		plt.text(0.5, 0.5, "No completion data", ha="center", va="center")
	plt.savefig(os.path.join(output_dir, "weekly_completions.png"), dpi=144)
	plt.close()

	# Chart 2: On-time vs late
	rate = _on_time_rate(df)
	plt.figure(figsize=(6, 4))
	if rate.sum() > 0:
		plt.pie([rate["on_time"], rate["late"]], labels=["On time", "Late"], autopct="%1.0f%%", colors=["#10b981", "#ef4444"])
		plt.title("On-time vs Late Completion")
	else:
		plt.text(0.5, 0.5, "No completion data", ha="center", va="center")
	plt.tight_layout()
	plt.savefig(os.path.join(output_dir, "on_time_rate.png"), dpi=144)
	plt.close()


if __name__ == "__main__":
	generate_charts()
