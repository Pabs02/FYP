-- Reference: ChatGPT (OpenAI) - Assignment Review Storage Schema
-- Date: 2026-01-22
-- Prompt: "I need a table to store AI assignment reviews with feedback and score
-- estimates linked to tasks and students. Can you draft the schema and indexes?"
-- ChatGPT provided the schema and indexing approach for AI review history.
-- Create assignment_reviews table for storing AI-generated reviews and grades
-- Links to tasks table for assignment association
CREATE TABLE IF NOT EXISTS assignment_reviews (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    filepath TEXT,
    original_text TEXT,
    ai_feedback TEXT,
    ai_score_estimate NUMERIC(6,2),
    ai_possible_score NUMERIC(6,2),
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for querying reviews by task
CREATE INDEX IF NOT EXISTS idx_assignment_reviews_task ON assignment_reviews(task_id);

-- Index for querying reviews by student
CREATE INDEX IF NOT EXISTS idx_assignment_reviews_student ON assignment_reviews(student_id);

-- Index for querying most recent reviews
CREATE INDEX IF NOT EXISTS idx_assignment_reviews_reviewed_at ON assignment_reviews(reviewed_at DESC);
