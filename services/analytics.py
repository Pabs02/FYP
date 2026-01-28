from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional, Dict, Any


@dataclass
class UpcomingTask:
	id: int
	title: str
	module_code: Optional[str]
	due_at: datetime
	due_in: timedelta
	weight: Optional[float]
	status: str
	canvas_score: Optional[float]
	canvas_possible: Optional[float]
	priority: float


def to_datetime(value) -> Optional[datetime]:
	if value is None:
		return None
	if isinstance(value, datetime):
		return value
	try:
		return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
	except Exception:
		return None


def to_date(value) -> Optional[datetime]:
	if value is None:
		return None
	if hasattr(value, "isoformat") and not isinstance(value, datetime):
		try:
			return datetime.combine(value, datetime.min.time())
		except Exception:
			return None
	try:
		return datetime.fromisoformat(str(value))
	except Exception:
		return None


# Reference: ChatGPT (OpenAI) - DateTime Normalization with Multiple Fallbacks
# Date: 2025-11-14
# Prompt: "I need a function that normalizes due dates from database rows. The row might have 
# a due_at (datetime), a due_date (date object), or a due_date string. I need to handle all 
# these cases and convert them to a datetime with timezone info, defaulting to 23:59 on the 
# due date. Can you help me write this normalization logic?"
# ChatGPT provided the algorithm for normalizing due dates with multiple fallback strategies. 
# It handles datetime objects, date objects, and ISO date strings, ensuring all are converted 
# to a consistent datetime format with timezone info for priority calculations.
def normalise_due_datetime(task_row: Dict[str, Any], now: datetime) -> Optional[datetime]:
	due_at = to_datetime(task_row.get("due_at"))
	if due_at:
		return due_at
	due_date = task_row.get("due_date")
	date_obj = None
	if hasattr(due_date, "isoformat") and not isinstance(due_date, datetime):
		try:
			from datetime import date
			if isinstance(due_date, date):
				date_obj = due_date
		except Exception:
			date_obj = None
	if date_obj is None:
		date_obj = to_date(due_date)
	if not date_obj:
		return None
	if isinstance(date_obj, datetime):
		base = date_obj
	else:
		base = datetime.combine(date_obj, datetime.min.time())
	return base.replace(hour=23, minute=59, second=0, microsecond=0, tzinfo=now.tzinfo)


# Reference: ChatGPT (OpenAI) - Priority Calculation Algorithm
# Date: 2025-11-14
# Prompt: "I need a priority scoring algorithm that combines assignment weight (percentage) 
# and urgency (hours until due). High weight assignments should score higher, and assignments 
# due soon should score higher. Urgency should have diminishing returns as time increases. 
# Can you help me design this scoring formula?"
# ChatGPT provided the priority calculation algorithm that combines weight and urgency 
# components. Weight is multiplied by 2.0, and urgency uses a hyperbolic decay function 
# (48.0 / (hours/24 + 0.5)) that heavily penalizes overdue tasks (100.0) while providing 
# diminishing urgency for tasks further out. This ensures high-weight and urgent tasks 
# appear first in priority lists.
def calculate_priority(weight: Optional[float], hours_remaining: float) -> float:
	# Convert weight to float if it's a Decimal type (from database)
	if weight is not None:
		try:
			weight = float(weight)
		except (TypeError, ValueError):
			weight = None
	weight_component = (weight or 0.0) * 2.0
	urgency_component = 0.0
	if hours_remaining <= 0:
		urgency_component = 100.0
	else:
		urgency_component = min(75.0, 48.0 / (hours_remaining / 24.0 + 0.5))
	return round(weight_component + urgency_component, 2)


def upcoming_tasks_with_priority(rows: Iterable[Dict[str, Any]], limit: int = 3) -> List[UpcomingTask]:
	now = datetime.now(timezone.utc)
	results: List[UpcomingTask] = []
	for row in rows:
		due_at = normalise_due_datetime(row, now)
		if not due_at:
			continue
		if due_at < now:
			# Skip tasks that are already past due for the priority widget
			continue
		delta = due_at - now
		weight = None
		try:
			raw_weight = row.get("weight_percentage")
			if raw_weight is not None:
				weight = float(raw_weight)
		except (TypeError, ValueError):
			weight = None
		priority = calculate_priority(weight, delta.total_seconds() / 3600)
		results.append(
			UpcomingTask(
				id=row.get("id"),
				title=row.get("title"),
				module_code=row.get("module_code"),
				due_at=due_at,
				due_in=delta,
				weight=weight,
				status=row.get("status", "pending"),
				canvas_score=row.get("canvas_score"),
				canvas_possible=row.get("canvas_possible"),
				priority=priority,
			)
		)
	results.sort(key=lambda item: (-item.priority, item.due_at))
	return results[:limit]


def assess_progress(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
	now = datetime.now(timezone.utc)
	overdue = 0
	nearly_due = 0
	completed_this_week = 0
	start_of_week = now - timedelta(days=now.weekday())
	for row in rows:
		status = row.get("status", "pending")
		due_at = normalise_due_datetime(row, now)
		if due_at and status != "completed":
			if due_at < now:
				overdue += 1
			elif due_at - now < timedelta(days=2):
				nearly_due += 1
		completed_at = to_datetime(row.get("completed_at"))
		if completed_at and completed_at >= start_of_week:
			completed_this_week += 1
	status_flag = "on_track"
	if overdue >= 2 or nearly_due >= 3:
		status_flag = "at_risk"
	elif overdue > 0 or nearly_due > 0:
		status_flag = "warning"
	return {
		"status": status_flag,
		"overdue": overdue,
		"nearly_due": nearly_due,
		"completed_this_week": completed_this_week
	}

