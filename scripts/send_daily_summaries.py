import sys
from datetime import datetime, timezone

from main import _build_daily_summary_email, _send_reminder_email  # type: ignore
from db_supabase import fetch_all as sb_fetch_all, execute as sb_execute


def _should_send_today(last_sent) -> bool:
	if not last_sent:
		return True
	try:
		last_date = last_sent.date() if hasattr(last_sent, "date") else None
		return last_date != datetime.now(timezone.utc).date()
	except Exception:
		return True


def send_daily_summaries() -> int:
	# Reference: ChatGPT (OpenAI) - Daily Summary Batch Job Pattern
	# Date: 2026-01-22
	# Prompt: "I need a script that iterates over students, checks a last‑sent date,
	# generates a summary, sends email, and records status. Can you sketch that flow?"
	# ChatGPT provided the batch flow and status update pattern.
	students = sb_fetch_all(
		"""
		SELECT id, email, email_daily_summary_enabled, last_daily_summary_sent_at
		FROM students
		WHERE email IS NOT NULL AND email <> ''
		"""
	)
	sent = 0
	for student in students:
		if not bool(student.get("email_daily_summary_enabled", True)):
			continue
		if not _should_send_today(student.get("last_daily_summary_sent_at")):
			continue
		body = _build_daily_summary_email(student.get("id"))
		if not body:
			continue
		error = _send_reminder_email(
			to_email=student.get("email"),
			subject="Your daily study summary",
			body=body,
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
				"student_id": student.get("id"),
			},
		)
		if error is None:
			sent += 1
	return sent


if __name__ == "__main__":
	count = send_daily_summaries()
	print(f"Daily summaries sent: {count}")
	sys.exit(0)
