-- Reference: ChatGPT (OpenAI) - Adding Timestamp Column with Backfill
-- Date: 2025-10-28
-- Prompt: "I have a tasks table with a due_date column (date only). I need to add a 
-- due_at column (timestamp with timezone) for precise due times. Can you give me SQL 
-- to add the column, backfill existing rows by setting due_at to 5 PM on the due_date, 
-- and create an index?"
-- ChatGPT provided the ALTER TABLE, UPDATE with interval arithmetic, and index creation.

-- Add due_at timestamp column to tasks for precise due times
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS due_at TIMESTAMPTZ;

-- Backfill existing rows where only due_date exists (set to 17:00 local assumption)
UPDATE tasks
SET due_at = (due_date::timestamptz + INTERVAL '17 hours')
WHERE due_at IS NULL AND due_date IS NOT NULL;

-- Helpful index for calendar queries
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at);
