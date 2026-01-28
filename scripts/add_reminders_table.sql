-- Reference: ChatGPT (OpenAI) - Reminders Table Schema
-- Date: 2026-01-22
-- Prompt: "I need a reminders table for automated nudges with unique constraints
-- per student/task/type. Can you draft the schema and indexes?"
-- ChatGPT provided the schema and indexing pattern for reminders.
-- Create reminders table for automated nudges
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    task_id BIGINT REFERENCES tasks(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_read BOOLEAN NOT NULL DEFAULT FALSE
);

-- Ensure we don't spam duplicate reminders per task/type
CREATE UNIQUE INDEX IF NOT EXISTS idx_reminders_unique
    ON reminders(student_id, task_id, reminder_type);

CREATE INDEX IF NOT EXISTS idx_reminders_student ON reminders(student_id);
CREATE INDEX IF NOT EXISTS idx_reminders_due_at ON reminders(due_at);
