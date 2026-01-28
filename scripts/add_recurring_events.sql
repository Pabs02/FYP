-- Reference: ChatGPT (OpenAI) - Recurring Events Fields
-- Date: 2026-01-22
-- Prompt: "I need to add recurring event support to the events table with a
-- recurrence end date and indexing. Can you provide the SQL?"
-- ChatGPT provided the schema update for recurring events.
-- Add recurring event support to events table
-- Allows events to repeat weekly on the same day and time

ALTER TABLE events 
ADD COLUMN IF NOT EXISTS is_recurring BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS recurrence_end_date DATE;

-- Index for querying recurring events
CREATE INDEX IF NOT EXISTS idx_events_recurring ON events(is_recurring, recurrence_end_date) WHERE is_recurring = TRUE;

