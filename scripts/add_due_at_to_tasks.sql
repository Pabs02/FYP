-- Add due_at timestamp column to tasks for precise due times
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS due_at TIMESTAMPTZ;

-- Backfill existing rows where only due_date exists (set to 17:00 local assumption)
UPDATE tasks
SET due_at = (due_date::timestamptz + INTERVAL '17 hours')
WHERE due_at IS NULL AND due_date IS NOT NULL;

-- Helpful index for calendar queries
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at);
