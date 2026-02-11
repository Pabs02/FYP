-- Reference: ChatGPT (OpenAI) - Group Workspace SQL Schema
-- Date: 2026-02-11
-- Prompt: "I need PostgreSQL tables for a group project workspace: projects owned by
-- a student, members per project, and delegated tasks with status/progress for tracking.
-- Can you draft a practical schema with indexes and safe constraints?"
-- ChatGPT provided the schema pattern below, adapted to this codebase.

CREATE TABLE IF NOT EXISTS group_projects (
    id SERIAL PRIMARY KEY,
    owner_student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    module_code TEXT,
    description TEXT,
    due_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_group_projects_owner_created
    ON group_projects(owner_student_id, created_at DESC);

CREATE TABLE IF NOT EXISTS group_project_members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES group_projects(id) ON DELETE CASCADE,
    member_name TEXT NOT NULL,
    member_email TEXT NOT NULL,
    member_role TEXT,
    notes TEXT,
    invite_token TEXT UNIQUE,
    invite_status TEXT NOT NULL DEFAULT 'pending',
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_group_project_members_project
    ON group_project_members(project_id);

CREATE UNIQUE INDEX IF NOT EXISTS uniq_group_project_member_email
    ON group_project_members(project_id, LOWER(member_email));

CREATE TABLE IF NOT EXISTS group_project_tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES group_projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    assigned_member_id INTEGER REFERENCES group_project_members(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'todo',
    priority TEXT NOT NULL DEFAULT 'medium',
    due_date DATE,
    estimated_hours NUMERIC(6,2),
    progress_percent INTEGER NOT NULL DEFAULT 0,
    ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT group_task_status_check CHECK (status IN ('todo', 'in_progress', 'review', 'done')),
    CONSTRAINT group_task_priority_check CHECK (priority IN ('low', 'medium', 'high')),
    CONSTRAINT group_task_progress_check CHECK (progress_percent >= 0 AND progress_percent <= 100)
);

CREATE INDEX IF NOT EXISTS idx_group_project_tasks_project
    ON group_project_tasks(project_id, due_date);

CREATE INDEX IF NOT EXISTS idx_group_project_tasks_member
    ON group_project_tasks(assigned_member_id, status);

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
