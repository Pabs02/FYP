-- Reference: ChatGPT (OpenAI) - Lecturer Messages Table
-- Date: 2026-01-23
-- Prompt: "I need a table to store messages sent to lecturers from a dashboard
-- contact form, with student and lecturer references and timestamps. Can you draft it?"
-- ChatGPT provided the schema and indexing pattern for lecturer messages.
CREATE TABLE IF NOT EXISTS lecturer_messages (
    id SERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    lecturer_id INTEGER REFERENCES lecturers(id) ON DELETE SET NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    email_status VARCHAR(20),
    email_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_lecturer_messages_student ON lecturer_messages(student_id, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_lecturer_messages_lecturer ON lecturer_messages(lecturer_id, sent_at DESC);
