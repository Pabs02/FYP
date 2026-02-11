-- Reference: ChatGPT (OpenAI) - Group Workspace Incremental Migration
-- Date: 2026-02-11
-- Prompt: "I already created initial group workspace tables. I now need a safe
-- follow-up migration to add invite token support, milestones, and task
-- attachments without breaking existing data. Can you provide ALTER/CREATE
-- statements with IF NOT EXISTS patterns?"
-- ChatGPT provided the incremental migration pattern below.

ALTER TABLE group_project_members
    ADD COLUMN IF NOT EXISTS invite_token TEXT;

ALTER TABLE group_project_members
    ADD COLUMN IF NOT EXISTS invite_status TEXT NOT NULL DEFAULT 'pending';

ALTER TABLE group_project_members
    ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMPTZ;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND indexname = 'uniq_group_project_member_invite_token'
    ) THEN
        CREATE UNIQUE INDEX uniq_group_project_member_invite_token
            ON group_project_members(invite_token)
            WHERE invite_token IS NOT NULL;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS group_project_milestones (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES group_projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    target_date DATE NOT NULL,
    notes TEXT,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_group_project_milestones_project
    ON group_project_milestones(project_id, target_date);

CREATE TABLE IF NOT EXISTS group_project_task_files (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES group_project_tasks(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES group_projects(id) ON DELETE CASCADE,
    uploaded_by_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    file_size_bytes INTEGER,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_group_project_task_files_project_task
    ON group_project_task_files(project_id, task_id, uploaded_at DESC);

CREATE TABLE IF NOT EXISTS group_project_files (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES group_projects(id) ON DELETE CASCADE,
    uploaded_by_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    file_size_bytes INTEGER,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_group_project_files_project
    ON group_project_files(project_id, uploaded_at DESC);

CREATE TABLE IF NOT EXISTS group_project_messages (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES group_projects(id) ON DELETE CASCADE,
    sender_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    sender_name TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_group_project_messages_project
    ON group_project_messages(project_id, created_at DESC);
