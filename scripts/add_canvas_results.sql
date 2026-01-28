-- Reference: ChatGPT (OpenAI) - Canvas Grade Fields
-- Date: 2026-01-22
-- Prompt: "I need to store Canvas grades on tasks (score, possible, graded_at).
-- Can you provide the ALTER TABLE and index SQL?"
-- ChatGPT provided the schema update for Canvas grade fields.
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS canvas_score NUMERIC(6,2),
ADD COLUMN IF NOT EXISTS canvas_possible NUMERIC(6,2),
ADD COLUMN IF NOT EXISTS canvas_graded_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_tasks_canvas_score ON tasks(canvas_score);


