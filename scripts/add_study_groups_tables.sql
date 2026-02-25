-- Reference: ChatGPT (OpenAI) - Study Groups Migration Script
-- Date: 2026-02-25
-- Prompt: "I need a safe SQL migration for module-based collaborative study groups
-- with members, message thread, and shared resources. Can you provide CREATE TABLE
-- and index statements using IF NOT EXISTS so reruns are safe?"
-- ChatGPT provided the idempotent migration pattern adapted below.

CREATE TABLE IF NOT EXISTS study_groups (
    id SERIAL PRIMARY KEY,
    module_code TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(group_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_study_group_members_group
    ON study_group_members(group_id, joined_at DESC);

CREATE INDEX IF NOT EXISTS idx_study_group_members_student
    ON study_group_members(student_id, joined_at DESC);

CREATE TABLE IF NOT EXISTS study_group_messages (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    student_name TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_study_group_messages_group
    ON study_group_messages(group_id, created_at DESC);

CREATE TABLE IF NOT EXISTS study_group_resources (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_study_group_resources_group
    ON study_group_resources(group_id, created_at DESC);
