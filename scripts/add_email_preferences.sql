-- Reference: ChatGPT (OpenAI) - Email Preferences Fields
-- Date: 2026-01-22
-- Prompt: "I need columns for email notification preferences and daily summary
-- status tracking in my students table. Can you provide the SQL?"
-- ChatGPT provided the ALTER TABLE statements for email preferences and status tracking.
-- Add email notification preferences to students
ALTER TABLE students
ADD COLUMN IF NOT EXISTS email_notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS email_daily_summary_enabled BOOLEAN NOT NULL DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS last_daily_summary_sent_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS daily_summary_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS daily_summary_error TEXT;
