-- Reference: ChatGPT (OpenAI) - Activity Logs Table Schema
-- Date: 2026-02-04
-- Prompt: "I need a table to store all user actions with timestamps. It should log
-- student_id, path, method, endpoint, status_code, duration, and metadata."
-- ChatGPT provided the schema and indexing pattern for activity logs.
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(500) NOT NULL,
    endpoint VARCHAR(120),
    status_code INTEGER,
    duration_ms INTEGER,
    ip_address VARCHAR(100),
    user_agent VARCHAR(500),
    referrer VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_student_time
    ON activity_logs(student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_path
    ON activity_logs(path);
