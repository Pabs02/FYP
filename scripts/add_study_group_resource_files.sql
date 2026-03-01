-- Reference: ChatGPT (OpenAI) - Study Group Resource File Columns Migration
-- Date: 2026-03-01
-- Prompt: "I need an idempotent SQL migration to extend study_group_resources with
-- optional file metadata columns so resources can include uploaded files."
-- ChatGPT provided the ALTER TABLE IF NOT EXISTS migration pattern adapted below.

ALTER TABLE study_group_resources
ADD COLUMN IF NOT EXISTS resource_filename TEXT;

ALTER TABLE study_group_resources
ADD COLUMN IF NOT EXISTS resource_filepath TEXT;

ALTER TABLE study_group_resources
ADD COLUMN IF NOT EXISTS resource_file_size_bytes INTEGER;
