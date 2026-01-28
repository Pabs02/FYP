-- Reference: ChatGPT (OpenAI) - Task Weight Field
-- Date: 2026-01-22
-- Prompt: "I need to add a weight_percentage column to tasks and index it for
-- analytics. Can you provide the SQL?"
-- ChatGPT provided the ALTER TABLE and index pattern.
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS weight_percentage NUMERIC(5,2);

CREATE INDEX IF NOT EXISTS idx_tasks_weight ON tasks(weight_percentage);


