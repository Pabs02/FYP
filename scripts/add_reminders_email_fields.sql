-- Reference: ChatGPT (OpenAI) - Reminder Email Tracking Fields
-- Date: 2026-01-22
-- Prompt: "I need fields to track reminder email sent time, status, and error.
-- Can you add those columns to the reminders table?"
-- ChatGPT provided the SQL for the reminder email tracking fields.
-- Add email tracking fields for reminders
ALTER TABLE reminders
ADD COLUMN IF NOT EXISTS email_sent_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS email_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS email_error TEXT;
