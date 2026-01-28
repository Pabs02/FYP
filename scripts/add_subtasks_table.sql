-- Reference: ChatGPT (OpenAI) - Subtasks Table Schema
-- Date: 2026-01-22
-- Prompt: "I need a subtasks table to store micro‑tasks linked to a task,
-- including sequence ordering and planned dates. Can you draft the schema?"
-- ChatGPT provided the schema pattern for subtasks.
CREATE TABLE IF NOT EXISTS subtasks (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    sequence INTEGER NOT NULL DEFAULT 1,
    estimated_hours NUMERIC(5,2),
    planned_week INTEGER,
    planned_start DATE,
    planned_end DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subtasks_task ON subtasks(task_id);


