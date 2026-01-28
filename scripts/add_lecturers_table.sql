-- Reference: ChatGPT (OpenAI) - Lecturers Directory Table
-- Date: 2026-01-23
-- Prompt: "I need a lecturers table to store names, emails, and optional module codes
-- so students can contact lecturers from a dashboard form. Can you draft the schema
-- and indexes?"
-- ChatGPT provided the schema and indexing pattern for lecturer contacts.
CREATE TABLE IF NOT EXISTS lecturers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    module_code VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lecturers_email ON lecturers(email);
CREATE INDEX IF NOT EXISTS idx_lecturers_module_code ON lecturers(module_code);
