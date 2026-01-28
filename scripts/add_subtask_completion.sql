-- Reference: ChatGPT (OpenAI) - Subtask Completion Fields
-- Date: 2026-01-22
-- Prompt: "I need to add completion status and timestamps to subtasks and index
-- by completion state. Can you provide the ALTER TABLE statements?"
-- ChatGPT provided the SQL for completion fields and indexing.
-- Add completion status to subtasks table
ALTER TABLE subtasks 
ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Add index for filtering completed subtasks
CREATE INDEX IF NOT EXISTS idx_subtasks_completed ON subtasks(task_id, is_completed);



