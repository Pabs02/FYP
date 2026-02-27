import sys

from main import _run_daily_summary_batch  # type: ignore


def send_daily_summaries() -> int:
	# Reference: ChatGPT (OpenAI) - Daily Summary Batch Job Pattern
	# Date: 2026-01-22
	# Prompt: "I need a script that iterates over students, checks a last‑sent date,
	# generates a summary, sends email, and records status. Can you sketch that flow?"
	# ChatGPT provided the batch flow and status update pattern.
	stats = _run_daily_summary_batch()
	print(f"[daily-summary-cron] stats={stats}")
	return int(stats.get("sent", 0))


if __name__ == "__main__":
	count = send_daily_summaries()
	print(f"Daily summaries sent: {count}")
	sys.exit(0)
