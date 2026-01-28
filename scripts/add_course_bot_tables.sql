-- Reference: ChatGPT (OpenAI) - Course Bot Storage Tables
-- Date: 2026-01-22
-- Prompt: "I need tables for course documents and Q&A history for a course bot.
-- Can you draft the schema and indexes?"
-- ChatGPT provided the schema and indexing approach for course documents and Q&A history.
-- Create course_documents table for AI Course Bot
CREATE TABLE IF NOT EXISTS course_documents (
    id SERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    filepath TEXT,
    extracted_text TEXT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Store Q&A history for course bot
CREATE TABLE IF NOT EXISTS course_bot_history (
    id SERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT,
    citations TEXT,
    asked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_course_documents_student ON course_documents(student_id);
CREATE INDEX IF NOT EXISTS idx_course_documents_uploaded_at ON course_documents(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_course_bot_history_student ON course_bot_history(student_id);
CREATE INDEX IF NOT EXISTS idx_course_bot_history_asked_at ON course_bot_history(asked_at DESC);
