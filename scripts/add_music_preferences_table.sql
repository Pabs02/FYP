-- Reference: ChatGPT (OpenAI) - User Music Preferences Table Migration
-- Date: 2026-02-25
-- Prompt: "I need a safe migration to store per-student Spotify music category
-- preferences so each user can personalize playlist suggestions. Please include
-- an idempotent table + index pattern."
-- ChatGPT provided the idempotent migration pattern adapted below.

CREATE TABLE IF NOT EXISTS student_music_preferences (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    categories_json TEXT NOT NULL DEFAULT '[]',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(student_id)
);

CREATE INDEX IF NOT EXISTS idx_student_music_preferences_student
    ON student_music_preferences(student_id);
