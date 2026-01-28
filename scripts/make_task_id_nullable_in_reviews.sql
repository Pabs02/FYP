-- Reference: ChatGPT (OpenAI) - Nullable Task Link for Reviews
-- Date: 2026-01-22
-- Prompt: "I need to allow assignment reviews without a linked task by making
-- task_id nullable. Can you provide the SQL?"
-- ChatGPT provided the migration approach.
-- Make task_id nullable in assignment_reviews table
-- This allows reviews to be created without linking to a specific task
-- (useful for the standalone Assignment Review page)

ALTER TABLE assignment_reviews 
ALTER COLUMN task_id DROP NOT NULL;

